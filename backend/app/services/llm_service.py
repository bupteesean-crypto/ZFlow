import json
import logging
import time
from pathlib import Path
from typing import Callable
from urllib import error, request

from app.core.config import normalize_provider, settings

logger = logging.getLogger(__name__)

GLM_ENDPOINT_PATH = "/api/paas/v4/chat/completions"
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
SUMMARY_REWRITE_PATH = (
    Path(__file__).resolve().parents[1] / "prompts" / "summary_rewrite_v1.md"
)
SUBJECT_REWRITE_PATH = (
    Path(__file__).resolve().parents[1] / "prompts" / "subject_rewrite_v1.md"
)
SCENE_REWRITE_PATH = (
    Path(__file__).resolve().parents[1] / "prompts" / "scene_rewrite_v1.md"
)
BLUEPRINT_REWRITE_PATH = (
    Path(__file__).resolve().parents[1] / "prompts" / "blueprint_rewrite_v1.md"
)
PACKAGE_NAME_PATH = (
    Path(__file__).resolve().parents[1] / "prompts" / "package_name_v1.md"
)
SUMMARY_PROMPT_PATH = Path(__file__).resolve().parents[1] / "prompts" / "generate_summary_v1.md"
ART_STYLE_PROMPT_PATH = Path(__file__).resolve().parents[1] / "prompts" / "generate_art_style_v1.md"
CHARACTERS_PROMPT_PATH = Path(__file__).resolve().parents[1] / "prompts" / "generate_characters_v1.md"
SCENES_PROMPT_PATH = Path(__file__).resolve().parents[1] / "prompts" / "generate_scenes_v1.md"
STORYBOARD_PROMPT_PATH = Path(__file__).resolve().parents[1] / "prompts" / "generate_storyboard_v1.md"
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
DEFAULT_SUMMARY_REWRITE_PROMPT = (
    "You are a prompt rewrite assistant for summary edits. "
    "Given the current summary and user feedback, rewrite the FULL summary. "
    "Output JSON only with key: summary (Chinese output required). "
    "Apply feedback directly. Preserve details not requested to change. "
    "No Markdown, no extra text."
)
DEFAULT_SUBJECT_REWRITE_PROMPT = (
    "You are a prompt rewrite assistant for character edits. "
    "Given the current subject and user feedback, rewrite the FULL subject. "
    "Output JSON only with keys: name, role, description, visual_traits (Chinese output required). "
    "Apply feedback directly. Preserve details not requested to change. "
    "No Markdown, no extra text."
)
DEFAULT_SCENE_REWRITE_PROMPT = (
    "You are a prompt rewrite assistant for scene edits. "
    "Given the current scene and user feedback, rewrite the FULL scene. "
    "Output JSON only with keys: name, description, mood, purpose (Chinese output required). "
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
DEFAULT_SUMMARY_PROMPT = (
    "Return JSON only with key summary."
)
DEFAULT_ART_STYLE_PROMPT = (
    "Return JSON only with key art_style containing style_name, style_prompt, palette."
)
DEFAULT_CHARACTERS_PROMPT = "Return JSON only with key subjects."
DEFAULT_SCENES_PROMPT = "Return JSON only with key scenes."
DEFAULT_STORYBOARD_PROMPT = "Return JSON only with key storyboard."

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


def _normalize_subject_value(value: object) -> dict:
    if not isinstance(value, dict):
        return {"name": "", "description": "", "role": "", "visual_traits": []}
    name = _normalize_text(value.get("name"), "")
    description = _normalize_text(value.get("description"), "")
    role = _normalize_text(value.get("role"), "")
    traits = value.get("visual_traits") if isinstance(value.get("visual_traits"), list) else []
    traits = [str(trait).strip() for trait in traits if str(trait).strip()]
    return {"name": name, "description": description, "role": role, "visual_traits": traits}


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


def _normalize_scene_value(value: object) -> dict:
    if not isinstance(value, dict):
        return {"name": "", "description": "", "mood": "", "purpose": ""}
    name = _normalize_text(value.get("name"), "")
    description = _normalize_text(value.get("description"), "")
    mood = _normalize_text(value.get("mood"), "")
    purpose = _normalize_text(value.get("purpose"), "")
    return {
        "name": name,
        "description": description,
        "mood": mood,
        "purpose": purpose,
    }


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


def _load_stage_prompt(path: Path, fallback: str, label: str) -> str:
    try:
        return path.read_text(encoding="utf-8").strip() or fallback
    except OSError:
        logger.warning("Failed to read %s prompt at %s; using default prompt", label, path)
        return fallback


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


def _load_summary_rewrite_prompt() -> str:
    try:
        return (
            SUMMARY_REWRITE_PATH.read_text(encoding="utf-8").strip()
            or DEFAULT_SUMMARY_REWRITE_PROMPT
        )
    except OSError:
        logger.warning(
            "Failed to read summary prompt at %s; using default prompt",
            SUMMARY_REWRITE_PATH,
        )
        return DEFAULT_SUMMARY_REWRITE_PROMPT


def _load_subject_rewrite_prompt() -> str:
    try:
        return (
            SUBJECT_REWRITE_PATH.read_text(encoding="utf-8").strip()
            or DEFAULT_SUBJECT_REWRITE_PROMPT
        )
    except OSError:
        logger.warning(
            "Failed to read subject prompt at %s; using default prompt",
            SUBJECT_REWRITE_PATH,
        )
        return DEFAULT_SUBJECT_REWRITE_PROMPT


def _load_scene_rewrite_prompt() -> str:
    try:
        return (
            SCENE_REWRITE_PATH.read_text(encoding="utf-8").strip()
            or DEFAULT_SCENE_REWRITE_PROMPT
        )
    except OSError:
        logger.warning(
            "Failed to read scene prompt at %s; using default prompt",
            SCENE_REWRITE_PATH,
        )
        return DEFAULT_SCENE_REWRITE_PROMPT


ART_STYLE_REWRITE_PROMPT = _load_art_style_prompt()
STORYBOARD_REWRITE_PROMPT = _load_storyboard_prompt()
SUMMARY_REWRITE_PROMPT = _load_summary_rewrite_prompt()
SUBJECT_REWRITE_PROMPT = _load_subject_rewrite_prompt()
SCENE_REWRITE_PROMPT = _load_scene_rewrite_prompt()


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

SUMMARY_PROMPT = _load_stage_prompt(SUMMARY_PROMPT_PATH, DEFAULT_SUMMARY_PROMPT, "summary")
ART_STYLE_PROMPT = _load_stage_prompt(ART_STYLE_PROMPT_PATH, DEFAULT_ART_STYLE_PROMPT, "art style")
CHARACTERS_PROMPT = _load_stage_prompt(CHARACTERS_PROMPT_PATH, DEFAULT_CHARACTERS_PROMPT, "characters")
SCENES_PROMPT = _load_stage_prompt(SCENES_PROMPT_PATH, DEFAULT_SCENES_PROMPT, "scenes")
STORYBOARD_PROMPT = _load_stage_prompt(STORYBOARD_PROMPT_PATH, DEFAULT_STORYBOARD_PROMPT, "storyboard")


class LLMService:
    def __init__(
        self,
        api_key: str | None = None,
        api_base: str | None = None,
        allow_env_fallback: bool = True,
    ) -> None:
        self._provider = settings.llm_provider
        self._last_error: str | None = None
        self._api_key = api_key.strip() if isinstance(api_key, str) and api_key.strip() else None
        self._api_base = api_base.strip().rstrip("/") if isinstance(api_base, str) and api_base.strip() else None
        self._allow_env_fallback = allow_env_fallback

    def _resolve_glm_api_key(self) -> str:
        if self._api_key:
            return self._api_key
        if self._allow_env_fallback:
            return settings.glm_api_key
        return ""

    def _resolve_glm_endpoint(self) -> str:
        base = self._api_base or settings.glm_api_base or "https://open.bigmodel.cn"
        base = base.strip().rstrip("/")
        if base.endswith("/chat/completions"):
            return base
        if base.endswith("/api/paas/v4"):
            return f"{base}/chat/completions"
        return f"{base}{GLM_ENDPOINT_PATH}"

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

    def _build_stage_prompt(self, base_prompt: str, mode: str) -> tuple[str, float]:
        normalized_mode = _normalize_generation_mode(mode)
        if normalized_mode == "pro":
            return f"{base_prompt}\n\n{PRO_MODE_BLOCK}", 0.4
        return f"{base_prompt}\n\n{GENERAL_MODE_BLOCK}", 0.6

    def generate_summary(
        self,
        prompt: str,
        mode: str,
        documents: list | None = None,
        input_config: dict | None = None,
        feedback: str | None = None,
        previous_summary: str | None = None,
        on_delta: Callable[[str, str], None] | None = None,
    ) -> tuple[str, list[str]]:
        provider = normalize_provider(self._provider)
        if provider != "glm":
            logger.error("LLM provider is not configured for summary generation")
            raise RuntimeError("LLM provider not configured")
        system_prompt, temperature = self._build_stage_prompt(SUMMARY_PROMPT, mode)
        payload_context = {
            "mode": _normalize_generation_mode(mode),
            "user_prompt": (prompt or "").strip(),
            "summary": (previous_summary or "").strip(),
            "feedback": (feedback or "").strip(),
            "documents": documents or [],
            "input_config": input_config or {},
        }
        if on_delta:
            result = self._call_glm_stream(system_prompt, payload_context, temperature=temperature, on_delta=on_delta)
            content = result.get("content") or ""
        else:
            content = self._call_glm(system_prompt, payload_context, temperature=temperature)
        if not content and self._last_error == "rate_limited":
            raise RuntimeError("LLM rate limited")
        parsed = self._parse_json_dict(content)
        summary = _normalize_text(parsed.get("summary"), "")
        keywords = _normalize_keywords(parsed.get("keywords"))
        if not summary:
            logger.error("LLM output invalid for summary generation")
            raise ValueError("Invalid LLM output: summary missing")
        return summary, keywords

    def generate_art_style(
        self,
        summary: str,
        prompt: str,
        mode: str,
        documents: list | None = None,
        input_config: dict | None = None,
        feedback: str | None = None,
        previous_art_style: dict | None = None,
        on_delta: Callable[[str, str], None] | None = None,
    ) -> dict:
        provider = normalize_provider(self._provider)
        if provider != "glm":
            logger.error("LLM provider is not configured for art style generation")
            raise RuntimeError("LLM provider not configured")
        system_prompt, temperature = self._build_stage_prompt(ART_STYLE_PROMPT, mode)
        payload_context = {
            "mode": _normalize_generation_mode(mode),
            "user_prompt": (prompt or "").strip(),
            "summary": (summary or "").strip(),
            "previous_art_style": _normalize_art_style(previous_art_style or {}),
            "feedback": (feedback or "").strip(),
            "documents": documents or [],
            "input_config": input_config or {},
        }
        if on_delta:
            result = self._call_glm_stream(system_prompt, payload_context, temperature=temperature, on_delta=on_delta)
            content = result.get("content") or ""
        else:
            content = self._call_glm(system_prompt, payload_context, temperature=temperature)
        if not content and self._last_error == "rate_limited":
            raise RuntimeError("LLM rate limited")
        parsed = self._parse_json_dict(content)
        art_style = parsed.get("art_style") if isinstance(parsed.get("art_style"), dict) else parsed
        normalized = _normalize_art_style(art_style)
        if not _normalize_text(normalized.get("style_name"), "") and not _normalize_text(
            normalized.get("style_prompt"), ""
        ):
            logger.error("LLM output invalid for art style generation")
            raise ValueError("Invalid LLM output: art_style missing")
        return normalized

    def generate_characters(
        self,
        summary: str,
        art_style: dict,
        prompt: str,
        mode: str,
        documents: list | None = None,
        input_config: dict | None = None,
        feedback: str | None = None,
        previous_subjects: list | None = None,
        on_delta: Callable[[str, str], None] | None = None,
    ) -> list[dict]:
        provider = normalize_provider(self._provider)
        if provider != "glm":
            logger.error("LLM provider is not configured for character generation")
            raise RuntimeError("LLM provider not configured")
        system_prompt, temperature = self._build_stage_prompt(CHARACTERS_PROMPT, mode)
        payload_context = {
            "mode": _normalize_generation_mode(mode),
            "user_prompt": (prompt or "").strip(),
            "summary": (summary or "").strip(),
            "art_style": _normalize_art_style(art_style or {}),
            "previous_subjects": previous_subjects or [],
            "feedback": (feedback or "").strip(),
            "documents": documents or [],
            "input_config": input_config or {},
        }
        if on_delta:
            result = self._call_glm_stream(system_prompt, payload_context, temperature=temperature, on_delta=on_delta)
            content = result.get("content") or ""
        else:
            content = self._call_glm(system_prompt, payload_context, temperature=temperature)
        if not content and self._last_error == "rate_limited":
            raise RuntimeError("LLM rate limited")
        parsed = self._parse_json_dict(content)
        subjects = parsed.get("subjects") if isinstance(parsed.get("subjects"), list) else parsed
        normalized = _normalize_subjects(subjects, summary)
        if not normalized:
            logger.error("LLM output invalid for character generation")
            raise ValueError("Invalid LLM output: subjects missing")
        return normalized

    def generate_scenes(
        self,
        summary: str,
        art_style: dict,
        subjects: list[dict],
        prompt: str,
        mode: str,
        documents: list | None = None,
        input_config: dict | None = None,
        feedback: str | None = None,
        previous_scenes: list | None = None,
        on_delta: Callable[[str, str], None] | None = None,
    ) -> list[dict]:
        provider = normalize_provider(self._provider)
        if provider != "glm":
            logger.error("LLM provider is not configured for scene generation")
            raise RuntimeError("LLM provider not configured")
        system_prompt, temperature = self._build_stage_prompt(SCENES_PROMPT, mode)
        payload_context = {
            "mode": _normalize_generation_mode(mode),
            "user_prompt": (prompt or "").strip(),
            "summary": (summary or "").strip(),
            "art_style": _normalize_art_style(art_style or {}),
            "subjects": subjects or [],
            "previous_scenes": previous_scenes or [],
            "feedback": (feedback or "").strip(),
            "documents": documents or [],
            "input_config": input_config or {},
        }
        if on_delta:
            result = self._call_glm_stream(system_prompt, payload_context, temperature=temperature, on_delta=on_delta)
            content = result.get("content") or ""
        else:
            content = self._call_glm(system_prompt, payload_context, temperature=temperature)
        if not content and self._last_error == "rate_limited":
            raise RuntimeError("LLM rate limited")
        parsed = self._parse_json_dict(content)
        scenes = parsed.get("scenes") if isinstance(parsed.get("scenes"), list) else parsed
        normalized = _normalize_scenes(scenes, summary)
        if not normalized:
            logger.error("LLM output invalid for scene generation")
            raise ValueError("Invalid LLM output: scenes missing")
        return normalized

    def generate_storyboard(
        self,
        summary: str,
        art_style: dict,
        subjects: list[dict],
        scenes: list[dict],
        prompt: str,
        mode: str,
        documents: list | None = None,
        input_config: dict | None = None,
        feedback: str | None = None,
        previous_storyboard: list | None = None,
        on_delta: Callable[[str, str], None] | None = None,
    ) -> list[dict]:
        provider = normalize_provider(self._provider)
        if provider != "glm":
            logger.error("LLM provider is not configured for storyboard generation")
            raise RuntimeError("LLM provider not configured")
        system_prompt, temperature = self._build_stage_prompt(STORYBOARD_PROMPT, mode)
        payload_context = {
            "mode": _normalize_generation_mode(mode),
            "user_prompt": (prompt or "").strip(),
            "summary": (summary or "").strip(),
            "art_style": _normalize_art_style(art_style or {}),
            "subjects": subjects or [],
            "scenes": scenes or [],
            "previous_storyboard": previous_storyboard or [],
            "feedback": (feedback or "").strip(),
            "documents": documents or [],
            "input_config": input_config or {},
        }
        if on_delta:
            result = self._call_glm_stream(system_prompt, payload_context, temperature=temperature, on_delta=on_delta)
            content = result.get("content") or ""
        else:
            content = self._call_glm(system_prompt, payload_context, temperature=temperature)
        if not content and self._last_error == "rate_limited":
            raise RuntimeError("LLM rate limited")
        parsed = self._parse_json_dict(content)
        storyboard = parsed.get("storyboard") if isinstance(parsed.get("storyboard"), list) else parsed
        normalized = _normalize_storyboard(storyboard, summary)
        if not normalized:
            logger.error("LLM output invalid for storyboard generation")
            raise ValueError("Invalid LLM output: storyboard missing")
        return normalized

    def generate_material_package(
        self,
        prompt: str,
        mode: str,
        previous_package: dict | None = None,
        feedback: str | None = None,
        documents: list | None = None,
        input_config: dict | None = None,
    ) -> dict:
        provider = normalize_provider(self._provider)
        if provider != "glm":
            logger.error(
                "LLM provider is not configured for material package generation"
            )
            raise RuntimeError("LLM provider not configured")
        previous_summary = _normalize_text(previous_package.get("summary"), "") if isinstance(previous_package, dict) else ""
        previous_art_style = previous_package.get("art_style") if isinstance(previous_package, dict) else {}
        previous_subjects = previous_package.get("subjects") if isinstance(previous_package, dict) else []
        previous_scenes = previous_package.get("scenes") if isinstance(previous_package, dict) else []
        previous_storyboard = previous_package.get("storyboard") if isinstance(previous_package, dict) else []

        summary, keywords = self.generate_summary(
            prompt,
            mode,
            documents=documents,
            input_config=input_config,
            feedback=feedback,
            previous_summary=previous_summary,
        )
        art_style = self.generate_art_style(
            summary,
            prompt,
            mode,
            documents=documents,
            input_config=input_config,
            feedback=feedback,
            previous_art_style=previous_art_style if isinstance(previous_art_style, dict) else {},
        )
        subjects = self.generate_characters(
            summary,
            art_style,
            prompt,
            mode,
            documents=documents,
            input_config=input_config,
            feedback=feedback,
            previous_subjects=previous_subjects if isinstance(previous_subjects, list) else [],
        )
        scenes = self.generate_scenes(
            summary,
            art_style,
            subjects,
            prompt,
            mode,
            documents=documents,
            input_config=input_config,
            feedback=feedback,
            previous_scenes=previous_scenes if isinstance(previous_scenes, list) else [],
        )
        storyboard = self.generate_storyboard(
            summary,
            art_style,
            subjects,
            scenes,
            prompt,
            mode,
            documents=documents,
            input_config=input_config,
            feedback=feedback,
            previous_storyboard=previous_storyboard if isinstance(previous_storyboard, list) else [],
        )
        return {
            "summary": summary,
            "keywords": keywords,
            "art_style": art_style,
            "subjects": subjects,
            "scenes": scenes,
            "storyboard": storyboard,
        }

    def stream_material_package(
        self,
        prompt: str,
        mode: str,
        documents: list | None = None,
        input_config: dict | None = None,
        on_delta: Callable[[str, str], None] | None = None,
    ) -> dict:
        provider = normalize_provider(self._provider)
        if provider != "glm":
            logger.error("LLM provider is not configured for streaming generation")
            raise RuntimeError("LLM provider not configured")
        system_prompt, temperature = self._build_stage_prompt(SYSTEM_PROMPT, mode)
        payload_context = {
            "mode": _normalize_generation_mode(mode),
            "user_prompt": (prompt or "").strip(),
            "source_prompt": (prompt or "").strip(),
            "documents": documents or [],
            "input_config": input_config or {},
        }
        return self._call_glm_stream(system_prompt, payload_context, temperature, on_delta)

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
        api_key = self._resolve_glm_api_key()
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
            self._resolve_glm_endpoint(),
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

    def rewrite_summary(self, current_summary: str, feedback: str) -> str:
        provider = normalize_provider(self._provider)
        if not provider or provider == "mock":
            return self._mock_rewrite_summary(current_summary, feedback)
        if provider == "glm":
            return self._rewrite_summary_glm(current_summary, feedback)
        logger.warning("LLM provider %s not implemented; using mock rewrite", provider)
        return self._mock_rewrite_summary(current_summary, feedback)

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
        api_key = self._resolve_glm_api_key()
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
            self._resolve_glm_endpoint(),
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

    def _mock_rewrite_summary(self, current_summary: str, feedback: str) -> str:
        base = (current_summary or "").strip()
        note = (feedback or "").strip()
        if not base:
            return note
        if not note:
            return base
        return f"{base}\n\nUser feedback: {note}"

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

    def rewrite_subject(self, current_subject: dict, feedback: str) -> dict:
        provider = normalize_provider(self._provider)
        if not provider or provider == "mock":
            return self._mock_rewrite_subject(current_subject, feedback)
        if provider == "glm":
            return self._rewrite_subject_glm(current_subject, feedback)
        logger.warning("LLM provider %s not implemented; using mock rewrite", provider)
        return self._mock_rewrite_subject(current_subject, feedback)

    def rewrite_scene(self, current_scene: dict, feedback: str) -> dict:
        provider = normalize_provider(self._provider)
        if not provider or provider == "mock":
            return self._mock_rewrite_scene(current_scene, feedback)
        if provider == "glm":
            return self._rewrite_scene_glm(current_scene, feedback)
        logger.warning("LLM provider %s not implemented; using mock rewrite", provider)
        return self._mock_rewrite_scene(current_scene, feedback)

    def _mock_rewrite_art_style(self, current_style: dict, feedback: str) -> dict:
        style = _normalize_art_style(current_style or {})
        note = (feedback or "").strip()
        if note:
            prompt = style.get("style_prompt") or ""
            style["style_prompt"] = f"{prompt}\n\nUser feedback: {note}".strip()
        return style

    def _mock_rewrite_subject(self, current_subject: dict, feedback: str) -> dict:
        subject = _normalize_subject_value(current_subject or {})
        note = (feedback or "").strip()
        if note:
            description = subject.get("description") or ""
            subject["description"] = f"{description}\n\nUser feedback: {note}".strip()
        return subject

    def _mock_rewrite_scene(self, current_scene: dict, feedback: str) -> dict:
        scene = _normalize_scene_value(current_scene or {})
        note = (feedback or "").strip()
        if note:
            description = scene.get("description") or ""
            scene["description"] = f"{description}\n\nUser feedback: {note}".strip()
        return scene

    def _mock_rewrite_storyboard(self, current_description: str, feedback: str) -> str:
        base = (current_description or "").strip()
        note = (feedback or "").strip()
        if not base:
            return note
        if not note:
            return base
        return f"{base}\n\nUser feedback: {note}"

    def _rewrite_art_style_glm(self, current_style: dict, feedback: str) -> dict:
        api_key = self._resolve_glm_api_key()
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
        api_key = self._resolve_glm_api_key()
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

    def _rewrite_summary_glm(self, current_summary: str, feedback: str) -> str:
        api_key = self._resolve_glm_api_key()
        model = settings.glm_model
        if not api_key or not model:
            logger.error(
                "GLM provider selected but GLM_API_KEY or GLM_MODEL is missing"
            )
            return self._mock_rewrite_summary(current_summary, feedback)

        payload_context = {
            "current_summary": (current_summary or "").strip(),
            "feedback": (feedback or "").strip(),
        }
        content = self._call_glm(
            SUMMARY_REWRITE_PROMPT, payload_context, temperature=0.4
        )
        parsed = self._parse_json_dict(content)
        summary = _normalize_text(parsed.get("summary"), "")
        return summary or self._mock_rewrite_summary(current_summary, feedback)

    def _rewrite_subject_glm(self, current_subject: dict, feedback: str) -> dict:
        api_key = self._resolve_glm_api_key()
        model = settings.glm_model
        if not api_key or not model:
            logger.error(
                "GLM provider selected but GLM_API_KEY or GLM_MODEL is missing"
            )
            return self._mock_rewrite_subject(current_subject, feedback)

        payload_context = {
            "current_subject": _normalize_subject_value(current_subject or {}),
            "feedback": (feedback or "").strip(),
        }
        content = self._call_glm(
            SUBJECT_REWRITE_PROMPT, payload_context, temperature=0.4
        )
        parsed = self._parse_json_dict(content)
        rewritten = _normalize_subject_value(parsed)
        if not rewritten.get("name") and not rewritten.get("description"):
            return _normalize_subject_value(current_subject or {})
        return rewritten

    def _rewrite_scene_glm(self, current_scene: dict, feedback: str) -> dict:
        api_key = self._resolve_glm_api_key()
        model = settings.glm_model
        if not api_key or not model:
            logger.error(
                "GLM provider selected but GLM_API_KEY or GLM_MODEL is missing"
            )
            return self._mock_rewrite_scene(current_scene, feedback)

        payload_context = {
            "current_scene": _normalize_scene_value(current_scene or {}),
            "feedback": (feedback or "").strip(),
        }
        content = self._call_glm(
            SCENE_REWRITE_PROMPT, payload_context, temperature=0.4
        )
        parsed = self._parse_json_dict(content)
        rewritten = _normalize_scene_value(parsed)
        if not rewritten.get("name") and not rewritten.get("description"):
            return _normalize_scene_value(current_scene or {})
        return rewritten

    def _call_glm(
        self, system_prompt: str, payload_context: dict, temperature: float = 0.4
    ) -> str:
        api_key = self._resolve_glm_api_key()
        model = settings.glm_model
        if not api_key or not model:
            return ""
        self._last_error = None
        logger.info(
            "llm.request provider=glm model=%s temperature=%.2f payload_keys=%s",
            model,
            temperature,
            ",".join(sorted(payload_context.keys())),
        )

        req = request.Request(
            self._resolve_glm_endpoint(),
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

        max_attempts = 5
        backoff_base = 2.0
        response_text = ""
        for attempt in range(max_attempts):
            try:
                with request.urlopen(req, timeout=180) as response:
                    response_text = response.read().decode("utf-8")
                break
            except error.HTTPError as exc:
                logger.error("GLM API error: status=%s reason=%s", exc.code, exc.reason)
                if exc.code == 429:
                    self._last_error = "rate_limited"
                elif exc.code in {500, 502, 503, 504}:
                    self._last_error = "upstream_error"
                should_retry = exc.code in {429, 500, 502, 503, 504} and attempt < max_attempts - 1
                if should_retry:
                    retry_after = None
                    try:
                        retry_after = exc.headers.get("Retry-After")
                    except Exception:
                        retry_after = None
                    delay = None
                    if isinstance(retry_after, str) and retry_after.strip():
                        try:
                            delay = float(retry_after.strip())
                        except ValueError:
                            delay = None
                    if delay is None:
                        delay = backoff_base * (2**attempt)
                    logger.warning("GLM request retrying in %.1fs (attempt %s/%s)", delay, attempt + 1, max_attempts)
                    time.sleep(delay)
                    continue
                return ""
            except Exception:
                logger.exception("GLM API request failed")
                self._last_error = "request_failed"
                if attempt < max_attempts - 1:
                    delay = backoff_base * (2**attempt)
                    logger.warning("GLM request retrying in %.1fs (attempt %s/%s)", delay, attempt + 1, max_attempts)
                    time.sleep(delay)
                    continue
                return ""

        try:
            data = json.loads(response_text)
        except json.JSONDecodeError:
            logger.error("GLM API response was not valid JSON")
            self._last_error = "invalid_response"
            return ""

        choices = data.get("choices") or []
        message = choices[0].get("message", {}) if choices else {}
        content = message.get("content") if isinstance(message, dict) else None
        return (content or "").strip()

    def _call_glm_stream(
        self,
        system_prompt: str,
        payload_context: dict,
        temperature: float,
        on_delta: Callable[[str, str], None] | None,
    ) -> dict:
        api_key = self._resolve_glm_api_key()
        model = settings.glm_model
        if not api_key or not model:
            return {"content": "", "finish_reason": None, "usage": None, "done": False}
        self._last_error = None
        logger.info(
            "llm.request provider=glm model=%s temperature=%.2f payload_keys=%s stream=true",
            model,
            temperature,
            ",".join(sorted(payload_context.keys())),
        )

        payload = {
            "model": model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": json.dumps(payload_context, ensure_ascii=False)},
            ],
            "temperature": temperature,
            "stream": True,
        }

        max_attempts = 5
        backoff_base = 2.0

        for attempt in range(max_attempts):
            content_parts: list[str] = []
            finish_reason = None
            usage = None
            saw_done = False
            emitted = False
            req = request.Request(
                self._resolve_glm_endpoint(),
                data=json.dumps(payload).encode("utf-8"),
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {api_key}",
                },
                method="POST",
            )
            try:
                with request.urlopen(req, timeout=180) as response:
                    for raw_line in response:
                        if not raw_line:
                            continue
                        line = raw_line.decode("utf-8").strip()
                        if not line or not line.startswith("data:"):
                            continue
                        data = line[len("data:") :].strip()
                        if data == "[DONE]":
                            saw_done = True
                            break
                        try:
                            chunk = json.loads(data)
                        except json.JSONDecodeError:
                            continue
                        choices = chunk.get("choices") or []
                        choice = choices[0] if choices else {}
                        delta = choice.get("delta") if isinstance(choice, dict) else {}
                        delta_content = delta.get("content") if isinstance(delta, dict) else ""
                        delta_reasoning = delta.get("reasoning_content") if isinstance(delta, dict) else ""
                        if delta_content:
                            content_parts.append(delta_content)
                        if on_delta and (delta_content or delta_reasoning):
                            emitted = True
                            try:
                                on_delta(delta_content or "", delta_reasoning or "")
                            except Exception:
                                logger.exception("LLM stream delta callback failed")
                        if choice.get("finish_reason"):
                            finish_reason = choice.get("finish_reason")
                        if chunk.get("usage"):
                            usage = chunk.get("usage")
                return {
                    "content": "".join(content_parts),
                    "finish_reason": finish_reason,
                    "usage": usage,
                    "done": saw_done,
                }
            except error.HTTPError as exc:
                logger.error("GLM API error: status=%s reason=%s", exc.code, exc.reason)
                if exc.code == 429:
                    self._last_error = "rate_limited"
                elif exc.code in {500, 502, 503, 504}:
                    self._last_error = "upstream_error"
                if emitted:
                    break
                should_retry = exc.code in {429, 500, 502, 503, 504} and attempt < max_attempts - 1
                if should_retry:
                    retry_after = None
                    try:
                        retry_after = exc.headers.get("Retry-After")
                    except Exception:
                        retry_after = None
                    delay = None
                    if isinstance(retry_after, str) and retry_after.strip():
                        try:
                            delay = float(retry_after.strip())
                        except ValueError:
                            delay = None
                    if delay is None:
                        delay = backoff_base * (2**attempt)
                    logger.warning(
                        "GLM stream retrying in %.1fs (attempt %s/%s)",
                        delay,
                        attempt + 1,
                        max_attempts,
                    )
                    time.sleep(delay)
                    continue
                break
            except Exception:
                logger.exception("GLM API stream request failed")
                self._last_error = "request_failed"
                if emitted:
                    break
                if attempt < max_attempts - 1:
                    delay = backoff_base * (2**attempt)
                    logger.warning(
                        "GLM stream retrying in %.1fs (attempt %s/%s)",
                        delay,
                        attempt + 1,
                        max_attempts,
                    )
                    time.sleep(delay)
                    continue
                break

        return {
            "content": "",
            "finish_reason": None,
            "usage": None,
            "done": False,
        }

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
        if not content and self._last_error == "rate_limited":
            raise RuntimeError("LLM rate limited")
        parsed = self._parse_json_dict(content)
        normalized = _normalize_material_package_struct(parsed)
        valid, reason = _validate_material_package_struct(normalized)
        if not valid:
            logger.error("LLM output invalid for blueprint rewrite: %s", reason)
            raise ValueError(f"Invalid LLM output: {reason}")
        return normalized

    def generate_package_name(self, summary: str, art_style: dict) -> str:
        provider = normalize_provider(self._provider)
        if provider != "glm":
            logger.error("LLM provider is not configured for package naming")
            raise RuntimeError("LLM provider not configured")
        payload_context = {
            "summary": (summary or "").strip(),
            "art_style": _normalize_art_style(art_style or {}),
        }
        content = self._call_glm(PACKAGE_NAME_PROMPT, payload_context, temperature=0.4)
        if not content and self._last_error == "rate_limited":
            raise RuntimeError("LLM rate limited")
        parsed = self._parse_json_dict(content)
        name = _normalize_text(parsed.get("name"), "")
        if not name:
            logger.error("LLM output invalid for package naming")
            raise ValueError("Invalid LLM output: name missing")
        return name[:10]
