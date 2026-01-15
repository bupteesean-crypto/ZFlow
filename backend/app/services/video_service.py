import base64
import logging
from urllib.parse import urlsplit, urlunsplit

import requests

from app.core.config import require_api_key, require_provider, settings

logger = logging.getLogger(__name__)
RAW_GITHUB_HOSTS = {"raw.githubusercontent.com"}
CDN_GITHUB_HOST = "cdn.jsdelivr.net"
SIGNED_QUERY_MARKERS = ("x-tos-", "x-amz-", "x-oss-", "signature=")
DATA_URL_PREFIX = "data:"
MAX_BASE64_BYTES = 10 * 1024 * 1024
ALLOWED_IMAGE_TYPES = {"image/png", "image/jpeg", "image/jpg", "image/webp"}
VIDU_ALLOWED_SIZES = {"1280x720", "1920x1080"}


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

    def get_video_task_result(self, task_id: str) -> dict:
        provider = require_provider(
            self._provider,
            {"vidu", "runway", "pika", "sora"},
            "VIDEO_PROVIDER",
        )
        if provider == "vidu":
            return self._get_vidu_task_result(task_id)
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

    def _async_result_endpoint(self, task_id: str) -> str:
        endpoint = (settings.vidu_async_result_endpoint or "").strip()
        if endpoint:
            return endpoint.format(task_id=task_id)
        api_base = (settings.vidu_api_base or "https://open.bigmodel.cn/api/paas/v4").rstrip("/")
        return f"{api_base}/async-result/{task_id}"

    def _video_model(self, model: str | None) -> str:
        return model or settings.vidu_video_model or "viduq2-pro-img2video"

    def _video_size(self, size: str | None) -> str:
        candidate = size or settings.vidu_video_default_size or "1280x720"
        if candidate not in VIDU_ALLOWED_SIZES:
            logger.warning("Unsupported video size %s; using default 1280x720", candidate)
            return "1280x720"
        return candidate

    def _convert_to_cdn_url(self, url: str) -> str:
        if not isinstance(url, str):
            return ""
        cleaned = url.strip()
        if not cleaned:
            return ""
        parsed = urlsplit(cleaned)
        if parsed.netloc not in RAW_GITHUB_HOSTS:
            return cleaned
        parts = [part for part in parsed.path.split("/") if part]
        if len(parts) < 4:
            return cleaned
        user, repo, branch = parts[:3]
        rest = "/".join(parts[3:])
        cdn_path = f"/gh/{user}/{repo}@{branch}/{rest}"
        return urlunsplit((parsed.scheme or "https", CDN_GITHUB_HOST, cdn_path, "", ""))

    def _is_signed_url(self, parsed_url) -> bool:
        if not parsed_url:
            return False
        query = (parsed_url.query or "").lower()
        return any(marker in query for marker in SIGNED_QUERY_MARKERS)

    def _download_as_data_url(self, url: str) -> str:
        try:
            response = requests.get(url, timeout=30)
            response.raise_for_status()
        except requests.RequestException:
            logger.exception("Failed to download image for base64 conversion")
            return ""

        if len(response.content) > MAX_BASE64_BYTES:
            logger.warning("Image exceeds base64 size limit: %s bytes", len(response.content))
            return ""

        content_type = response.headers.get("Content-Type", "").split(";", 1)[0].strip().lower()
        if content_type and content_type not in ALLOWED_IMAGE_TYPES:
            logger.warning("Unsupported image content-type for video: %s", content_type)
            return ""
        if not content_type:
            content_type = "image/jpeg"

        encoded = base64.b64encode(response.content).decode("ascii")
        return f"{DATA_URL_PREFIX}{content_type};base64,{encoded}"

    def _convert_jpeg_extension(self, url: str) -> str:
        if not isinstance(url, str):
            return ""
        cleaned = url.strip()
        if not cleaned:
            return ""
        parsed = urlsplit(cleaned)
        path = (parsed.path or "")
        if not path.lower().endswith(".jpeg"):
            return cleaned
        alt_path = f"{path[:-5]}.jpg"
        alt_url = urlunsplit((parsed.scheme, parsed.netloc, alt_path, parsed.query, parsed.fragment))
        try:
            response = requests.head(alt_url, timeout=10)
            if response.status_code < 400:
                return alt_url
        except requests.RequestException:
            logger.exception("Failed to validate .jpg replacement for video input")
        return cleaned

    def _prepare_vidu_image_input(self, url: str) -> str:
        if not isinstance(url, str):
            return ""
        cleaned = url.strip()
        if not cleaned:
            return ""
        if cleaned.startswith(DATA_URL_PREFIX):
            return cleaned

        parsed = urlsplit(cleaned)
        if parsed.scheme not in {"http", "https"}:
            return ""

        if self._is_signed_url(parsed):
            data_url = self._download_as_data_url(cleaned)
            if data_url:
                return data_url
            logger.warning("Signed image URL could not be converted to base64; using original URL")
            return cleaned

        return self._convert_jpeg_extension(cleaned)

    def _normalize_image_urls(self, image_urls: list[str]) -> list[str]:
        urls: list[str] = []
        for url in image_urls:
            if not isinstance(url, str):
                continue
            cleaned = url.strip()
            if not cleaned:
                continue
            if cleaned.startswith(DATA_URL_PREFIX):
                urls.append(cleaned)
                continue
            if not (cleaned.startswith("http://") or cleaned.startswith("https://")):
                continue
            cdn_url = self._convert_to_cdn_url(cleaned)
            prepared = self._prepare_vidu_image_input(cdn_url)
            if prepared:
                urls.append(prepared)
        return urls

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
        urls = self._normalize_image_urls(image_urls)

        if len(urls) > 1:
            logger.warning("Vidu only supports 1 image; extra images will be ignored")
        image_input = urls[0] if urls else ""
        payload = {
            "model": model,
            "prompt": cleaned_prompt or "No prompt provided.",
            "image_url": image_input,
            "size": size,
        }
        if image_input:
            preview = image_input
            if isinstance(preview, str) and preview.startswith(DATA_URL_PREFIX):
                preview = preview[:200] + "...(base64)"
            logger.info("Sending Vidu image_url preview: %s", preview)

        result = {
            "provider": "vidu",
            "model": model,
            "prompt": cleaned_prompt,
            "size": size,
            "task_id": None,
            "request_id": None,
            "task_status": None,
        }
        if not image_input:
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
            if response.status_code >= 400:
                logger.error(
                    "BigModel video API error: status=%s body=%s",
                    response.status_code,
                    response.text,
                )
            response.raise_for_status()
        except requests.RequestException:
            logger.exception("BigModel video API request failed")
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

    def _get_vidu_task_result(self, task_id: str) -> dict:
        result = {
            "provider": "vidu",
            "task_id": task_id,
            "task_status": None,
            "video_url": None,
            "cover_image_url": None,
            "request_id": None,
            "raw_response": None,
        }
        if not task_id:
            return result
        api_key = require_api_key(settings.vidu_api_key, "VIDU_API_KEY")

        try:
            response = requests.get(
                self._async_result_endpoint(task_id),
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {api_key}",
                },
                timeout=60,
            )
            if response.status_code >= 400:
                logger.error(
                    "BigModel video async-result error: status=%s body=%s",
                    response.status_code,
                    response.text,
                )
            response.raise_for_status()
        except requests.RequestException:
            logger.exception("BigModel video async-result request failed")
            return result

        try:
            data = response.json()
        except ValueError:
            logger.error("BigModel video async-result response was not valid JSON")
            return result

        if settings.environment != "production":
            logger.info("BigModel video async-result payload: %s", data)

        result["raw_response"] = data
        result["request_id"] = data.get("request_id")
        result["task_status"] = data.get("task_status")
        video_list = data.get("video_result") if isinstance(data.get("video_result"), list) else []
        if video_list:
            first = video_list[0] if isinstance(video_list[0], dict) else {}
            result["video_url"] = first.get("url")
            result["cover_image_url"] = first.get("cover_image_url")
        return result
