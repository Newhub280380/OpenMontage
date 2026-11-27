"""Adapt public generation-agent skills and model cards into OpenMontage knowledge.

The source zip is research input. It is not committed. Product names, sales
copy, and third-party prompt bodies are not written into the tree. Run:

    python scripts/adapt_middle_knowledge.py --skills-zip <zip> --trends <trends.json>
"""

from __future__ import annotations

import argparse
import json
import re
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "skills" / "knowledge" / "middle"
BRAND = re.compile(r"givon|гивон", re.I)

RENAMES = {
    "givon-ai-create": "generation-lifecycle",
    "givon-ai-job-recovery": "generation-recovery",
    "givon-ai-model-router": "model-router",
    "givon-ai-marketplace-cards": "marketplace-card-generation",
    "givon-ai-product-photoshoot": "product-photoshoot",
}

SKIP_PARTS = ("/agents/", "/scripts/", "openai.yaml", "_all.json")


def _neutralize(text: str) -> str:
    parts = re.split(r"(?<=[.!?])\s+", text or "")
    kept = [part.strip() for part in parts if part.strip() and not BRAND.search(part)]
    return " ".join(kept).strip()


CALLS = (
    ("the planner_list_models", "the model-card catalog"),
    ("the planner_get_model_schema", "the model card"),
    ("the planner_quote_generation", "the launch-card estimate"),
    ("the planner_generate_content", "an approved OpenMontage provider tool"),
    ("the planner_get_generation_status", "the provider job status"),
    ("the planner_get_balance", "CostTracker budget remaining"),
    ("the planner_upload_file_asset", "a local asset id"),
    ("the planner_import_asset", "a local asset id"),
    ("the planner_list_assets", "the project asset list"),
    ("the planner_get_asset", "the project asset record"),
    ("the planner_archive_asset", "removing that asset from the project"),
    ("the planner_list_voices", "tts_selector"),
    ("the planner_list_avatars", "the character sheet"),
    ("the planner_upload_asset", "a local asset id"),
    ("the planner model list", "the model-card catalog"),
    ("the planner model get <id>", "the model card"),
    ("the planner model get", "the model card"),
    ("the planner voice list", "tts_selector"),
    ("the planner asset import", "a local asset id"),
    ("token price", "catalog estimate"),
    ("Token cost", "Catalog estimate"),
    ("token balance", "budget remaining"),
    ("token cost", "catalog estimate"),
    ("present token pricing metadata; do not invent missing totals.", "present catalog-unit metadata; do not invent a live price."),
)


def _clean_skill(text: str) -> str:
    text = re.sub(r"^---\n.*?\n---\n", "", text, count=1, flags=re.S)
    for old, new in RENAMES.items():
        text = text.replace(old, new)
    text = BRAND.sub("the planner", text)
    for old, new in CALLS:
        text = text.replace(old, new)
    text = re.sub(r"https?://\S+", "", text)
    text = text.replace("maxTokens", "the approved price ceiling")
    text = text.replace("--max-tokens", "the approved price ceiling")
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip() + "\n"


def _rewrite_branded(name: str, original: str) -> str | None:
    """Replace skills whose original text is a product client, not a craft note."""
    if name == "generation-lifecycle":
        return """# Generation lifecycle

Plan the smallest valid request, then stop before a paid call.

1. Infer the modality: image, video, music, or voice.
2. Read `model-cards/catalog.json` and rank video models with `lib.scoring.rank_providers` through `identity_middle_layer`. Do not invent a model that has no card.
3. Read that model's card before writing fields. Use only modes, durations, resolutions, and alias rules the card lists.
4. References are ids in the plan. This step does not upload or read photo bytes.
5. Build a launch card: model, full prompt, settings, catalog estimate, expiry. Record the estimate with `CostTracker`. Wait for sheet approval, then frame approval, then the launch card.
6. An expired card is not refreshed into a running job. A price that no longer matches the card is re-quoted. The planning tool never calls a provider.

A comparison or a prompt-only request does not authorize a paid job.
"""
    if name == "generation-recovery":
        return """# Generation recovery

When a result is not the person, do not add adjectives and run the same call again.

Use a stronger lever, in this order:

1. Add an approved close still of the face.
2. Shorten the chunk.
3. Leave one person in the frame.

A failed or rejected paid attempt is refunded in the cost log when the provider reports no charge. The planning layer itself never spends.
"""
    if name == "model-router":
        return """# Model router

Rank compatible cards. The catalog owns modes, limits, and alias rules. `lib.scoring` owns the weights: task fit 30%, quality 20%, control 15%, reliability 15%, cost 10%, speed 5%, continuity 5%.

For a person placed into an existing clip, require `source_video_edit`. A motion-reference card does not promise frame-by-frame preservation.

If the caller already named a model, check that model's card. Do not open a new contest unless the inputs changed.

A ranking is not permission to launch. Finish through the launch card.
"""
    if name == "auto-montage":
        return """# Assembly and QA

Assemble approved chunks locally. Do not copy a third-party montage script.

1. Probe local files with `ffprobe`. Do not download stand-in videos.
2. Write an edit decision list: user media in order, each missing shot marked as a planned generation with its own launch card.
3. Stitch approved files with `video_stitch`.
4. Run `identity_middle_layer` action `qa`: duration, black frames, frozen frames, silence, loudness near -14 LUFS.
5. One quoted launch card per missing shot. A folder of footage is not a blanket approval to spend.
"""
    if name == "model-selection-guidance":
        return _clean_skill(original).replace(
            "Finish through the planner-ai-create",
            "Finish through the launch card",
        )
    return None


def write_skills(zip_path: Path) -> list[str]:
    skills_root = OUT / "skills"
    if skills_root.exists():
        for child in skills_root.rglob("*"):
            if child.is_file():
                child.unlink()
    written: list[str] = []
    with zipfile.ZipFile(zip_path) as archive:
        names = [
            name
            for name in archive.namelist()
            if "/skills_embedded/" in name
            and name.endswith(".md")
            and not any(part in name for part in SKIP_PARTS)
        ]
        for name in sorted(names):
            relative = name.split("/skills_embedded/", 1)[1]
            skill_dir = relative.split("/", 1)[0]
            skill_dir = RENAMES.get(skill_dir, skill_dir)
            rest = relative.split("/", 1)[1] if "/" in relative else relative
            text = archive.read(name).decode("utf-8")
            if rest == "SKILL.md":
                replacement = _rewrite_branded(skill_dir, text)
                body = replacement if replacement is not None else _clean_skill(text)
                header = (
                    "Adapted for OpenMontage. Sales copy and third-party product calls were removed. "
                    "This file does not authorize a paid provider call.\n\n"
                )
                if not body.startswith("Adapted for"):
                    body = header + body
            else:
                body = _clean_skill(text)
            target = skills_root / skill_dir / rest
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(body, encoding="utf-8")
            written.append(str(target.relative_to(OUT)))
    return written


def write_cards(zip_path: Path) -> int:
    cards_dir = OUT / "model-cards"
    cards_dir.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(zip_path) as archive:
        raw = json.loads(archive.read("account/models/_catalog.json"))
    models = []
    for item in raw:
        params = {entry.get("key"): entry for entry in item.get("inputParameters") or []}
        authoring = item.get("promptAuthoring") or {}
        duration = params.get("duration") or {}
        resolution = params.get("resolution") or {}
        aspect = params.get("aspectRatio") or {}
        mode = params.get("mode") or {}
        card = {
            "id": item["id"],
            "kind": item.get("kind"),
            "provider": item.get("provider"),
            "label": item.get("label"),
            "input_modes": list(item.get("inputModes") or []),
            "mode_options": list(mode.get("options") or []),
            "resolutions": list(resolution.get("options") or []),
            "durations": list(duration.get("options") or []),
            "aspect_ratios": list(aspect.get("options") or []),
            "aliases": bool(authoring.get("requiresInlineReferenceAliases")),
            "prompt_language": authoring.get("defaultLanguage") or "en",
            "supported_languages": list(authoring.get("supportedLanguages") or []),
            "prompt_semantics": authoring.get("inputSemantics"),
            "tokens_per_second": (item.get("cost") or {}).get("tokensPerSecond"),
            "stability": "production" if item["id"] == "seedance-2.5" else "beta",
            "editorial": _neutralize(item.get("guidance") or "")[:700],
        }
        models.append(card)
        lines = [
            f"# {card['id']}",
            "",
            "Adapted model card. Sales copy was removed. This card does not quote a live price.",
            "",
            f"- Kind: {card['kind']}",
            f"- Provider family: {card['provider']}",
            f"- Label: {card['label']}",
            f"- Input modes: {', '.join(card['input_modes']) or 'unspecified'}",
            f"- Mode options: {', '.join(card['mode_options']) or 'unspecified'}",
            f"- Resolutions: {', '.join(map(str, card['resolutions'])) or 'unspecified'}",
            f"- Durations (seconds): {', '.join(map(str, card['durations'])) or 'unspecified'}",
            f"- Aspect ratios: {', '.join(card['aspect_ratios']) or 'unspecified'}",
            f"- Inline @ aliases: {'yes' if card['aliases'] else 'no'}",
            f"- Prompt language: {card['prompt_language']}",
            f"- Prompt semantics: {card['prompt_semantics'] or 'unspecified'}",
            "",
        ]
        if card["editorial"]:
            lines.extend(["## Editorial note", "", card["editorial"], ""])
        lines.extend(
            [
                "## OpenMontage use",
                "",
                "Edit-source means mode `edit` and field `sourceVideo`. "
                "Motion-reference means the clip controls motion and camera only. "
                "Rank this card with `lib.scoring`, then show a launch card before any paid call.",
                "",
            ]
        )
        (cards_dir / f"{card['id']}.md").write_text("\n".join(lines), encoding="utf-8")
    (cards_dir / "catalog.json").write_text(
        json.dumps({"models": models}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return len(models)


def write_trends(trends_path: Path) -> int:
    data = json.loads(trends_path.read_text(encoding="utf-8"))
    trends = []
    for item in data:
        prompt = item.get("prompt") or ""
        lowered = prompt.lower()
        settings = item.get("generation_settings") or {}
        slots = []
        for token in re.findall(r"\[[^\[\]\n]{1,40}\]", prompt):
            if token not in slots:
                slots.append(token)
            if len(slots) == 8:
                break
        categories = []
        for category in item.get("categories") or []:
            if isinstance(category, dict):
                categories.append(category.get("slug") or "")
        trends.append(
            {
                "slug": item.get("slug"),
                "title": item.get("title"),
                "generation_type": item.get("generation_type"),
                "model": settings.get("model_type"),
                "mode": settings.get("mode"),
                "resolution": settings.get("resolution") or settings.get("image_size"),
                "aspect_ratio": settings.get("aspect_ratio"),
                "duration_seconds": settings.get("video_duration"),
                "categories": [value for value in categories if value],
                "stand_in": any(
                    word in lowered
                    for word in (
                        "mannequin",
                        "mocap",
                        "motion-capture",
                        "motion capture",
                        "pass 1",
                    )
                ),
                "slots": slots,
            }
        )
    target = OUT / "trends"
    target.mkdir(parents=True, exist_ok=True)
    (target / "index.json").write_text(
        json.dumps(
            {
                "source": "public trend catalog, settings only",
                "prompts_included": False,
                "count": len(trends),
                "trends": trends,
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    (target / "TEMPLATE.md").write_text(
        """# Trend template

A trend entry is a settings template: model, mode, resolution, aspect, duration, and bracket slots. The original prompt text is not stored.

When a person asks to repeat a trend, copy the settings onto a launch card and fill the slots. Then compile the prompt in this order:

```
TASK & FORMAT
REFERENCES
ABSOLUTE REPLACEMENT RULES
PRESERVE
REPLACE
INTEGRATE
GLOBAL SETTINGS
TIMELINE
0.00-0.00 measured bounds only
MOTION
CONSTRAINTS
```

Edit-source uses `sourceVideo`. Motion-only uses `referenceVideo`. A stand-in entry (`stand_in: true`) uses the two-pass mannequin plan: actor to a colored suit, then the suit to the approved `@name` sheet.
""",
        encoding="utf-8",
    )
    return len(trends)


def write_index(skill_count: int, card_count: int, trend_count: int) -> None:
    skills = sorted(path.parent.name for path in (OUT / "skills").glob("*/SKILL.md"))
    lines = [
        "# Middle-layer knowledge",
        "",
        "Mechanics for keeping a person stable between a short wish and a video model.",
        "Adapted from publicly documented agent skills and model catalogs.",
        "Sales copy, product client calls, and third-party prompt bodies were removed.",
        "OpenMontage remains AGPL-3.0. These notes do not authorize a paid call.",
        "",
        f"- Skills: {skill_count} directories, {len(skills)} skill files",
        f"- Model cards: {card_count}",
        f"- Trend templates: {trend_count} (settings and slots only)",
        "",
        "Use them from the `identity-insert` pipeline and the `identity_middle_layer` tool.",
        "",
        "## Skills",
        "",
    ]
    for name in skills:
        lines.append(f"- `{name}`")
    lines.append("")
    (OUT / "README.md").write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--skills-zip", type=Path, required=True)
    parser.add_argument("--trends", type=Path, required=True)
    args = parser.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)
    skills = write_skills(args.skills_zip)
    skill_dirs = {Path(item).parts[1] for item in skills if item.startswith("skills/")}
    cards = write_cards(args.skills_zip)
    trends = write_trends(args.trends)
    write_index(len(skill_dirs), cards, trends)
    print(f"skills={len(skill_dirs)} files={len(skills)} cards={cards} trends={trends}")


if __name__ == "__main__":
    main()
