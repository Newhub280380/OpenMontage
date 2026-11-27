"""Planning tool for a person, a reference clip, and a short wish.

Actions build a character sheet, choose edit versus motion-reference, compile
a prompt, and write a launch card. They do not call a video provider.
"""

from __future__ import annotations

import json
import time
from datetime import datetime
from pathlib import Path
from typing import Any

from lib.config_model import BudgetMode
from lib.middle_layer import (
    MiddleRefusal,
    MiddleStore,
    approve,
    pick_trend,
    prepare,
    recovery,
    run_qa,
)
from tools.base_tool import (
    BaseTool,
    Determinism,
    ExecutionMode,
    ResourceProfile,
    ToolResult,
    ToolTier,
)
from tools.cost_tracker import CostTracker


class IdentityMiddleLayer(BaseTool):
    name = "identity_middle_layer"
    version = "0.1.0"
    tier = ToolTier.ANALYZE
    capability = "identity_planning"
    provider = "openmontage"
    execution_mode = ExecutionMode.SYNC
    determinism = Determinism.DETERMINISTIC
    resource_profile = ResourceProfile(cpu_cores=1, ram_mb=256, disk_mb=20)
    agent_skills = ["identity-middle-layer"]
    capabilities = [
        "character_sheet",
        "mode_select",
        "frame_first",
        "mannequin_pass",
        "prompt_compile",
        "trend_template",
        "launch_card",
        "draft_chunk_plan",
        "ffmpeg_qa",
    ]
    best_for = [
        "Planning a face or character into an existing clip without provider calls",
        "Keeping identity on an approved sheet and approved stills",
    ]
    not_good_for = [
        "Calling a paid video model",
        "Rendering the character sheet or the finished clip",
    ]
    input_schema = {
        "type": "object",
        "required": ["action"],
        "properties": {
            "action": {
                "type": "string",
                "enum": ["plan", "approve", "trends", "qa", "recover"],
            },
            "output_path": {"type": "string"},
        },
    }
    output_schema = {"type": "object"}
    side_effects = ["writes a plan JSON when output_path is set", "records a cost estimate"]
    user_visible_verification = [
        "Launch card shows model, prompt, settings, estimate, and expiry",
        "render_started stays false",
    ]

    def execute(self, inputs: dict[str, Any]) -> ToolResult:
        start = time.time()
        action = inputs.get("action")
        if action in {"generate", "render"}:
            return self._fail(
                "generation_refused",
                "This tool plans only. No provider is called.",
                start,
            )
        try:
            if action == "plan":
                data = self._plan(inputs)
            elif action == "approve":
                data = self._approve(inputs)
            elif action == "trends":
                data = {"trends": pick_trend(str(inputs.get("query") or ""), int(inputs.get("limit") or 5)), "prompts_included": False}
            elif action == "qa":
                data = {"qa": run_qa(str(inputs.get("path") or ""), expected_seconds=inputs.get("expected_seconds"))}
            elif action == "recover":
                data = {"recovery": recovery(str(inputs.get("reason") or ""))}
            else:
                return self._fail("action_rejected", "Action is plan, approve, trends, qa, or recover.", start)
        except MiddleRefusal as exc:
            return self._fail(exc.code, str(exc), start)
        artifacts = []
        output_path = inputs.get("output_path")
        if output_path and "plan" in data:
            path = Path(output_path)
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(json.dumps(data["plan"], ensure_ascii=False, indent=2), encoding="utf-8")
            artifacts.append(str(path))
        return ToolResult(
            success=True,
            data=data,
            artifacts=artifacts,
            cost_usd=0.0,
            duration_seconds=round(time.time() - start, 3),
        )

    def _plan(self, inputs: dict[str, Any]) -> dict[str, Any]:
        log = inputs.get("cost_log_path")
        if log is None and inputs.get("output_path"):
            log = str(Path(inputs["output_path"]).with_suffix(".cost.json"))
            inputs = {**inputs, "cost_log_path": log}
        tracker = self._tracker(inputs)
        moment = _moment(inputs.get("now"))
        plan = prepare(inputs, moment=moment, tracker=tracker)
        if log:
            plan.setdefault("budget", {})["cost_log_path"] = str(log)
        store_dir = inputs.get("store_dir")
        if store_dir:
            MiddleStore(Path(store_dir)).save(plan)
        return {"plan": plan, "render_started": False}

    def _approve(self, inputs: dict[str, Any]) -> dict[str, Any]:
        plan = inputs.get("plan")
        if plan is None and inputs.get("store_dir") and inputs.get("plan_id"):
            plan = MiddleStore(Path(inputs["store_dir"])).get(str(inputs["plan_id"]))
        if not isinstance(plan, dict):
            raise MiddleRefusal("not_found", "Plan not found.")
        tracker = self._tracker(inputs, existing=plan)
        moment = _moment(inputs.get("now"))
        plan = approve(plan, str(inputs.get("gate") or ""), moment, tracker)
        if inputs.get("store_dir"):
            MiddleStore(Path(inputs["store_dir"])).save(plan)
        return {"plan": plan, "render_started": False}

    def _tracker(self, inputs: dict[str, Any], existing: dict[str, Any] | None = None) -> CostTracker:
        log_path = inputs.get("cost_log_path")
        if log_path:
            path = Path(log_path)
        elif existing and (existing.get("budget") or {}).get("cost_log_path"):
            path = Path(existing["budget"]["cost_log_path"])
        else:
            path = None
        mode_name = str(inputs.get("budget_mode") or "warn")
        mode = BudgetMode(mode_name)
        tracker = CostTracker(
            budget_total_usd=float(inputs.get("budget_usd") or 10.0),
            mode=mode,
            cost_log_path=path,
        )
        if path is not None and existing is not None:
            existing.setdefault("budget", {})["cost_log_path"] = str(path)
        return tracker

    def _fail(self, code: str, message: str, start: float) -> ToolResult:
        return ToolResult(
            success=False,
            data={"code": code, "render_started": False, "generation_performed": False},
            error=message,
            cost_usd=0.0,
            duration_seconds=round(time.time() - start, 3),
        )


def _moment(value: Any) -> datetime | None:
    if not value:
        return None
    return datetime.fromisoformat(str(value))
