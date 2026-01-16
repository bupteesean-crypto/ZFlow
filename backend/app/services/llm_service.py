import json
import logging
from pathlib import Path
from urllib import error, request

from app.core.config import normalize_provider, settings

logger = logging.getLogger(__name__)

GLM_ENDPOINT = "https://open.bigmodel.cn/api/paas/v4/chat/completions"
PROMPT_PATH = (
    Path(__file__).resolve().parents[1]
    / "prompts"
    / "material_package_generation_v1.md"
)
REWRITE_PROMPT_PATH = (
    Path(__file__).resolve().parents[1] / "prompts" / "prompt_rewrite.md"
)
ART_STYLE_REWRITE_PATH = (
    Path(__file__).resolve().parents[1] / "prompts" / "art_style_rewrite_v1.md"
)
STORYBOARD_REWRITE_PATH = (
    Path(__file__).resolve().parents[1] / "prompts" / "storyboard_rewrite_v1.md"
)
BLUEPRINT_REWRITE_PATH = (
    Path(__file__).resolve().parents[1] / "prompts" / "blueprint_rewrite_v1.md"
)
PACKAGE_NAME_PATH = (
    Path(__file__).resolve().parents[1] / "prompts" / "package_name_v1.md"
)
REFINE_SUMMARY_PATH = Path(__file__).resolve().parents[1] / "prompts" / "refine_summary_v1.md"
REFINE_ART_STYLE_PATH = Path(__file__).resolve().parents[1] / "prompts" / "refine_art_style_v1.md"
REFINE_SUBJECTS_PATH = Path(__file__).resolve().parents[1] / "prompts" / "refine_subjects_v1.md"
REFINE_SCENES_PATH = Path(__file__).resolve().parents[1] / "prompts" / "refine_scenes_v1.md"
REFINE_STORYBOARD_PATH = Path(__file__).resolve().parents[1] / "prompts" / "refine_storyboard_v1.md"
REVIEW_PACKAGE_PATH = Path(__file__).resolve().parents[1] / "prompts" / "review_material_package_v1.md"
MATERIAL_PACKAGE_PROMPT_PATH = (
    Path(__file__).resolve().parents[1]
    / "prompts"
    / "material_package_generation_v1.md"
)
DEFAULT_SYSTEM_PROMPT = (
    "You are generating a complete creative material package for a short-form video. "
    "Return JSON only with keys: summary, art_style, subjects, scenes, storyboard. "
    "Use Chinese for all user-facing fields. Do not copy user input verbatim. "
    "Include psychological contrast, narrative progression, scene purpose, and character state changes. "
    "No Markdown, no extra text."
)
DEFAULT_REWRITE_PROMPT = (
    "You are a prompt rewrite assistant for image generation. "
    "Given the original prompt and the user's feedback, rewrite the full prompt. "
    "Output the revised full prompt only. Preserve constraints unless the feedback asks to change them. "
    "Apply the feedback directly; do not add unrelated changes. No Markdown, no explanations."
)
DEFAULT_ART_STYLE_REWRITE_PROMPT = (
    "You are a prompt rewrite assistant for art style edits. "
    "Given the current art style and user feedback, rewrite the FULL art style. "
    "Output JSON only with keys: style_name, style_prompt, palette (Chinese output required). "
    "Apply feedback directly. Preserve details not requested to change. "
    "No Markdown, no extra text."
)
DEFAULT_STORYBOARD_REWRITE_PROMPT = (
    "You are a prompt rewrite assistant for storyboard description edits. "
    "Given the current storyboard description and user feedback, rewrite the FULL description. "
    "Output JSON only with keys: description (Chinese output required). "
    "Apply feedback directly. Preserve details not requested to change. "
    "No Markdown, no extra text."
)
DEFAULT_BLUEPRINT_REWRITE_PROMPT = (
    "You are a blueprint rewrite assistant for video material packages. "
    "Given previous blueprint JSON, user feedback, and original idea, output JSON with keys: "
    "summary, art_style, subjects, scenes, storyboard. "
    "Use Chinese for all user-facing fields. Do not copy feedback verbatim unless requested. "
    "Preserve structure and intent when not asked to change. No Markdown, no extra text."
)
DEFAULT_PACKAGE_NAME_PROMPT = (
    "You are a naming assistant for video material packages. "
    "Output JSON only with key: name. Name must be Chinese, 2 to 10 characters, "
    "memorable and relevant. No Markdown, no extra text."
)
DEFAULT_MATERIAL_PACKAGE_PROMPT = DEFAULT_SYSTEM_PROMPT
DEFAULT_REFINE_SUMMARY_PROMPT = (
    "Return JSON only with keys: summary, keywords. "
    "Rewrite the summary and keywords for clarity and consistency."
)
DEFAULT_REFINE_ART_STYLE_PROMPT = (
    "Return JSON only with key art_style containing style_name, style_prompt, palette."
)
DEFAULT_REFINE_SUBJECTS_PROMPT = "Return JSON only with key subjects."
DEFAULT_REFINE_SCENES_PROMPT = "Return JSON only with key scenes."
DEFAULT_REFINE_STORYBOARD_PROMPT = "Return JSON only with key storyboard."
DEFAULT_REVIEW_PROMPT = (
    "Return JSON only with keys: pass, feedback(summary, art_style, subjects, scenes, storyboard)."
)
MAX_REVIEW_ATTEMPTS = 5

GENERAL_MODE_BLOCK = (
    "Mode: general. Expand a short idea into a complete short-form video creative plan. "
    "Invent characters, scenes, emotions, contrast, and rhythm. "
    "Ensure the result is rich, layered, and narrative-driven."
)
PRO_MODE_BLOCK = (
    "Mode: pro. Treat the user input as constraints. Preserve any provided structure when present. "
    "Fill missing parts professionally without changing intended meaning."
)


def _normalize_text(value: object, fallback: str = "") -> str:
    return value.strip() if isinstance(value, str) and value.strip() else fallback


def _normalize_keywords(value: object) -> list[str]:
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    if isinstance(value, str) and value.strip():
        return [item.strip() for item in value.split(",") if item.strip()]
    return []


def _normalize_generation_mode(value: object) -> str:
    mode = (value or "").strip().lower() if isinstance(value, str) else ""
    if mode in {"pro", "professional", "专业"}:
        return "pro"
    if mode in {"general", "通用"}:
        return "general"
    return "general"


def _default_art_style() -> dict:
    return {
        "style_name": "general illustration",
        "style_prompt": "clean, consistent illustration, cohesive palette, soft contrast",
        "palette": [],
    }


def _normalize_art_style(value: object) -> dict:
    if not isinstance(value, dict):
        return _default_art_style()
    style_name = _normalize_text(
        value.get("style_name") or value.get("name"), "general illustration"
    )
    style_prompt = _normalize_text(
        value.get("style_prompt") or value.get("prompt"),
        "clean, consistent illustration, cohesive palette, soft contrast",
    )
    palette = value.get("palette") if isinstance(value.get("palette"), list) else []
    palette = [str(item).strip() for item in palette if str(item).strip()]
    return {"style_name": style_name, "style_prompt": style_prompt, "palette": palette}


def _default_subjects(fallback_text: str) -> list[dict]:
    description = fallback_text or "Main character description."
    return [
        {
            "name": "Main Character",
            "description": description,
            "role": "protagonist",
            "visual_traits": [],
        }
    ]


def _normalize_subjects(value: object, fallback_text: str) -> list[dict]:
    if not isinstance(value, list):
        return _default_subjects(fallback_text)
    subjects = []
    for item in value:
        if not isinstance(item, dict):
            continue
        name = _normalize_text(item.get("name"), "")
        description = _normalize_text(item.get("description"), "")
        role = _normalize_text(item.get("role"), "")
        traits = (
            item.get("visual_traits")
            if isinstance(item.get("visual_traits"), list)
            else []
        )
        traits = [str(trait).strip() for trait in traits if str(trait).strip()]
        if not name and not description:
            continue
        subjects.append(
            {
                "name": name or "Main Character",
                "description": description,
                "role": role,
                "visual_traits": traits,
            }
        )
    return subjects if subjects else _default_subjects(fallback_text)


def _default_scenes(fallback_text: str) -> list[dict]:
    description = fallback_text or "Main scene."
    return [{"name": "Main Scene", "description": description, "mood": "neutral"}]


def _normalize_scenes(value: object, fallback_text: str) -> list[dict]:
    if not isinstance(value, list):
        return _default_scenes(fallback_text)
    scenes = []
    for item in value:
        if not isinstance(item, dict):
            continue
        name = _normalize_text(item.get("name"), "")
        description = _normalize_text(item.get("description"), "")
        mood = _normalize_text(item.get("mood"), "neutral")
        if not name and not description:
            continue
        scenes.append(
            {
                "name": name or "Main Scene",
                "description": description or fallback_text,
                "mood": mood,
            }
        )
    return scenes if scenes else _default_scenes(fallback_text)


def _default_storyboard(fallback_text: str) -> list[dict]:
    description = fallback_text or "Main shot."
    return [
        {
            "description": description,
            "scene_id": "scene_1",
            "duration_sec": 3,
            "camera": "mid-shot",
        }
    ]


def _normalize_storyboard(value: object, fallback_text: str) -> list[dict]:
    if not isinstance(value, list):
        return _default_storyboard(fallback_text)
    shots = []
    for item in value:
        if not isinstance(item, dict):
            continue
        description = _normalize_text(item.get("description"), "")
        if not description:
            continue
        scene_id = _normalize_text(item.get("scene_id"), "scene_1")
        duration = item.get("duration_sec")
        if isinstance(duration, (int, float)) and duration > 0:
            duration_sec = int(duration)
        else:
            duration_sec = 3
        camera = _normalize_text(item.get("camera"), "")
        shots.append(
            {
                "description": description,
                "scene_id": scene_id,
                "duration_sec": duration_sec,
                "camera": camera,
            }
        )
    return shots if shots else _default_storyboard(fallback_text)


def _normalize_summary_payload(parsed: dict, base_summary: str, base_keywords: list[str]) -> tuple[str, list[str]]:
    summary = _normalize_text(parsed.get("summary"), base_summary)
    keywords = _normalize_keywords(parsed.get("keywords"))
    if not keywords:
        keywords = base_keywords or []
    return summary, keywords


def _normalize_subjects_with_prompts(
    value: object,
    base_subjects: list[dict],
    fallback_text: str,
) -> list[dict]:
    if not isinstance(value, list):
        value = []
    if not base_subjects:
        base_subjects = _default_subjects(fallback_text)
    merged: list[dict] = []
    for idx, base in enumerate(base_subjects):
        item = value[idx] if idx < len(value) and isinstance(value[idx], dict) else {}
        name = _normalize_text(item.get("name"), _normalize_text(base.get("name"), f"Character {idx + 1}"))
        description = _normalize_text(item.get("description"), _normalize_text(base.get("description"), fallback_text))
        role = _normalize_text(item.get("role"), _normalize_text(base.get("role"), ""))
        traits = item.get("visual_traits") if isinstance(item.get("visual_traits"), list) else base.get("visual_traits")
        traits = [str(trait).strip() for trait in (traits or []) if str(trait).strip()]
        image_prompt = _normalize_text(item.get("image_prompt"), _normalize_text(base.get("image_prompt"), ""))
        if not image_prompt:
            image_prompt = f"{name}. {description}".strip()
            if traits:
                image_prompt = f"{image_prompt} Visual traits: {', '.join(traits)}"
        merged.append(
            {
                "name": name,
                "description": description,
                "role": role,
                "visual_traits": traits,
                "image_prompt": image_prompt,
            }
        )
    return merged


def _normalize_scenes_with_prompts(
    value: object,
    base_scenes: list[dict],
    fallback_text: str,
) -> list[dict]:
    if not isinstance(value, list):
        value = []
    if not base_scenes:
        base_scenes = _default_scenes(fallback_text)
    merged: list[dict] = []
    for idx, base in enumerate(base_scenes):
        item = value[idx] if idx < len(value) and isinstance(value[idx], dict) else {}
        name = _normalize_text(item.get("name"), _normalize_text(base.get("name"), f"Scene {idx + 1}"))
        description = _normalize_text(item.get("description"), _normalize_text(base.get("description"), fallback_text))
        mood = _normalize_text(item.get("mood"), _normalize_text(base.get("mood"), "neutral"))
        purpose = _normalize_text(item.get("purpose"), _normalize_text(base.get("purpose"), ""))
        image_prompt = _normalize_text(item.get("image_prompt"), _normalize_text(base.get("image_prompt"), ""))
        if not image_prompt:
            image_prompt = f"{description}".strip()
            if mood:
                image_prompt = f"{image_prompt} Mood: {mood}".strip()
        merged.append(
            {
                "name": name,
                "description": description,
                "mood": mood,
                "purpose": purpose,
                "image_prompt": image_prompt,
            }
        )
    return merged


def _normalize_storyboard_with_prompts(
    value: object,
    base_storyboard: list[dict],
    fallback_text: str,
) -> list[dict]:
    if not isinstance(value, list):
        value = []
    if not base_storyboard:
        base_storyboard = _default_storyboard(fallback_text)
    merged: list[dict] = []
    for idx, base in enumerate(base_storyboard):
        item = value[idx] if idx < len(value) and isinstance(value[idx], dict) else {}
        description = _normalize_text(item.get("description"), _normalize_text(base.get("description"), fallback_text))
        scene_id = _normalize_text(item.get("scene_id"), _normalize_text(base.get("scene_id"), "scene_1"))
        duration_raw = item.get("duration_sec", base.get("duration_sec"))
        duration_sec = int(duration_raw) if isinstance(duration_raw, (int, float)) and duration_raw > 0 else 3
        camera = _normalize_text(item.get("camera"), _normalize_text(base.get("camera"), ""))
        image_prompt = _normalize_text(item.get("image_prompt"), _normalize_text(base.get("image_prompt"), ""))
        if not image_prompt:
            image_prompt = description
        subject_names = item.get("subject_names") if isinstance(item.get("subject_names"), list) else []
        subject_names = [str(name).strip() for name in subject_names if str(name).strip()]
        subject_ids = item.get("subject_ids") if isinstance(item.get("subject_ids"), list) else []
        subject_ids = [str(value).strip() for value in subject_ids if str(value).strip()]
        merged.append(
            {
                "description": description,
                "scene_id": scene_id,
                "duration_sec": duration_sec,
                "camera": camera,
                "image_prompt": image_prompt,
                "subject_names": subject_names,
                "subject_ids": subject_ids,
            }
        )
    return merged


def _normalize_review_result(parsed: dict) -> tuple[bool, dict]:
    if not isinstance(parsed, dict):
        return False, {}
    passed = parsed.get("pass") is True
    feedback_raw = parsed.get("feedback") if isinstance(parsed.get("feedback"), dict) else {}
    feedback = {}
    for key in ("summary", "art_style", "subjects", "scenes", "storyboard"):
        feedback[key] = _normalize_text(feedback_raw.get(key), "")
    return passed, feedback


def _coerce_structured_output(parsed: dict, fallback_text: str) -> dict:
    summary = _normalize_text(parsed.get("summary"), fallback_text)
    keywords = _normalize_keywords(parsed.get("keywords"))
    art_style = _normalize_art_style(parsed.get("art_style"))
    subjects = _normalize_subjects(parsed.get("subjects"), summary)
    scenes = _normalize_scenes(parsed.get("scenes"), summary)
    storyboard = _normalize_storyboard(parsed.get("storyboard"), summary)
    return {
        "summary": summary,
        "keywords": keywords,
        "art_style": art_style,
        "subjects": subjects,
        "scenes": scenes,
        "storyboard": storyboard,
    }


def _normalize_material_package_struct(parsed: dict) -> dict:
    if not isinstance(parsed, dict):
        return {}
    summary = _normalize_text(parsed.get("summary"), "")
    keywords = _normalize_keywords(parsed.get("keywords"))

    art_style_raw = (
        parsed.get("art_style") if isinstance(parsed.get("art_style"), dict) else {}
    )
    style_name = _normalize_text(art_style_raw.get("style_name"), "")
    style_prompt = _normalize_text(art_style_raw.get("style_prompt"), "")
    palette = (
        art_style_raw.get("palette")
        if isinstance(art_style_raw.get("palette"), list)
        else []
    )
    palette = [str(item).strip() for item in palette if str(item).strip()]
    art_style = {
        "style_name": style_name,
        "style_prompt": style_prompt,
        "palette": palette,
    }

    subjects = []
    subjects_raw = (
        parsed.get("subjects") if isinstance(parsed.get("subjects"), list) else []
    )
    for item in subjects_raw:
        if not isinstance(item, dict):
            continue
        name = _normalize_text(item.get("name"), "")
        description = _normalize_text(item.get("description"), "")
        role = _normalize_text(item.get("role"), "")
        traits = (
            item.get("visual_traits")
            if isinstance(item.get("visual_traits"), list)
            else []
        )
        traits = [str(trait).strip() for trait in traits if str(trait).strip()]
        image_prompt = _normalize_text(item.get("image_prompt"), "")
        if not name and not description:
            continue
        subjects.append(
            {
                "name": name,
                "description": description,
                "role": role,
                "visual_traits": traits,
                "image_prompt": image_prompt,
            }
        )

    scenes = []
    scenes_raw = parsed.get("scenes") if isinstance(parsed.get("scenes"), list) else []
    for item in scenes_raw:
        if not isinstance(item, dict):
            continue
        name = _normalize_text(item.get("name"), "")
        description = _normalize_text(item.get("description"), "")
        mood = _normalize_text(item.get("mood"), "")
        purpose = _normalize_text(item.get("purpose"), "")
        image_prompt = _normalize_text(item.get("image_prompt"), "")
        if not name and not description:
            continue
        scenes.append(
            {
                "name": name,
                "description": description,
                "mood": mood,
                "purpose": purpose,
                "image_prompt": image_prompt,
            }
        )

    storyboard = []
    storyboard_raw = (
        parsed.get("storyboard") if isinstance(parsed.get("storyboard"), list) else []
    )
    for item in storyboard_raw:
        if not isinstance(item, dict):
            continue
        description = _normalize_text(item.get("description"), "")
        scene_id = _normalize_text(item.get("scene_id"), "")
        duration_raw = item.get("duration_sec")
        duration_sec = (
            int(duration_raw)
            if isinstance(duration_raw, (int, float)) and duration_raw > 0
            else 0
        )
        camera = _normalize_text(item.get("camera"), "")
        image_prompt = _normalize_text(item.get("image_prompt"), "")
        subject_names = item.get("subject_names") if isinstance(item.get("subject_names"), list) else []
        subject_names = [str(name).strip() for name in subject_names if str(name).strip()]
        subject_ids = item.get("subject_ids") if isinstance(item.get("subject_ids"), list) else []
        subject_ids = [str(value).strip() for value in subject_ids if str(value).strip()]
        if not description:
            continue
        storyboard.append(
            {
                "description": description,
                "scene_id": scene_id,
                "duration_sec": duration_sec,
                "camera": camera,
                "image_prompt": image_prompt,
                "subject_names": subject_names,
                "subject_ids": subject_ids,
            }
        )

    return {
        "summary": summary,
        "keywords": keywords,
        "art_style": art_style,
        "subjects": subjects,
        "scenes": scenes,
        "storyboard": storyboard,
    }


def _validate_material_package_struct(parsed: dict) -> tuple[bool, str]:
    if not parsed:
        return False, "empty LLM output"
    if not _normalize_text(parsed.get("summary"), ""):
        return False, "summary missing"
    art_style = (
        parsed.get("art_style") if isinstance(parsed.get("art_style"), dict) else {}
    )
    if not _normalize_text(art_style.get("style_name"), "") and not _normalize_text(
        art_style.get("style_prompt"), ""
    ):
        return False, "art_style missing"
    subjects = (
        parsed.get("subjects") if isinstance(parsed.get("subjects"), list) else []
    )
    if not subjects:
        return False, "subjects missing"
    scenes = parsed.get("scenes") if isinstance(parsed.get("scenes"), list) else []
    if not scenes:
        return False, "scenes missing"
    storyboard = (
        parsed.get("storyboard") if isinstance(parsed.get("storyboard"), list) else []
    )
    if not storyboard:
        return False, "storyboard missing"
    return True, ""


def _blueprint_to_llm_struct(blueprint: dict) -> dict:
    summary = blueprint.get("summary") if isinstance(blueprint, dict) else {}
    art_style = blueprint.get("art_style") if isinstance(blueprint, dict) else {}
    return {
        "summary": summary.get("logline") or summary.get("synopsis") or "",
        "keywords": summary.get("keywords")
        if isinstance(summary.get("keywords"), list)
        else [],
        "art_style": art_style if isinstance(art_style, dict) else {},
        "subjects": blueprint.get("subjects")
        if isinstance(blueprint.get("subjects"), list)
        else [],
        "scenes": blueprint.get("scenes")
        if isinstance(blueprint.get("scenes"), list)
        else [],
        "storyboard": blueprint.get("storyboard")
        if isinstance(blueprint.get("storyboard"), list)
        else [],
    }


def _load_system_prompt() -> str:
    try:
        return PROMPT_PATH.read_text(encoding="utf-8").strip() or DEFAULT_SYSTEM_PROMPT
    except OSError:
        logger.warning(
            "Failed to read prompt asset at %s; using default prompt", PROMPT_PATH
        )
        return DEFAULT_SYSTEM_PROMPT


SYSTEM_PROMPT = _load_system_prompt()


def _load_material_package_prompt() -> str:
    try:
        return (
            MATERIAL_PACKAGE_PROMPT_PATH.read_text(encoding="utf-8").strip()
            or DEFAULT_MATERIAL_PACKAGE_PROMPT
        )
    except OSError:
        logger.warning(
            "Failed to read material package prompt at %s; using default prompt",
            MATERIAL_PACKAGE_PROMPT_PATH,
        )
        return DEFAULT_MATERIAL_PACKAGE_PROMPT


MATERIAL_PACKAGE_PROMPT = _load_material_package_prompt()


def _load_rewrite_prompt() -> str:
    try:
        return (
            REWRITE_PROMPT_PATH.read_text(encoding="utf-8").strip()
            or DEFAULT_REWRITE_PROMPT
        )
    except OSError:
        logger.warning(
            "Failed to read rewrite prompt at %s; using default prompt",
            REWRITE_PROMPT_PATH,
        )
        return DEFAULT_REWRITE_PROMPT


REWRITE_PROMPT = _load_rewrite_prompt()


def _load_art_style_prompt() -> str:
    try:
        return (
            ART_STYLE_REWRITE_PATH.read_text(encoding="utf-8").strip()
            or DEFAULT_ART_STYLE_REWRITE_PROMPT
        )
    except OSError:
        logger.warning(
            "Failed to read art style prompt at %s; using default prompt",
            ART_STYLE_REWRITE_PATH,
        )
        return DEFAULT_ART_STYLE_REWRITE_PROMPT


def _load_storyboard_prompt() -> str:
    try:
        return (
            STORYBOARD_REWRITE_PATH.read_text(encoding="utf-8").strip()
            or DEFAULT_STORYBOARD_REWRITE_PROMPT
        )
    except OSError:
        logger.warning(
            "Failed to read storyboard prompt at %s; using default prompt",
            STORYBOARD_REWRITE_PATH,
        )
        return DEFAULT_STORYBOARD_REWRITE_PROMPT


ART_STYLE_REWRITE_PROMPT = _load_art_style_prompt()
STORYBOARD_REWRITE_PROMPT = _load_storyboard_prompt()


def _load_blueprint_prompt() -> str:
    try:
        return (
            BLUEPRINT_REWRITE_PATH.read_text(encoding="utf-8").strip()
            or DEFAULT_BLUEPRINT_REWRITE_PROMPT
        )
    except OSError:
        logger.warning(
            "Failed to read blueprint prompt at %s; using default prompt",
            BLUEPRINT_REWRITE_PATH,
        )
        return DEFAULT_BLUEPRINT_REWRITE_PROMPT


def _load_package_name_prompt() -> str:
    try:
        return (
            PACKAGE_NAME_PATH.read_text(encoding="utf-8").strip()
            or DEFAULT_PACKAGE_NAME_PROMPT
        )
    except OSError:
        logger.warning(
            "Failed to read package name prompt at %s; using default prompt",
            PACKAGE_NAME_PATH,
        )
        return DEFAULT_PACKAGE_NAME_PROMPT


BLUEPRINT_REWRITE_PROMPT = _load_blueprint_prompt()
PACKAGE_NAME_PROMPT = _load_package_name_prompt()


def _load_refine_summary_prompt() -> str:
    try:
        return REFINE_SUMMARY_PATH.read_text(encoding="utf-8").strip() or DEFAULT_REFINE_SUMMARY_PROMPT
    except OSError:
        logger.warning("Failed to read refine summary prompt at %s; using default prompt", REFINE_SUMMARY_PATH)
        return DEFAULT_REFINE_SUMMARY_PROMPT


def _load_refine_art_style_prompt() -> str:
    try:
        return REFINE_ART_STYLE_PATH.read_text(encoding="utf-8").strip() or DEFAULT_REFINE_ART_STYLE_PROMPT
    except OSError:
        logger.warning("Failed to read refine art style prompt at %s; using default prompt", REFINE_ART_STYLE_PATH)
        return DEFAULT_REFINE_ART_STYLE_PROMPT


def _load_refine_subjects_prompt() -> str:
    try:
        return REFINE_SUBJECTS_PATH.read_text(encoding="utf-8").strip() or DEFAULT_REFINE_SUBJECTS_PROMPT
    except OSError:
        logger.warning("Failed to read refine subjects prompt at %s; using default prompt", REFINE_SUBJECTS_PATH)
        return DEFAULT_REFINE_SUBJECTS_PROMPT


def _load_refine_scenes_prompt() -> str:
    try:
        return REFINE_SCENES_PATH.read_text(encoding="utf-8").strip() or DEFAULT_REFINE_SCENES_PROMPT
    except OSError:
        logger.warning("Failed to read refine scenes prompt at %s; using default prompt", REFINE_SCENES_PATH)
        return DEFAULT_REFINE_SCENES_PROMPT


def _load_refine_storyboard_prompt() -> str:
    try:
        return REFINE_STORYBOARD_PATH.read_text(encoding="utf-8").strip() or DEFAULT_REFINE_STORYBOARD_PROMPT
    except OSError:
        logger.warning("Failed to read refine storyboard prompt at %s; using default prompt", REFINE_STORYBOARD_PATH)
        return DEFAULT_REFINE_STORYBOARD_PROMPT


def _load_review_prompt() -> str:
    try:
        return REVIEW_PACKAGE_PATH.read_text(encoding="utf-8").strip() or DEFAULT_REVIEW_PROMPT
    except OSError:
        logger.warning("Failed to read review prompt at %s; using default prompt", REVIEW_PACKAGE_PATH)
        return DEFAULT_REVIEW_PROMPT


REFINE_SUMMARY_PROMPT = _load_refine_summary_prompt()
REFINE_ART_STYLE_PROMPT = _load_refine_art_style_prompt()
REFINE_SUBJECTS_PROMPT = _load_refine_subjects_prompt()
REFINE_SCENES_PROMPT = _load_refine_scenes_prompt()
REFINE_STORYBOARD_PROMPT = _load_refine_storyboard_prompt()
REVIEW_PACKAGE_PROMPT = _load_review_prompt()


class LLMService:
    def __init__(self) -> None:
        self._provider = settings.llm_provider

    def generate(self, prompt: str) -> dict:
        provider = normalize_provider(self._provider)
        if not provider or provider == "mock":
            return self._mock_output(prompt)
        if provider == "glm":
            return self._generate_glm(prompt)
        logger.warning("LLM provider %s not implemented; using mock output", provider)
        return self._mock_output(prompt)

    def generate_text(self, prompt: str) -> str:
        result = self.generate(prompt)
        if isinstance(result, dict):
            storyline = result.get("storyline")
            summary = result.get("summary")
            if isinstance(storyline, str) and storyline.strip():
                return storyline.strip()
            if isinstance(summary, str) and summary.strip():
                return summary.strip()
        return "Demo content"

    def _build_material_package_prompt(self, mode: str) -> tuple[str, float]:
        normalized_mode = _normalize_generation_mode(mode)
        if normalized_mode == "pro":
            return f"{MATERIAL_PACKAGE_PROMPT}\n\n{PRO_MODE_BLOCK}", 0.4
        return f"{MATERIAL_PACKAGE_PROMPT}\n\n{GENERAL_MODE_BLOCK}", 0.7

    def _generate_base_package(
        self,
        prompt: str,
        mode: str,
        previous_package: dict | None,
        feedback: str | None,
        documents: list | None,
    ) -> dict:
        system_prompt, temperature = self._build_material_package_prompt(mode)
        payload_context = {
            "mode": _normalize_generation_mode(mode),
            "user_prompt": (prompt or "").strip(),
            "source_prompt": (prompt or "").strip(),
            "previous_package": previous_package or {},
            "feedback": (feedback or "").strip(),
            "documents": documents or [],
        }
        logger.info(
            "llm.call stage=material_package_base mode=%s prompt_chars=%s feedback=%s",
            payload_context["mode"],
            len(payload_context["user_prompt"]),
            bool(payload_context["feedback"]),
        )
        content = self._call_glm(system_prompt, payload_context, temperature=temperature)
        parsed = self._parse_json_dict(content)
        normalized = _normalize_material_package_struct(parsed)
        valid, reason = _validate_material_package_struct(normalized)
        if not valid:
            logger.error("LLM output invalid for base package generation: %s", reason)
            raise ValueError(f"Invalid LLM output: {reason}")
        return normalized

    def _refine_summary(
        self,
        prompt: str,
        base_summary: str,
        base_keywords: list[str],
        feedback: str | None,
    ) -> tuple[str, list[str]]:
        payload_context = {
            "user_prompt": (prompt or "").strip(),
            "base_summary": (base_summary or "").strip(),
            "base_keywords": base_keywords or [],
            "feedback": (feedback or "").strip(),
        }
        content = self._call_glm(REFINE_SUMMARY_PROMPT, payload_context, temperature=0.4)
        parsed = self._parse_json_dict(content)
        return _normalize_summary_payload(parsed, base_summary, base_keywords)

    def _refine_art_style(
        self,
        prompt: str,
        base_art_style: dict,
        summary: str,
        keywords: list[str],
        feedback: str | None,
    ) -> dict:
        payload_context = {
            "user_prompt": (prompt or "").strip(),
            "base_art_style": _normalize_art_style(base_art_style or {}),
            "summary": (summary or "").strip(),
            "keywords": keywords or [],
            "feedback": (feedback or "").strip(),
        }
        content = self._call_glm(REFINE_ART_STYLE_PROMPT, payload_context, temperature=0.4)
        parsed = self._parse_json_dict(content)
        art_style = parsed.get("art_style") if isinstance(parsed.get("art_style"), dict) else parsed
        return _normalize_art_style(art_style or base_art_style)

    def _refine_subjects(
        self,
        prompt: str,
        base_subjects: list[dict],
        summary: str,
        keywords: list[str],
        art_style: dict,
        feedback: str | None,
    ) -> list[dict]:
        payload_context = {
            "user_prompt": (prompt or "").strip(),
            "base_subjects": base_subjects or [],
            "summary": (summary or "").strip(),
            "keywords": keywords or [],
            "art_style": _normalize_art_style(art_style or {}),
            "feedback": (feedback or "").strip(),
        }
        content = self._call_glm(REFINE_SUBJECTS_PROMPT, payload_context, temperature=0.4)
        parsed = self._parse_json_dict(content)
        subjects = parsed.get("subjects") if isinstance(parsed.get("subjects"), list) else parsed
        return _normalize_subjects_with_prompts(subjects, base_subjects, summary)

    def _refine_scenes(
        self,
        prompt: str,
        base_scenes: list[dict],
        summary: str,
        keywords: list[str],
        art_style: dict,
        subjects: list[dict],
        feedback: str | None,
    ) -> list[dict]:
        payload_context = {
            "user_prompt": (prompt or "").strip(),
            "base_scenes": base_scenes or [],
            "summary": (summary or "").strip(),
            "keywords": keywords or [],
            "art_style": _normalize_art_style(art_style or {}),
            "subjects": subjects or [],
            "feedback": (feedback or "").strip(),
        }
        content = self._call_glm(REFINE_SCENES_PROMPT, payload_context, temperature=0.4)
        parsed = self._parse_json_dict(content)
        scenes = parsed.get("scenes") if isinstance(parsed.get("scenes"), list) else parsed
        return _normalize_scenes_with_prompts(scenes, base_scenes, summary)

    def _refine_storyboard(
        self,
        prompt: str,
        base_storyboard: list[dict],
        summary: str,
        keywords: list[str],
        art_style: dict,
        scenes: list[dict],
        subjects: list[dict],
        feedback: str | None,
    ) -> list[dict]:
        payload_context = {
            "user_prompt": (prompt or "").strip(),
            "base_storyboard": base_storyboard or [],
            "summary": (summary or "").strip(),
            "keywords": keywords or [],
            "art_style": _normalize_art_style(art_style or {}),
            "scenes": scenes or [],
            "subjects": subjects or [],
            "feedback": (feedback or "").strip(),
        }
        content = self._call_glm(REFINE_STORYBOARD_PROMPT, payload_context, temperature=0.4)
        parsed = self._parse_json_dict(content)
        storyboard = parsed.get("storyboard") if isinstance(parsed.get("storyboard"), list) else parsed
        return _normalize_storyboard_with_prompts(storyboard, base_storyboard, summary)

    def _review_package(self, prompt: str, package_struct: dict) -> tuple[bool, dict]:
        payload_context = {
            "user_prompt": (prompt or "").strip(),
            "summary": package_struct.get("summary") or "",
            "keywords": package_struct.get("keywords") or [],
            "art_style": package_struct.get("art_style") or {},
            "subjects": package_struct.get("subjects") or [],
            "scenes": package_struct.get("scenes") or [],
            "storyboard": package_struct.get("storyboard") or [],
        }
        content = self._call_glm(REVIEW_PACKAGE_PROMPT, payload_context, temperature=0.3)
        parsed = self._parse_json_dict(content)
        return _normalize_review_result(parsed)

    def _refine_package(
        self,
        prompt: str,
        base_struct: dict,
        user_feedback: str | None,
        review_feedback: dict | None,
    ) -> dict:
        review_feedback = review_feedback or {}
        base_summary = base_struct.get("summary") or ""
        base_keywords = base_struct.get("keywords") if isinstance(base_struct.get("keywords"), list) else []
        base_art_style = base_struct.get("art_style") if isinstance(base_struct.get("art_style"), dict) else {}
        base_subjects = base_struct.get("subjects") if isinstance(base_struct.get("subjects"), list) else []
        base_scenes = base_struct.get("scenes") if isinstance(base_struct.get("scenes"), list) else []
        base_storyboard = base_struct.get("storyboard") if isinstance(base_struct.get("storyboard"), list) else []

        summary, keywords = self._refine_summary(
            prompt,
            base_summary,
            base_keywords,
            review_feedback.get("summary") or user_feedback,
        )
        art_style = self._refine_art_style(
            prompt,
            base_art_style,
            summary,
            keywords,
            review_feedback.get("art_style") or user_feedback,
        )
        subjects = self._refine_subjects(
            prompt,
            base_subjects,
            summary,
            keywords,
            art_style,
            review_feedback.get("subjects") or user_feedback,
        )
        scenes = self._refine_scenes(
            prompt,
            base_scenes,
            summary,
            keywords,
            art_style,
            subjects,
            review_feedback.get("scenes") or user_feedback,
        )
        storyboard = self._refine_storyboard(
            prompt,
            base_storyboard,
            summary,
            keywords,
            art_style,
            scenes,
            subjects,
            review_feedback.get("storyboard") or user_feedback,
        )
        return {
            "summary": summary,
            "keywords": keywords,
            "art_style": art_style,
            "subjects": subjects,
            "scenes": scenes,
            "storyboard": storyboard,
        }

    def generate_material_package(
        self,
        prompt: str,
        mode: str,
        previous_package: dict | None = None,
        feedback: str | None = None,
        documents: list | None = None,
    ) -> dict:
        provider = normalize_provider(self._provider)
        if provider != "glm":
            logger.error(
                "LLM provider is not configured for material package generation"
            )
            raise RuntimeError("LLM provider not configured")
        base_struct = self._generate_base_package(
            prompt,
            mode,
            previous_package,
            feedback,
            documents,
        )
        refined_struct = self._refine_package(prompt, base_struct, feedback, None)
        for attempt in range(MAX_REVIEW_ATTEMPTS):
            passed, review_feedback = self._review_package(prompt, refined_struct)
            if passed:
                return refined_struct
            logger.info(
                "llm.review attempt=%s passed=%s",
                attempt + 1,
                passed,
            )
            refined_struct = self._refine_package(prompt, base_struct, feedback, review_feedback)
        logger.warning("LLM review failed after %s attempts; falling back to base package", MAX_REVIEW_ATTEMPTS)
        return base_struct

    def _mock_output(self, prompt: str) -> dict:
        fallback = (prompt or "").strip() or "Demo content"
        return _coerce_structured_output({}, fallback)

    def _extract_json(self, content: str) -> str:
        start = content.find("{")
        end = content.rfind("}")
        if start == -1 or end == -1 or end <= start:
            return ""
        return content[start : end + 1]

    def _parse_json_dict(self, content: str) -> dict:
        for candidate in (content, self._extract_json(content)):
            if not candidate:
                continue
            try:
                parsed = json.loads(candidate)
                if isinstance(parsed, dict):
                    return parsed
            except json.JSONDecodeError:
                continue
        return {}

    def _parse_structured_output(self, content: str, fallback_text: str) -> dict:
        parsed = None
        for candidate in (content, self._extract_json(content)):
            if not candidate:
                continue
            try:
                parsed = json.loads(candidate)
                break
            except json.JSONDecodeError:
                continue
        if not isinstance(parsed, dict):
            return self._mock_output(fallback_text)
        return _coerce_structured_output(parsed, fallback_text)

    def _generate_glm(self, prompt: str) -> dict:
        api_key = settings.glm_api_key
        model = settings.glm_model
        if not api_key or not model:
            logger.error(
                "GLM provider selected but GLM_API_KEY or GLM_MODEL is missing"
            )
            return self._mock_output(prompt)

        user_input = (prompt or "").strip() or "No user input provided."
        payload = {
            "model": model,
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_input},
            ],
            "temperature": 0.7,
        }

        req = request.Request(
            GLM_ENDPOINT,
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {api_key}",
            },
            method="POST",
        )

        try:
            with request.urlopen(req, timeout=180) as response:
                response_text = response.read().decode("utf-8")
        except error.HTTPError as exc:
            logger.error("GLM API error: status=%s reason=%s", exc.code, exc.reason)
            return self._mock_output(prompt)
        except Exception:
            logger.exception("GLM API request failed")
            return self._mock_output(prompt)

        try:
            data = json.loads(response_text)
        except json.JSONDecodeError:
            logger.error("GLM API response was not valid JSON")
            return self._mock_output(prompt)

        choices = data.get("choices") or []
        message = choices[0].get("message", {}) if choices else {}
        content = message.get("content") if isinstance(message, dict) else None
        if not content:
            logger.error("GLM API response missing content")
            return self._mock_output(prompt)
        return self._parse_structured_output(content.strip(), user_input)

    def rewrite_prompt(
        self, original_prompt: str, feedback: str, prompt_parts: dict | None = None
    ) -> str:
        provider = normalize_provider(self._provider)
        if not provider or provider == "mock":
            return self._mock_rewrite(original_prompt, feedback)
        if provider == "glm":
            return self._rewrite_glm(original_prompt, feedback, prompt_parts)
        logger.warning("LLM provider %s not implemented; using mock rewrite", provider)
        return self._mock_rewrite(original_prompt, feedback)

    def _mock_rewrite(self, original_prompt: str, feedback: str) -> str:
        base = (original_prompt or "").strip()
        note = (feedback or "").strip()
        if not base:
            return note
        if not note:
            return base
        return f"{base}\n\nUser feedback: {note}"

    def _rewrite_glm(
        self, original_prompt: str, feedback: str, prompt_parts: dict | None
    ) -> str:
        api_key = settings.glm_api_key
        model = settings.glm_model
        if not api_key or not model:
            logger.error(
                "GLM provider selected but GLM_API_KEY or GLM_MODEL is missing"
            )
            return self._mock_rewrite(original_prompt, feedback)

        payload_context = {
            "original_prompt": (original_prompt or "").strip(),
            "feedback": (feedback or "").strip(),
        }
        if isinstance(prompt_parts, dict):
            payload_context["prompt_parts"] = {
                "content": (prompt_parts.get("content") or "").strip(),
                "style": (prompt_parts.get("style") or "").strip(),
                "constraints": (prompt_parts.get("constraints") or "").strip(),
            }

        req = request.Request(
            GLM_ENDPOINT,
            data=json.dumps(
                {
                    "model": model,
                    "messages": [
                        {"role": "system", "content": REWRITE_PROMPT},
                        {
                            "role": "user",
                            "content": json.dumps(payload_context, ensure_ascii=True),
                        },
                    ],
                    "temperature": 0.4,
                }
            ).encode("utf-8"),
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {api_key}",
            },
            method="POST",
        )

        try:
            with request.urlopen(req, timeout=180) as response:
                response_text = response.read().decode("utf-8")
        except error.HTTPError as exc:
            logger.error("GLM API error: status=%s reason=%s", exc.code, exc.reason)
            return self._mock_rewrite(original_prompt, feedback)
        except Exception:
            logger.exception("GLM API request failed")
            return self._mock_rewrite(original_prompt, feedback)

        try:
            data = json.loads(response_text)
        except json.JSONDecodeError:
            logger.error("GLM API response was not valid JSON")
            return self._mock_rewrite(original_prompt, feedback)

        choices = data.get("choices") or []
        message = choices[0].get("message", {}) if choices else {}
        content = message.get("content") if isinstance(message, dict) else None
        rewritten = (content or "").strip()
        return rewritten or self._mock_rewrite(original_prompt, feedback)

    def rewrite_art_style(self, current_style: dict, feedback: str) -> dict:
        provider = normalize_provider(self._provider)
        if not provider or provider == "mock":
            return self._mock_rewrite_art_style(current_style, feedback)
        if provider == "glm":
            return self._rewrite_art_style_glm(current_style, feedback)
        logger.warning("LLM provider %s not implemented; using mock rewrite", provider)
        return self._mock_rewrite_art_style(current_style, feedback)

    def rewrite_storyboard_description(
        self, current_description: str, feedback: str
    ) -> str:
        provider = normalize_provider(self._provider)
        if not provider or provider == "mock":
            return self._mock_rewrite_storyboard(current_description, feedback)
        if provider == "glm":
            return self._rewrite_storyboard_glm(current_description, feedback)
        logger.warning("LLM provider %s not implemented; using mock rewrite", provider)
        return self._mock_rewrite_storyboard(current_description, feedback)

    def _mock_rewrite_art_style(self, current_style: dict, feedback: str) -> dict:
        style = _normalize_art_style(current_style or {})
        note = (feedback or "").strip()
        if note:
            prompt = style.get("style_prompt") or ""
            style["style_prompt"] = f"{prompt}\n\nUser feedback: {note}".strip()
        return style

    def _mock_rewrite_storyboard(self, current_description: str, feedback: str) -> str:
        base = (current_description or "").strip()
        note = (feedback or "").strip()
        if not base:
            return note
        if not note:
            return base
        return f"{base}\n\nUser feedback: {note}"

    def _rewrite_art_style_glm(self, current_style: dict, feedback: str) -> dict:
        api_key = settings.glm_api_key
        model = settings.glm_model
        if not api_key or not model:
            logger.error(
                "GLM provider selected but GLM_API_KEY or GLM_MODEL is missing"
            )
            return self._mock_rewrite_art_style(current_style, feedback)

        payload_context = {
            "current_style": _normalize_art_style(current_style or {}),
            "feedback": (feedback or "").strip(),
        }
        content = self._call_glm(
            ART_STYLE_REWRITE_PROMPT, payload_context, temperature=0.4
        )
        if not content:
            return _normalize_art_style(current_style or {})
        parsed = self._parse_json_dict(content)
        if not parsed:
            return _normalize_art_style(current_style or {})
        rewritten = _normalize_art_style(parsed)
        if not rewritten.get("style_prompt") and not rewritten.get("style_name"):
            return _normalize_art_style(current_style or {})
        return rewritten

    def _rewrite_storyboard_glm(self, current_description: str, feedback: str) -> str:
        api_key = settings.glm_api_key
        model = settings.glm_model
        if not api_key or not model:
            logger.error(
                "GLM provider selected but GLM_API_KEY or GLM_MODEL is missing"
            )
            return self._mock_rewrite_storyboard(current_description, feedback)

        payload_context = {
            "current_description": (current_description or "").strip(),
            "feedback": (feedback or "").strip(),
        }
        content = self._call_glm(
            STORYBOARD_REWRITE_PROMPT, payload_context, temperature=0.4
        )
        parsed = self._parse_json_dict(content)
        description = _normalize_text(parsed.get("description"), "")
        return description or self._mock_rewrite_storyboard(
            current_description, feedback
        )

    def _call_glm(
        self, system_prompt: str, payload_context: dict, temperature: float = 0.4
    ) -> str:
        api_key = settings.glm_api_key
        model = settings.glm_model
        if not api_key or not model:
            return ""
        logger.info(
            "llm.request provider=glm model=%s temperature=%.2f payload_keys=%s",
            model,
            temperature,
            ",".join(sorted(payload_context.keys())),
        )

        req = request.Request(
            GLM_ENDPOINT,
            data=json.dumps(
                {
                    "model": model,
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {
                            "role": "user",
                            "content": json.dumps(payload_context, ensure_ascii=True),
                        },
                    ],
                    "temperature": temperature,
                }
            ).encode("utf-8"),
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {api_key}",
            },
            method="POST",
        )

        try:
            with request.urlopen(req, timeout=180) as response:
                response_text = response.read().decode("utf-8")
        except error.HTTPError as exc:
            logger.error("GLM API error: status=%s reason=%s", exc.code, exc.reason)
            return ""
        except Exception:
            logger.exception("GLM API request failed")
            return ""

        try:
            data = json.loads(response_text)
        except json.JSONDecodeError:
            logger.error("GLM API response was not valid JSON")
            return ""

        choices = data.get("choices") or []
        message = choices[0].get("message", {}) if choices else {}
        content = message.get("content") if isinstance(message, dict) else None
        return (content or "").strip()

    def rewrite_blueprint(
        self, previous_blueprint: dict, feedback: str, source_prompt: str
    ) -> dict:
        provider = normalize_provider(self._provider)
        if provider != "glm":
            logger.error("LLM provider is not configured for blueprint rewrite")
            raise RuntimeError("LLM provider not configured")
        payload_context = {
            "previous_blueprint": previous_blueprint or {},
            "feedback": (feedback or "").strip(),
            "source_prompt": (source_prompt or "").strip(),
        }
        content = self._call_glm(
            BLUEPRINT_REWRITE_PROMPT, payload_context, temperature=0.5
        )
        parsed = self._parse_json_dict(content)
        normalized = _normalize_material_package_struct(parsed)
        valid, reason = _validate_material_package_struct(normalized)
        if not valid:
            logger.error("LLM output invalid for blueprint rewrite: %s", reason)
            raise ValueError(f"Invalid LLM output: {reason}")
        return normalized

    def generate_package_name(self, source_prompt: str, summary: str) -> str:
        provider = normalize_provider(self._provider)
        if provider != "glm":
            logger.error("LLM provider is not configured for package naming")
            raise RuntimeError("LLM provider not configured")
        payload_context = {
            "source_prompt": (source_prompt or "").strip(),
            "summary": (summary or "").strip(),
        }
        content = self._call_glm(PACKAGE_NAME_PROMPT, payload_context, temperature=0.4)
        parsed = self._parse_json_dict(content)
        name = _normalize_text(parsed.get("name"), "")
        if not name:
            logger.error("LLM output invalid for package naming")
            raise ValueError("Invalid LLM output: name missing")
        return name[:10]
