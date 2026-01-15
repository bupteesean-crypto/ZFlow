import logging
from datetime import datetime, timezone
from pathlib import Path

import requests

from app.core.config import normalize_provider, settings

logger = logging.getLogger(__name__)
PROMPT_PATH = Path(__file__).resolve().parents[3] / "worker" / "prompts" / "image" / "illustration_v1.txt"
MOCK_IMAGE_URL = "data:image/gif;base64,R0lGODlhAQABAIAAAAAAAP///ywAAAAAAQABAAACAUwAOw=="
MAX_REFERENCE_IMAGES = 10
DEFAULT_PROMPT = (
    "Create a clean, consistent 3:4 portrait illustration suitable for a short video storyboard frame.\n\n"
    "Scene summary: {{scene_summary}}\n"
    "Mood: {{mood}}\n"
    "Keywords: {{keywords}}\n\n"
    "Style:\n"
    "- modern, clear illustration\n"
    "- cohesive color palette\n"
    "- soft contrast, balanced lighting\n"
    "- no photorealism, no heavy textures\n\n"
    "Composition:\n"
    "- single focal subject\n"
    "- readable silhouette\n"
    "- mid-shot, cinematic framing\n"
    "- uncluttered background\n\n"
    "Constraints:\n"
    "- no text, no captions, no logos, no watermark\n"
    "- avoid low-quality artifacts or distortion\n"
    "- avoid extra limbs or malformed anatomy\n"
    "- avoid busy patterns or chaotic layouts\n"
)


class ImageService:
    def __init__(self) -> None:
        self._provider = settings.image_provider
        self._prompt_template = self._load_prompt_template()

    def generate_image(self, prompt: str, size: str | None = None) -> dict:
        provider = normalize_provider(self._provider)
        if not provider or provider == "mock":
            return self._mock_output(prompt, size)
        if provider == "seedream":
            result = self.generate_seedream_image(prompt, size=size)
        else:
            logger.warning("Image provider %s not implemented; using mock output", provider)
            result = self._mock_output(prompt, size)
        if not result.get("url"):
            logger.warning("Image generation returned no url; falling back to mock output")
            return self._mock_output(prompt)
        return result

    def _mock_output(self, prompt: str, size: str | None = None) -> dict:
        return {
            "provider": "mock",
            "model": None,
            "url": MOCK_IMAGE_URL,
            "size": size or "1x1",
            "prompt": (prompt or "").strip(),
            "created_at": self._utc_now(),
        }

    def _utc_now(self) -> str:
        return datetime.now(timezone.utc).isoformat()

    def _load_prompt_template(self) -> str:
        try:
            return PROMPT_PATH.read_text(encoding="utf-8").strip() or DEFAULT_PROMPT
        except OSError:
            logger.warning("Failed to read image prompt at %s; using default template", PROMPT_PATH)
            return DEFAULT_PROMPT

    def _seedream_endpoint(self) -> str:
        endpoint = (settings.seedream_image_endpoint or "").strip()
        if endpoint:
            return endpoint
        api_base = settings.seedream_api_base.rstrip("/")
        return f"{api_base}/images/generations"

    def _parse_seedream_response(self, data: dict) -> tuple[str | None, str | None]:
        def _extract(payload: object) -> tuple[str | None, str | None]:
            if isinstance(payload, list) and payload:
                item = payload[0] if isinstance(payload[0], dict) else {}
                return item.get("url") or item.get("image_url"), item.get("image_id")
            if isinstance(payload, dict):
                return payload.get("url") or payload.get("image_url"), payload.get("image_id")
            return None, None

        if not isinstance(data, dict):
            return None, None

        for key in ("data", "output"):
            url, image_id = _extract(data.get(key))
            if url or image_id:
                return url, image_id

        return data.get("url") or data.get("image_url"), data.get("image_id")

    def _seedream_request(self, payload: dict, prompt: str, model: str, size: str) -> dict:
        api_key = settings.seedream_api_key
        result = {
            "provider": "seedream",
            "model": model,
            "url": None,
            "size": size,
            "prompt": (prompt or "").strip(),
            "created_at": self._utc_now(),
            "request_id": None,
        }

        if not api_key:
            logger.error("Seedream provider selected but SEEDREAM_API_KEY is missing")
            return result

        try:
            response = requests.post(
                self._seedream_endpoint(),
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {api_key}",
                },
                json=payload,
                timeout=60,
            )
            response.raise_for_status()
        except requests.RequestException:
            logger.exception("Seedream API request failed")
            return result

        try:
            data = response.json()
        except ValueError:
            logger.error("Seedream API response was not valid JSON")
            return result

        if settings.environment != "production":
            logger.info("Seedream response payload: %s", data)

        result["request_id"] = data.get("request_id") or data.get("id")
        url, image_id = self._parse_seedream_response(data)
        result["url"] = url
        if not result["url"]:
            result["image_id"] = image_id
        return result

    def build_prompt(self, scene_summary: str, mood: str, keywords: list[str] | str | None) -> str:
        summary_text = (scene_summary or "").strip() or "No scene summary provided."
        mood_text = (mood or "").strip() or "neutral"
        if isinstance(keywords, list):
            keywords_text = ", ".join([str(item).strip() for item in keywords if str(item).strip()])
        elif isinstance(keywords, str):
            keywords_text = keywords.strip()
        else:
            keywords_text = ""
        prompt = self._prompt_template
        prompt = prompt.replace("{{scene_summary}}", summary_text)
        prompt = prompt.replace("{{mood}}", mood_text)
        prompt = prompt.replace("{{keywords}}", keywords_text)
        return prompt.strip()

    def generate_seedream_image(self, prompt: str, size: str | None = None) -> dict:
        model = settings.seedream_model or "doubao-seedream-4.0"
        cleaned_prompt = (prompt or "").strip()
        size = size or settings.seedream_default_size or "2K"

        payload = {
            "model": model,
            "prompt": cleaned_prompt or "No prompt provided.",
            "size": size,
        }
        return self._seedream_request(payload, cleaned_prompt, model, size)

    def generate_image_with_refs(
        self,
        prompt: str,
        images: list[str],
        size: str | None = None,
        model: str | None = None,
    ) -> dict:
        provider = normalize_provider(self._provider)
        if not provider or provider != "seedream":
            return self.generate_image(prompt, size=size)

        cleaned_prompt = (prompt or "").strip()
        ref_images = []
        for item in images:
            if isinstance(item, str) and item.strip():
                ref_images.append(item.strip())
        if ref_images:
            ref_images = list(dict.fromkeys(ref_images))
        if len(ref_images) > MAX_REFERENCE_IMAGES:
            ref_images = ref_images[:MAX_REFERENCE_IMAGES]

        if not ref_images:
            return self.generate_seedream_image(cleaned_prompt, size=size)

        model = model or settings.seedream_model or "doubao-seedream-4.0"
        size = size or settings.seedream_default_size or "2K"
        payload = {
            "model": model,
            "prompt": cleaned_prompt or "No prompt provided.",
            "images": ref_images,
            "size": size,
        }
        return self._seedream_request(payload, cleaned_prompt, model, size)
