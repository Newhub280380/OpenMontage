"""Identity-insert planner. No provider is called and no picture is rendered."""

from __future__ import annotations

import json
import shutil
import subprocess
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from lib.middle_layer import (
    MiddleRefusal,
    approve,
    character_sheet,
    compile_prompt,
    mannequin_passes,
    pick_trend,
    prepare,
    recovery,
    run_qa,
    video_mode,
)
from lib.scoring import score_provider
from tools.base_tool import ToolStatus
from tools.cost_tracker import BudgetExceededError, CostTracker
from tools.identity.middle_layer import IdentityMiddleLayer
from lib.config_model import BudgetMode

WHEN = datetime(2026, 11, 27, 12, 0, tzinfo=timezone.utc)
ROOT = Path(__file__).resolve().parents[2]
KNOWLEDGE = ROOT / "skills" / "knowledge" / "middle"


def _wish() -> dict:
    return {
        "wish": "face of user into GTA-style 13 s clip as the driver",
        "photo_asset_id": "photo-synthetic",
        "video_asset_id": "video-synthetic",
        "name": "driver",
        "duration_seconds": 13,
        "video_mode": "edit",
        "rules": ["Keep the adult age described by the user."],
    }


def test_sheet_limits_and_alias() -> None:
    sheet = character_sheet("driver", ["photo-a", "photo-b"])
    assert sheet["alias"] == "@driver"
    assert len(sheet["views"]) == 8
    assert len(sheet["plates"]) == 3
    assert sheet["rendered"] is False
    assert all(view["rendered"] is False for view in sheet["views"])
    with pytest.raises(MiddleRefusal) as caught:
        character_sheet("driver", ["x"] * 17)
    assert caught.value.code == "sheet_photos_rejected"


def test_video_modes_stay_distinct() -> None:
    edit = video_mode("edit")
    motion = video_mode("reference")
    assert edit["field"] == "sourceVideo"
    assert edit["keeps_frames"] is True
    assert motion["field"] == "referenceVideo"
    assert motion["motion_only"] is True


def test_gta_plan_gates_budget_and_expiry(tmp_path: Path) -> None:
    tracker = CostTracker(
        budget_total_usd=10,
        mode=BudgetMode.CAP,
        cost_log_path=tmp_path / "cost.json",
    )
    plan = prepare(_wish(), moment=WHEN, tracker=tracker)
    assert plan["render_started"] is False
    assert plan["generation_performed"] is False
    assert plan["paid_call_allowed"] is False
    assert plan["video_mode"]["mode"] == "edit"
    assert plan["video_mode"]["field"] == "sourceVideo"
    assert [frame["role"] for frame in plan["frames"]["frames"]] == ["first", "key", "last"]
    assert [item["index"] for item in plan["mannequin"]["passes"]] == [1, 2]
    assert plan["mannequin"]["applies"] is True
    text = plan["prompt"]["text"]
    assert "PRESERVE" in text and "REPLACE" in text and "INTEGRATE" in text
    assert plan["prompt"]["order"] == ["preserve", "replace", "integrate"]
    assert plan["prompt"]["timeline"][0]["end"] == "13.00"
    assert "@driver" in text
    assert plan["draft"]["draft"]["resolution"] == "480p"
    assert plan["draft"]["chunks"] == [
        {
            "index": 1,
            "start_seconds": 0.0,
            "duration_seconds": 13.0,
            "prompt": plan["prompts"][0],
        }
    ]
    assert plan["routing"][0]["model"] == "seedance-2.5"
    assert plan["routing"][0]["weights"]["task_fit"] == 0.30
    assert plan["launch"]["approved"] is False
    assert plan["launch"]["price_estimate"]["live_quote"] is False
    assert plan["launch"]["price_estimate"]["usd"] == 1.11
    assert plan["budget"]["entry_id"]
    assert any("gta" in (item.get("slug") or "") for item in plan["trends"])
    assert "prompt" not in plan["trends"][0]
    with pytest.raises(MiddleRefusal):
        approve(plan, "launch", WHEN, tracker)
    approve(plan, "sheet", WHEN, tracker)
    approve(plan, "frames", WHEN, tracker)
    approve(plan, "launch", WHEN + timedelta(minutes=1), tracker)
    assert plan["launch"]["approved"] is True
    assert plan["render_started"] is False
    assert plan["budget"]["reserved"] is True
    plan["launch"]["approved"] = False
    with pytest.raises(MiddleRefusal) as caught:
        approve(plan, "launch", WHEN + timedelta(minutes=16), tracker)
    assert caught.value.code == "card_expired"


def test_long_clip_splits_and_reference_is_not_edit() -> None:
    plan = prepare(
        {
            "wish": "repeat the motion only",
            "photo_asset_id": "p",
            "video_asset_id": "v",
            "name": "driver",
            "duration_seconds": 48,
            "video_mode": "reference",
        },
        moment=WHEN,
    )
    assert plan["video_mode"]["field"] == "referenceVideo"
    assert plan["mannequin"]["applies"] is False
    assert [item["duration_seconds"] for item in plan["draft"]["chunks"]] == [15.0, 15.0, 18.0]
    compiled = compile_prompt("kling-3.0", "@driver", "reference", 10, "a short motion")
    assert compiled["aliases"] is False
    with pytest.raises(MiddleRefusal) as caught:
        compile_prompt("kling-3.0", "@driver", "reference", 16, "too long")
    assert caught.value.code == "duration_rejected"
    with pytest.raises(MiddleRefusal) as caught:
        compile_prompt("wan-3.0", "@driver", "edit", 5, "keep the frames")
    assert caught.value.code == "mode_rejected"


def test_recovery_and_trends_have_no_prompt_text() -> None:
    lever = recovery("not_like")
    assert lever["rewrote_prompt"] is False
    assert "shorter_chunk" in lever["levers"]
    found = pick_trend("gta", 3)
    assert found
    assert "prompt" not in found[0]
    passes = mannequin_passes("@driver", applies=True)
    assert passes["passes"][0]["suit"] == "green"
    assert "original actor" in passes["passes"][1]["note"]


def test_tool_refuses_generation(tmp_path: Path) -> None:
    tool = IdentityMiddleLayer()
    refused = tool.execute({"action": "generate"})
    assert refused.success is False
    assert refused.data["render_started"] is False
    planned = tool.execute(
        {
            "action": "plan",
            **_wish(),
            "now": WHEN.isoformat(),
            "output_path": str(tmp_path / "plan.json"),
            "cost_log_path": str(tmp_path / "cost.json"),
            "budget_usd": 10,
            "budget_mode": "cap",
        }
    )
    assert planned.success is True
    assert planned.data["plan"]["routing"][0]["model"] == "seedance-2.5"
    assert Path(planned.artifacts[0]).is_file()


def test_source_video_edit_changes_rank() -> None:
    class _Tool:
        def __init__(self, name: str, edit: bool) -> None:
            self.name = name
            self._edit = edit

        def get_status(self) -> ToolStatus:
            return ToolStatus.AVAILABLE

        def estimate_cost(self, inputs: dict) -> float:
            return 0.2

        def get_info(self) -> dict:
            return {
                "name": self.name,
                "provider": self.name,
                "capability": "video_generation",
                "best_for": ["cinematic character identity"],
                "supports": {"source_video_edit": self._edit, "reference_image": True},
                "stability": "production",
                "runtime": "api",
                "tier": "generate",
            }

    context = {
        "intent": "character identity cinematic",
        "asset_type": "video",
        "style_keywords": ["cinematic"],
        "wants_source_video_edit": True,
        "motion_required": True,
    }
    edit = score_provider(_Tool("edit-model", True), context)
    motion = score_provider(_Tool("motion-model", False), context)
    assert edit.task_fit > motion.task_fit


def test_over_budget_blocks_launch(tmp_path: Path) -> None:
    tracker = CostTracker(
        budget_total_usd=0.5,
        reserve_pct=0.0,
        mode=BudgetMode.CAP,
        cost_log_path=tmp_path / "cost.json",
    )
    plan = prepare(_wish(), moment=WHEN, tracker=tracker)
    approve(plan, "sheet", WHEN, tracker)
    approve(plan, "frames", WHEN, tracker)
    with pytest.raises(MiddleRefusal) as caught:
        approve(plan, "launch", WHEN + timedelta(minutes=1), tracker)
    assert caught.value.code == "over_budget"
    assert plan["launch"]["approved"] is False
    assert isinstance(caught.value.__cause__, BudgetExceededError)


def test_ffmpeg_qa_on_local_clip(tmp_path: Path) -> None:
    if shutil.which("ffmpeg") is None:
        pytest.skip("ffmpeg is not installed")
    target = tmp_path / "tone.mp4"
    subprocess.run(
        [
            "ffmpeg",
            "-y",
            "-f",
            "lavfi",
            "-i",
            "color=c=blue:s=160x90:d=1",
            "-f",
            "lavfi",
            "-i",
            "sine=frequency=440:duration=1",
            "-shortest",
            "-pix_fmt",
            "yuv420p",
            str(target),
        ],
        check=True,
        capture_output=True,
    )
    report = run_qa(str(target), expected_seconds=1)
    assert report["ran"] is True
    assert report["duration_ok"] is True
    assert report["loudness_target_lufs"] == -14
    assert isinstance(report["black_frames"], list)


def test_knowledge_pack_has_no_brand_and_no_prompt_bodies() -> None:
    catalog = json.loads((KNOWLEDGE / "model-cards" / "catalog.json").read_text(encoding="utf-8"))
    trends = json.loads((KNOWLEDGE / "trends" / "index.json").read_text(encoding="utf-8"))
    skills = list((KNOWLEDGE / "skills").glob("*/SKILL.md"))
    assert len(catalog["models"]) == 105
    assert len(trends["trends"]) == 479
    assert trends["prompts_included"] is False
    assert len(skills) == 31
    assert "prompt" not in trends["trends"][0]
    blob = "\n".join(path.read_text(encoding="utf-8") for path in (KNOWLEDGE / "skills").rglob("*.md"))
    assert "givon" not in blob.lower()
