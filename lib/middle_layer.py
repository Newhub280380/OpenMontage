"""Planning layer between a short wish and a video model.

The functions here do not call a provider and do not render a picture.
A launch card stays idle until the character sheet and the still frames
are approved, and an expired card cannot be approved.

Model order comes from ``lib.scoring.rank_providers``. Spend is recorded
with ``tools.cost_tracker.CostTracker``. Those two modules stay the
source of truth for weights and for the budget cap.
"""

from __future__ import annotations

import hashlib
import json
import re
import shutil
import subprocess
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from lib.scoring import rank_providers
from tools.base_tool import ToolStatus
from tools.cost_tracker import (
    ApprovalRequiredError,
    BudgetExceededError,
    CostTracker,
)
from tools.provider_pricing import PriceQuoteRequired

ROOT = Path(__file__).resolve().parent.parent
KNOWLEDGE = ROOT / "skills" / "knowledge" / "middle"
CATALOG_PATH = KNOWLEDGE / "model-cards" / "catalog.json"
TRENDS_PATH = KNOWLEDGE / "trends" / "index.json"

VIEWS = (
    "front",
    "three_quarter_left",
    "three_quarter_right",
    "profile_left",
    "profile_right",
    "full_body",
    "back",
    "face",
)
PLATES = (
    {"id": "portrait", "views": ("face",)},
    {"id": "body", "views": ("front", "full_body", "back")},
    {
        "id": "face_sheet",
        "views": (
            "three_quarter_left",
            "three_quarter_right",
            "profile_left",
            "profile_right",
        ),
    },
)
CARD_MINUTES = 15
CHUNK_SECONDS = 15
DRAFT_RESOLUTION = "480p"
# Published OpenMontage rate for Seedance 2.5 in tools/video/seedance_video.py.
# The draft tier is the cheaper first pass described by the research (about
# 3.5x below a final). This is a catalog estimate, not a live quote.
SEEDANCE_FINAL_USD_PER_SECOND = 0.30
DRAFT_DISCOUNT = 3.5
SCORE_WEIGHTS = {
    "task_fit": 0.30,
    "output_quality": 0.20,
    "control": 0.15,
    "reliability": 0.15,
    "cost_efficiency": 0.10,
    "latency": 0.05,
    "continuity": 0.05,
}
_NAME = re.compile(r"^[a-z][a-z0-9_]{0,31}$")
_CATALOG: list[dict[str, Any]] | None = None
_TRENDS: list[dict[str, Any]] | None = None


class MiddleRefusal(Exception):
    """A planning input was rejected. No provider call was made."""

    def __init__(self, code: str, message: str) -> None:
        self.code = code
        super().__init__(message)


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _stamp(moment: datetime) -> str:
    return moment.isoformat()


def load_catalog() -> list[dict[str, Any]]:
    global _CATALOG
    if _CATALOG is None:
        payload = json.loads(CATALOG_PATH.read_text(encoding="utf-8"))
        _CATALOG = list(payload["models"])
    return _CATALOG


def load_trends() -> list[dict[str, Any]]:
    global _TRENDS
    if _TRENDS is None:
        payload = json.loads(TRENDS_PATH.read_text(encoding="utf-8"))
        _TRENDS = list(payload["trends"])
    return _TRENDS


def get_card(model_id: str) -> dict[str, Any]:
    for card in load_catalog():
        if card["id"] == model_id:
            return card
    raise MiddleRefusal(
        "model_unknown",
        f"No model card for {model_id}. No prompt was invented for it.",
    )


def card_can_edit(card: dict[str, Any]) -> bool:
    modes = set(card.get("input_modes") or [])
    options = set(card.get("mode_options") or [])
    return "video_edit" in modes or "edit" in options


def card_duration_bounds(card: dict[str, Any]) -> tuple[float, float] | None:
    durations = card.get("durations") or []
    numbers = [float(item) for item in durations]
    if not numbers:
        return None
    return min(numbers), max(numbers)


def draft_usd(card: dict[str, Any], seconds: float) -> float | None:
    if str(card.get("id", "")).startswith("seedance"):
        return round(SEEDANCE_FINAL_USD_PER_SECOND / DRAFT_DISCOUNT * float(seconds), 2)
    return None


class _CardTool:
    """Knowledge-card adapter scored by the existing provider ranker."""

    def __init__(self, card: dict[str, Any]) -> None:
        self.name = card["id"]
        self._card = card

    def get_status(self) -> ToolStatus:
        return ToolStatus.AVAILABLE

    def estimate_cost(self, inputs: dict[str, Any]) -> float:
        seconds = float(inputs.get("duration_seconds") or inputs.get("duration") or 0)
        usd = draft_usd(self._card, seconds or 5)
        if usd is None:
            raise PriceQuoteRequired(
                f"{self.name} has catalog units only. No OpenMontage USD rate is published."
            )
        return usd

    def get_info(self) -> dict[str, Any]:
        card = self._card
        edit = card_can_edit(card)
        modes = set(card.get("input_modes") or [])
        best_for = [
            "video generation",
            "character identity",
        ]
        if edit:
            best_for.append("source video edit cinematic character replacement")
        if "video_reference" in modes or "image_to_video" in modes:
            best_for.append("motion reference camera")
        supports = {
            "reference_image": edit or "image_to_video" in modes or "video_reference" in modes,
            "reference_to_video": "video_reference" in modes or edit,
            "multiple_reference_images": bool(card.get("aliases")),
            "source_video_edit": edit,
            "video_edit": edit,
            "camera_direction": str(card["id"]).startswith("seedance"),
            "cinematic_quality": str(card["id"]).startswith("seedance"),
        }
        return {
            "name": card["id"],
            "provider": card.get("provider") or "catalog",
            "capability": "video_generation",
            "best_for": best_for,
            "supports": supports,
            "stability": card.get("stability") or "beta",
            "runtime": "api",
            "tier": "generate",
        }


def rank_model_cards(context: dict[str, Any]) -> list[dict[str, Any]]:
    """Rank video model cards with ``lib.scoring.rank_providers``."""
    cards = [card for card in load_catalog() if card.get("kind") == "video"]
    tools = [_CardTool(card) for card in cards]
    by_id = {card["id"]: card for card in cards}
    ranked = []
    for score in rank_providers(tools, context):
        card = by_id[score.tool_name]
        ranked.append(
            {
                "model": score.tool_name,
                "provider": score.provider,
                "score": round(score.weighted_score, 4),
                "weights": dict(SCORE_WEIGHTS),
                "scores": {
                    "task_fit": round(score.task_fit, 4),
                    "output_quality": round(score.output_quality, 4),
                    "control": round(score.control, 4),
                    "reliability": round(score.reliability, 4),
                    "cost_efficiency": round(score.cost_efficiency, 4),
                    "latency": round(score.latency, 4),
                    "continuity": round(score.continuity, 4),
                },
                "edit": card_can_edit(card),
                "aliases": bool(card.get("aliases")),
                "why": score.explain(),
            }
        )
    ranked.sort(
        key=lambda item: (
            -item["score"],
            0 if item["model"] == "seedance-2.5" else 1,
            item["model"],
        )
    )
    return ranked


def pick_trend(query: str, limit: int = 5) -> list[dict[str, Any]]:
    words = [part for part in re.split(r"\W+", (query or "").lower()) if len(part) > 2]
    scored: list[tuple[int, dict[str, Any]]] = []
    for item in load_trends():
        categories = " ".join(item.get("categories") or [])
        hay = " ".join(
            [
                item.get("slug") or "",
                item.get("title") or "",
                item.get("model") or "",
                item.get("mode") or "",
                categories,
            ]
        ).lower()
        score = sum(1 for word in words if word in hay)
        if score:
            scored.append((score, item))
    scored.sort(key=lambda pair: (-pair[0], pair[1].get("slug") or ""))
    found = []
    for _score, item in scored[:limit]:
        copy = dict(item)
        copy.pop("prompt", None)
        found.append(copy)
    return found


def character_sheet(name: str, photo_ids: list[str]) -> dict[str, Any]:
    if not isinstance(name, str) or not _NAME.match(name):
        raise MiddleRefusal(
            "sheet_name_rejected",
            "Sheet name is a short lowercase handle, used as @name.",
        )
    if not isinstance(photo_ids, list) or not 1 <= len(photo_ids) <= 16:
        raise MiddleRefusal(
            "sheet_photos_rejected",
            "A character sheet takes 1 to 16 photo ids. None were dropped.",
        )
    if any(not isinstance(item, str) or not item for item in photo_ids):
        raise MiddleRefusal("sheet_photos_rejected", "Each photo id must be a string.")
    slots = []
    for index, view in enumerate(VIEWS):
        slots.append(
            {
                "view": view,
                "source_photo_id": photo_ids[index % len(photo_ids)],
                "rendered": False,
            }
        )
    plates = []
    for plate in PLATES:
        plates.append(
            {
                "id": plate["id"],
                "views": list(plate["views"]),
                "rendered": False,
            }
        )
    return {
        "name": name,
        "alias": "@" + name,
        "photo_ids": list(photo_ids),
        "photo_count": len(photo_ids),
        "views": slots,
        "plates": plates,
        "approved": False,
        "rendered": False,
    }


def video_mode(mode: str) -> dict[str, Any]:
    if mode == "edit":
        return {
            "mode": "edit",
            "field": "sourceVideo",
            "keeps_frames": True,
            "motion_only": False,
        }
    if mode == "reference":
        return {
            "mode": "reference",
            "field": "referenceVideo",
            "keeps_frames": False,
            "motion_only": True,
        }
    raise MiddleRefusal("video_mode_rejected", "Video mode is edit or reference.")


def choose_mode(body: dict[str, Any]) -> tuple[str, str]:
    requested = body.get("video_mode")
    if requested in {"edit", "reference"}:
        return requested, "caller selected the mode"
    wish = str(body.get("wish") or "").lower()
    motion_only = (
        "motion only" in wish
        or "camera only" in wish
        or "repeat the motion" in wish
    )
    if motion_only:
        return "reference", "the wish asks for motion without keeping the source frames"
    return "edit", "a source video plus a person means edit, which keeps the frames"


def frame_first(duration_seconds: float) -> dict[str, Any]:
    if (
        not isinstance(duration_seconds, (int, float))
        or isinstance(duration_seconds, bool)
        or duration_seconds <= 0
    ):
        raise MiddleRefusal("duration_rejected", "duration_seconds must be a positive number.")
    duration = float(duration_seconds)
    points = (("first", 0.0), ("key", round(duration / 2, 2)), ("last", round(duration, 2)))
    return {
        "approved": False,
        "rendered": False,
        "gate": "stills_before_animation",
        "frames": [
            {"role": role, "at_seconds": at, "still": None, "approved": False}
            for role, at in points
        ],
    }


def mannequin_passes(alias: str, *, applies: bool, color: str = "green") -> dict[str, Any]:
    if not alias.startswith("@"):
        raise MiddleRefusal(
            "alias_rejected",
            "The second pass names the approved sheet as @name.",
        )
    return {
        "rendered": False,
        "applies": applies,
        "reason": (
            "Edit mode replaces a marked stand-in so the original actor does not return."
            if applies
            else "Motion-reference mode does not run the stand-in pass."
        ),
        "passes": [
            {
                "index": 1,
                "action": "replace_actor_with_mannequin",
                "suit": color,
                "keep": ["motion", "camera", "light", "timing"],
                "prompt": (
                    f"Replace the actor with a {color} full-body motion-capture mannequin. "
                    "Keep motion, camera, light and timing."
                ),
            },
            {
                "index": 2,
                "action": "replace_mannequin_with_character",
                "suit": color,
                "alias": alias,
                "note": "The original actor is not the replacement target.",
                "prompt": (
                    f"@video1 is the authority for timing, movement and camera. "
                    f"Replace the intermediate subject in the {color} suit with {alias}."
                ),
            },
        ],
    }


def chunks(duration_seconds: float, limit: int = CHUNK_SECONDS) -> list[dict[str, Any]]:
    if duration_seconds <= 0:
        raise MiddleRefusal("duration_rejected", "duration_seconds must be positive.")
    pieces: list[dict[str, Any]] = []
    cursor = 0.0
    index = 1
    while cursor < duration_seconds - 0.001:
        length = min(float(limit), round(duration_seconds - cursor, 2))
        pieces.append(
            {
                "index": index,
                "start_seconds": round(cursor, 2),
                "duration_seconds": round(length, 2),
            }
        )
        cursor = round(cursor + length, 2)
        index += 1
    if len(pieces) > 1 and pieces[-1]["duration_seconds"] < 4:
        pieces[-2]["duration_seconds"] = round(
            pieces[-2]["duration_seconds"] + pieces[-1]["duration_seconds"],
            2,
        )
        pieces.pop()
    return pieces


def compile_prompt(
    model: str,
    alias: str,
    mode: str,
    duration_seconds: float,
    wish: str,
    rules: list[str] | None = None,
    *,
    resolution: str = DRAFT_RESOLUTION,
) -> dict[str, Any]:
    card = get_card(model)
    chosen = video_mode("edit" if mode == "edit" else "reference")
    bounds = card_duration_bounds(card)
    if bounds is not None:
        low, high = bounds
        if not low <= float(duration_seconds) <= high:
            raise MiddleRefusal(
                "duration_rejected",
                f"{model} accepts {low:g} to {high:g} seconds. {duration_seconds} was not stretched.",
            )
    if chosen["mode"] == "edit" and not card_can_edit(card):
        raise MiddleRefusal(
            "mode_rejected",
            f"{model} has no source-video edit slot. The mode was not rewritten as a reference.",
        )
    lines = [item.strip() for item in (rules or []) if isinstance(item, str) and item.strip()]
    preserve = [
        "Keep the approved person's age, face and proportions.",
        (
            "Keep the source camera, timing and light."
            if chosen["keeps_frames"]
            else "Use the video only for motion and camera. Do not promise frame-by-frame identity."
        ),
        *lines,
    ]
    replace = [
        f"Replace only the marked green stand-in with {alias}.",
        "Do not bring the original actor back.",
    ]
    integrate = [
        "Match light direction, contact shadows and grain.",
        "No halo around the replaced person.",
    ]
    timeline = [
        {
            "start": "0.00",
            "end": f"{float(duration_seconds):.2f}",
            "text": (wish or "").strip() or "The approved person performs the shot.",
        }
    ]
    if card.get("aliases"):
        alias_line = f"@Video1 is timing, movement and camera. {alias} is identity."
    else:
        alias_line = (
            "Identity file first, motion file second. This model card does not use inline @ aliases."
        )
    text = "\n".join(
        [
            "TASK & FORMAT",
            f"- Preserve the approved frame and the {float(duration_seconds):.2f}-second sequence.",
            "REFERENCES",
            "- " + alias_line,
            "ABSOLUTE REPLACEMENT RULES",
            "PRESERVE",
            *[("- " + line) for line in preserve],
            "REPLACE",
            *[("- " + line) for line in replace],
            "INTEGRATE",
            *[("- " + line) for line in integrate],
            "GLOBAL SETTINGS",
            f"- model {model}",
            f"- mode {chosen['mode']}",
            f"- field {chosen['field']}",
            f"- resolution {resolution}",
            f"- prompt_language {card.get('prompt_language') or 'en'}",
            "TIMELINE",
            f"- {timeline[0]['start']}-{timeline[0]['end']} {timeline[0]['text']}",
            "MOTION",
            f"- Performer 1 ({alias}) performs only the measured motion in this chunk.",
            "CONSTRAINTS",
            "- One identity. Appearance does not come from the motion video.",
            "- Timecodes are the measured chunk bounds only.",
        ]
    )
    return {
        "model": model,
        "order": ["preserve", "replace", "integrate"],
        "preserve": preserve,
        "replace": replace,
        "integrate": integrate,
        "timeline": timeline,
        "text": text,
        "aliases": bool(card.get("aliases")),
        "prompt_language": card.get("prompt_language") or "en",
        "format": "task_references_rules_timeline",
    }


def _idempotency_key(model: str, prompt: str, settings: dict[str, Any]) -> str:
    raw = json.dumps({"model": model, "prompt": prompt, "settings": settings}, sort_keys=True)
    return hashlib.sha256(raw.encode()).hexdigest()[:16]


def launch_card(
    model: str,
    prompt: str,
    settings: dict[str, Any],
    why: str,
    moment: datetime | None = None,
) -> dict[str, Any]:
    moment = moment or _now()
    seconds = float(settings.get("duration_seconds") or 0)
    card = get_card(model)
    usd = draft_usd(card, seconds)
    final_usd = None
    if str(model).startswith("seedance"):
        final_usd = round(SEEDANCE_FINAL_USD_PER_SECOND * seconds, 2)
    return {
        "model": model,
        "prompt": prompt,
        "settings": settings,
        "why": why,
        "price_estimate": {
            "usd": usd,
            "final_usd": final_usd,
            "usd_basis": (
                "OpenMontage Seedance 2.5 rate $0.30/s divided by 3.5 for the 480p draft. Not a live quote."
                if usd is not None
                else "No published OpenMontage USD rate. Catalog units only."
            ),
            "catalog_tokens_per_second": card.get("tokens_per_second"),
            "catalog_tokens": (
                None
                if card.get("tokens_per_second") is None
                else round(float(card["tokens_per_second"]) * seconds, 2)
            ),
            "live_quote": False,
        },
        "idempotency_key": _idempotency_key(model, prompt, settings),
        "created_at": _stamp(moment),
        "expires_at": _stamp(moment + timedelta(minutes=CARD_MINUTES)),
        "approved": False,
        "paid_call_allowed": False,
    }


def draft_plan(duration_seconds: float, final_resolution: str = "1080p") -> dict[str, Any]:
    return {
        "rendered": False,
        "draft": {
            "resolution": DRAFT_RESOLUTION,
            "duration_seconds": duration_seconds,
            "approved": False,
        },
        "final": {
            "resolution": final_resolution,
            "uses_same_draft": True,
            "regenerate_motion": False,
            "upscale_tool": "upscale",
            "approved": False,
        },
        "chunks": chunks(duration_seconds),
        "stitch": {"tool": "video_stitch", "rendered": False},
    }


def qa_plan() -> dict[str, Any]:
    return {
        "ran": False,
        "checks": ["duration", "black_frames", "frozen_frames", "silence", "loudness"],
        "loudness_target_lufs": -14,
    }


def recovery(reason: str) -> dict[str, Any]:
    if reason != "not_like":
        raise MiddleRefusal(
            "recovery_rejected",
            "Recovery is only for not_like. The prompt was not rewritten.",
        )
    return {
        "rewrote_prompt": False,
        "levers": ["add_close_frame", "shorter_chunk", "one_person"],
    }


def _photo_ids(body: dict[str, Any]) -> list[str]:
    photos = body.get("photo_ids")
    if photos is None and body.get("photo_asset_id"):
        photos = [body["photo_asset_id"]]
    if not isinstance(photos, list):
        raise MiddleRefusal(
            "references_required",
            "photo_ids (1 to 16) or photo_asset_id is required. Files are not read.",
        )
    return photos


def _chunk_limit(card: dict[str, Any]) -> int:
    bounds = card_duration_bounds(card)
    if bounds is None:
        return CHUNK_SECONDS
    return max(4, min(CHUNK_SECONDS, int(bounds[1])))


def prepare(
    body: dict[str, Any],
    moment: datetime | None = None,
    tracker: CostTracker | None = None,
) -> dict[str, Any]:
    if not isinstance(body, dict):
        raise MiddleRefusal("bad_request", "JSON object required.")
    wish = body.get("wish")
    if not isinstance(wish, str) or not wish.strip():
        raise MiddleRefusal("wish_required", "wish is required.")
    video = body.get("video_asset_id")
    if not isinstance(video, str) or not video:
        raise MiddleRefusal(
            "references_required",
            "video_asset_id is required. The file is not read.",
        )
    photos = _photo_ids(body)
    name = body.get("name") or "person"
    duration = body.get("duration_seconds", 13)
    if isinstance(duration, bool) or not isinstance(duration, (int, float)):
        raise MiddleRefusal("duration_rejected", "duration_seconds must be a number.")
    mode_name, mode_reason = choose_mode(body)
    mode = video_mode(mode_name)
    context = {
        "intent": wish.strip() + " character identity cinematic",
        "asset_type": "video",
        "style_keywords": ["cinematic", "character", "identity"],
        "budget_remaining_usd": None if tracker is None else tracker.usable_budget_usd,
        "motion_required": True,
        "wants_reference_conditioning": True,
        "wants_source_video_edit": mode["keeps_frames"],
        "duration_seconds": float(duration),
    }
    ranked = rank_model_cards(context)
    requested_model = body.get("model")
    if requested_model:
        if requested_model not in {item["model"] for item in ranked}:
            get_card(str(requested_model))
        model = str(requested_model)
    else:
        model = ranked[0]["model"]
    card = get_card(model)
    if mode["keeps_frames"] and not card_can_edit(card):
        raise MiddleRefusal(
            "mode_rejected",
            f"{model} cannot edit a source video. Pick an edit-capable card or use reference mode.",
        )
    sheet = character_sheet(str(name), photos)
    parts = chunks(float(duration), _chunk_limit(card))
    prompts = [
        compile_prompt(
            model,
            sheet["alias"],
            mode["mode"],
            part["duration_seconds"],
            wish.strip(),
            body.get("rules"),
        )
        for part in parts
    ]
    for part, compiled in zip(parts, prompts):
        part["prompt"] = compiled
    moment = moment or _now()
    why = ranked[0]["why"] if ranked and ranked[0]["model"] == model else (
        "Caller named the model. The ranking is still attached."
    )
    if mode["keeps_frames"]:
        why = "Edit-capable card ranked first for keeping the source frames.\n" + why
    else:
        why = "Motion reference does not keep the source frames.\n" + why
    card_payload = launch_card(
        model,
        prompts[0]["text"],
        {
            "mode": mode["mode"],
            "field": mode["field"],
            "resolution": DRAFT_RESOLUTION,
            "duration_seconds": float(duration),
            "aspect_ratio": body.get("aspect_ratio") or "9:16",
            "chunk_count": len(parts),
        },
        why,
        moment,
    )
    budget_block = _bind_budget(card_payload, tracker)
    plan = {
        "id": str(uuid.uuid4()),
        "wish": wish.strip(),
        "render_started": False,
        "generation_performed": False,
        "paid_call_allowed": False,
        "photo_ids": list(photos),
        "video_asset_id": video,
        "sheet": sheet,
        "video_mode": {**mode, "reason": mode_reason},
        "frames": frame_first(float(duration)),
        "mannequin": mannequin_passes(sheet["alias"], applies=mode["keeps_frames"]),
        "routing": ranked[:8],
        "prompt": prompts[0],
        "prompts": prompts,
        "draft": {**draft_plan(float(duration)), "chunks": parts},
        "launch": card_payload,
        "budget": budget_block,
        "trends": pick_trend(wish, 3),
        "qa": qa_plan(),
        "recovery": None,
    }
    return plan


def _bind_budget(card_payload: dict[str, Any], tracker: CostTracker | None) -> dict[str, Any]:
    usd = card_payload["price_estimate"]["usd"]
    if tracker is None or usd is None:
        return {
            "tracked": tracker is not None and usd is not None,
            "entry_id": None,
            "reserved": False,
            "usd": usd,
        }
    entry_id = tracker.estimate("identity_middle_layer", "draft_video", float(usd))
    return {
        "tracked": True,
        "entry_id": entry_id,
        "reserved": False,
        "usd": usd,
        "snapshot": tracker.cost_snapshot(),
    }


def approve(
    plan: dict[str, Any],
    gate: str,
    moment: datetime | None = None,
    tracker: CostTracker | None = None,
) -> dict[str, Any]:
    moment = moment or _now()
    if gate == "sheet":
        plan["sheet"]["approved"] = True
    elif gate == "frames":
        if not plan["sheet"]["approved"]:
            raise MiddleRefusal(
                "sheet_not_approved",
                "Approve the character sheet before the frames.",
            )
        plan["frames"]["approved"] = True
    elif gate == "launch":
        if not plan["frames"]["approved"]:
            raise MiddleRefusal(
                "frames_not_approved",
                "Approve the stills before the launch card.",
            )
        expires = datetime.fromisoformat(plan["launch"]["expires_at"])
        if moment > expires:
            raise MiddleRefusal(
                "card_expired",
                "The launch card expired. It was not refreshed into a running job.",
            )
        _reserve_launch(plan, tracker)
        plan["launch"]["approved"] = True
        plan["render_started"] = False
        plan["generation_performed"] = False
        plan["paid_call_allowed"] = False
    else:
        raise MiddleRefusal("gate_rejected", "Gate is sheet, frames or launch.")
    return plan


def _reserve_launch(plan: dict[str, Any], tracker: CostTracker | None) -> None:
    budget = plan.get("budget") or {}
    entry_id = budget.get("entry_id")
    if tracker is None or not entry_id:
        budget["reserved"] = False
        plan["budget"] = budget
        return
    tracker.approve_tool("identity_middle_layer")
    try:
        tracker.reserve(entry_id, human_approved=True)
    except BudgetExceededError as exc:
        raise MiddleRefusal("over_budget", str(exc)) from exc
    except ApprovalRequiredError as exc:
        raise MiddleRefusal("budget_approval_required", str(exc)) from exc
    budget["reserved"] = True
    budget["snapshot"] = tracker.cost_snapshot()
    plan["budget"] = budget


def run_qa(path: str, *, expected_seconds: float | None = None) -> dict[str, Any]:
    """Probe a local file with ffmpeg. Nothing is downloaded or generated."""
    plan = qa_plan()
    if shutil.which("ffmpeg") is None or shutil.which("ffprobe") is None:
        plan["reason"] = "ffmpeg_missing"
        return plan
    media = Path(path)
    if not media.is_file():
        raise MiddleRefusal(
            "qa_input_missing",
            "QA needs a local file. No download was attempted.",
        )
    probe = subprocess.run(
        [
            "ffprobe",
            "-v",
            "error",
            "-show_entries",
            "format=duration",
            "-of",
            "json",
            str(media),
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    duration = None
    if probe.returncode == 0:
        try:
            duration = float(json.loads(probe.stdout)["format"]["duration"])
        except (KeyError, TypeError, ValueError, json.JSONDecodeError):
            duration = None
    black = _ffmpeg_stderr(
        ["ffmpeg", "-i", str(media), "-vf", "blackdetect=d=0.1:pix_th=0.10", "-an", "-f", "null", "-"]
    )
    frozen = _ffmpeg_stderr(
        ["ffmpeg", "-i", str(media), "-vf", "freezedetect=n=0.003:d=0.5", "-an", "-f", "null", "-"]
    )
    silence = _ffmpeg_stderr(
        ["ffmpeg", "-i", str(media), "-af", "silencedetect=n=-50dB:d=0.3", "-vn", "-f", "null", "-"]
    )
    loud = _ffmpeg_stderr(
        ["ffmpeg", "-i", str(media), "-af", "loudnorm=I=-14:print_format=json", "-f", "null", "-"]
    )
    measured = _loudness(loud)
    duration_ok = duration is not None and (
        expected_seconds is None or abs(duration - expected_seconds) <= 0.35
    )
    plan.update(
        {
            "ran": True,
            "path": str(media),
            "duration_seconds": duration,
            "duration_ok": duration_ok,
            "black_frames": _spans(black, "black"),
            "frozen_frames": _spans(frozen, "freeze"),
            "silence": _spans(silence, "silence"),
            "loudness_lufs": measured,
            "loudness_ok": measured is not None and abs(measured - (-14)) <= 2,
        }
    )
    return plan


def _ffmpeg_stderr(cmd: list[str]) -> str:
    completed = subprocess.run(cmd, capture_output=True, text=True, check=False, timeout=60)
    return (completed.stderr or "") + (completed.stdout or "")


def _spans(log: str, kind: str) -> list[dict[str, float]]:
    pattern = re.compile(
        rf"{kind}_start:\s*([0-9.]+).*?{kind}_end:\s*([0-9.]+).*?{kind}_duration:\s*([0-9.]+)",
        re.S,
    )
    found = []
    for match in pattern.finditer(log):
        found.append(
            {
                "start": float(match.group(1)),
                "end": float(match.group(2)),
                "duration": float(match.group(3)),
            }
        )
    return found


def _loudness(log: str) -> float | None:
    match = re.search(r"\{[^{}]*\"input_i\"\s*:\s*\"([^\"]+)\"[^{}]*\}", log, re.S)
    if not match:
        return None
    try:
        return float(match.group(1))
    except ValueError:
        return None


class MiddleStore:
    def __init__(self, root: Path) -> None:
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)

    def save(self, plan: dict[str, Any]) -> dict[str, Any]:
        path = self.root / (plan["id"] + ".json")
        path.write_text(json.dumps(plan, ensure_ascii=False, indent=2), encoding="utf-8")
        return plan

    def get(self, plan_id: str) -> dict[str, Any] | None:
        path = self.root / (plan_id + ".json")
        if not path.is_file():
            return None
        return json.loads(path.read_text(encoding="utf-8"))
