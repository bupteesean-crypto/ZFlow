import logging

import requests

from app.core.config import require_api_key, require_provider, settings

logger = logging.getLogger(__name__)


class VideoService:
    def __init__(self) -> None:
        self._provider = settings.video_provider

    def generate_video_from_image(
        self,
        prompt: str,
        image_urls: list[str],
        size: str | None = None,
        model: str | None = None,
    ) -> dict:
        provider = require_provider(
            self._provider,
            {"vidu", "runway", "pika", "sora"},
            "VIDEO_PROVIDER",
        )
        if provider == "vidu":
            return self._generate_vidu_video(prompt, image_urls, size, model)
        if provider == "runway":
            require_api_key(settings.runway_api_key, "RUNWAY_API_KEY")
            raise NotImplementedError("Runway provider not implemented")
        if provider == "pika":
            require_api_key(settings.pika_api_key, "PIKA_API_KEY")
            raise NotImplementedError("Pika provider not implemented")
        if provider == "sora":
            require_api_key(settings.sora_api_key, "SORA_API_KEY")
            raise NotImplementedError("Sora provider not implemented")
        raise RuntimeError("Unsupported video provider")

    def _video_endpoint(self) -> str:
        endpoint = (settings.vidu_video_endpoint or "").strip()
        if endpoint:
            return endpoint
        api_base = (settings.vidu_api_base or "https://open.bigmodel.cn/api/paas/v4").rstrip("/")
        return f"{api_base}/videos/generations"

    def _video_model(self, model: str | None) -> str:
        return model or settings.vidu_video_model or "viduq2-pro-img2video"

    def _video_size(self, size: str | None) -> str:
        return size or settings.vidu_video_default_size or "1280x720"

    def _generate_vidu_video(
        self,
        prompt: str,
        image_urls: list[str],
        size: str | None,
        model: str | None,
    ) -> dict:
        cleaned_prompt = (prompt or "").strip()
        model = self._video_model(model)
        size = self._video_size(size)
        urls = [url.strip() for url in image_urls if isinstance(url, str) and url.strip()]

        payload = {
            "model": model,
            "prompt": cleaned_prompt or "No prompt provided.",
            "image_url": urls,
            "size": size,
        }

        result = {
            "provider": "vidu",
            "model": model,
            "prompt": cleaned_prompt,
            "size": size,
            "task_id": None,
            "request_id": None,
            "task_status": None,
        }
        if not urls:
            logger.error("Video generation requires at least one image_url")
            return result
        api_key = require_api_key(settings.vidu_api_key, "VIDU_API_KEY")

        try:
            response = requests.post(
                self._video_endpoint(),
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {api_key}",
                },
                json=payload,
                timeout=60,
            )
            response.raise_for_status()
        except requests.RequestException:
            logger.exception("Seedream video API request failed")
            return result

        try:
            data = response.json()
        except ValueError:
            logger.error("Seedream video API response was not valid JSON")
            return result

        if settings.environment != "production":
            logger.info("Seedream video response payload: %s", data)

        result["task_id"] = data.get("id") or data.get("task_id")
        result["request_id"] = data.get("request_id")
        result["task_status"] = data.get("task_status")
        return result
