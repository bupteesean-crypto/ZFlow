from __future__ import annotations

import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

SCENE_PROMPT_PATH = Path(__file__).resolve().parents[3] / "worker" / "prompts" / "image" / "scene_v1.txt"
CHARACTER_PROMPT_PATH = Path(__file__).resolve().parents[3] / "worker" / "prompts" / "image" / "character_view_v1.txt"
DEFAULT_SCENE_PROMPT = (
    "Create a clean 3:4 portrait illustration for a video storyboard scene.\n\n"
    "Scene summary: {{scene_summary}}\n"
    "Mood: {{mood}}\n"
    "Keywords: {{keywords}}\n"
    "Style: {{style}}\n\n"
    "Constraints:\n"
    "- no text, no captions, no logos, no watermark\n"
    "- no people, no characters, empty environment\n"
    "- avoid low-quality artifacts or distortion\n"
    "- clear subject, readable silhouette\n"
)
DEFAULT_CHARACTER_PROMPT = (
    "Create a clean 3:4 portrait character design sheet view for a single character.\n\n"
    "Character: {{character_name}}\n"
    "Description: {{character_description}}\n"
    "Visual traits: {{visual_traits}}\n"
    "Style: {{style}}\n"
    "View: {{view}}\n\n"
    "Composition:\n"
    "- full-body view, centered\n"
    "- clear silhouette and proportions\n"
    "- neutral background\n\n"
    "Constraints:\n"
    "- no text, no captions, no logos, no watermark\n"
    "- avoid extra limbs or distorted anatomy\n"
    "- consistent style across views\n"
)


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _load_scene_template() -> str:
    try:
        return SCENE_PROMPT_PATH.read_text(encoding="utf-8").strip() or DEFAULT_SCENE_PROMPT
    except OSError:
        logger.warning("Failed to read scene prompt at %s; using default template", SCENE_PROMPT_PATH)
        return DEFAULT_SCENE_PROMPT


def _load_character_template() -> str:
    try:
        return CHARACTER_PROMPT_PATH.read_text(encoding="utf-8").strip() or DEFAULT_CHARACTER_PROMPT
    except OSError:
        logger.warning("Failed to read character prompt at %s; using default template", CHARACTER_PROMPT_PATH)
        return DEFAULT_CHARACTER_PROMPT


def _normalize_text(value: Any, fallback: str = "") -> str:
    return value.strip() if isinstance(value, str) and value.strip() else fallback


def _normalize_keywords(value: Any) -> list[str]:
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    if isinstance(value, str) and value.strip():
        return [item.strip() for item in value.split(",") if item.strip()]
    return []


def _render_template(template: str, context: dict[str, str]) -> str:
    output = template
    for key, value in context.items():
        output = output.replace(f"{{{{{key}}}}}", value)
    return output.strip()


def build_blueprint(llm_struct: dict, source_prompt: str) -> dict:
    summary_text = _normalize_text(llm_struct.get("summary"))
    keywords = _normalize_keywords(llm_struct.get("keywords"))

    logline = summary_text or _normalize_text(source_prompt, "Untitled concept")
    synopsis = summary_text or logline

    art_style = llm_struct.get("art_style") if isinstance(llm_struct.get("art_style"), dict) else {}
    style_name = _normalize_text(art_style.get("style_name"), "general illustration")
    style_prompt = _normalize_text(
        art_style.get("style_prompt"),
        "clean, consistent illustration, cohesive palette, soft contrast",
    )
    palette = art_style.get("palette") if isinstance(art_style.get("palette"), list) else []

    scenes_raw = llm_struct.get("scenes") if isinstance(llm_struct.get("scenes"), list) else []
    scenes = []
    if not scenes_raw:
        scenes_raw = [
            {
                "name": "Main Scene",
                "description": synopsis,
                "mood": keywords[0] if keywords else "neutral",
            }
        ]

    scene_template = _load_scene_template()
    for idx, scene in enumerate(scenes_raw, start=1):
        name = _normalize_text(scene.get("name"), f"Scene {idx}")
        description = _normalize_text(scene.get("description"), synopsis)
        mood = _normalize_text(scene.get("mood"), keywords[0] if keywords else "neutral")
        purpose = _normalize_text(scene.get("purpose"), "")
        prompt_hint = _render_template(
            scene_template,
            {
                "scene_summary": description,
                "mood": mood,
                "keywords": ", ".join(keywords),
                "style": style_prompt,
            },
        )
        scenes.append(
            {
                "id": f"scene_{idx}",
                "name": name,
                "description": description,
                "mood": mood,
                "purpose": purpose,
                "prompt_hint": prompt_hint,
            }
        )

    character_template = _load_character_template()
    subjects_raw = llm_struct.get("subjects") if isinstance(llm_struct.get("subjects"), list) else []
    subjects = []
    for idx, subject in enumerate(subjects_raw, start=1):
        name = _normalize_text(subject.get("name"), f"Character {idx}")
        description = _normalize_text(subject.get("description"), "")
        traits = subject.get("visual_traits") if isinstance(subject.get("visual_traits"), list) else []
        prompt_hint = f"{name}. {description}".strip()
        views = ["front", "side", "back"]
        view_prompts = {}
        for view in views:
            view_prompts[view] = _render_template(
                character_template,
                {
                    "character_name": name,
                    "character_description": description,
                    "visual_traits": ", ".join([str(item).strip() for item in traits if str(item).strip()]),
                    "style": style_prompt,
                    "view": view,
                },
            )
        subjects.append(
            {
                "id": f"char_{idx}",
                "name": name,
                "role": _normalize_text(subject.get("role"), ""),
                "description": description,
                "visual_traits": traits,
                "views": views,
                "view_prompts": view_prompts,
                "prompt_hint": prompt_hint,
            }
        )

    storyboard_raw = llm_struct.get("storyboard") if isinstance(llm_struct.get("storyboard"), list) else []
    storyboard = []
    for idx, shot in enumerate(storyboard_raw, start=1):
        description = _normalize_text(shot.get("description"), "")
        storyboard.append(
            {
                "id": f"shot_{idx}",
                "shot_number": idx,
                "scene_id": _normalize_text(shot.get("scene_id"), ""),
                "description": description,
                "duration_sec": shot.get("duration_sec", 3),
                "camera": _normalize_text(shot.get("camera"), ""),
                "prompt_hint": description,
            }
        )

    return {
        "version": "v1",
        "summary": {"logline": logline, "synopsis": synopsis, "keywords": keywords},
        "art_style": {
            "style_name": style_name,
            "style_prompt": style_prompt,
            "palette": palette,
            "reference": None,
        },
        "subjects": subjects,
        "scenes": scenes,
        "storyboard": storyboard,
        "generation": {
            "aspect_ratio": "3:4",
            "seed": None,
            "created_at": _utc_now(),
            "source_prompt": _normalize_text(source_prompt, ""),
        },
    }
