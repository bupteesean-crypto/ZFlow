from app.core.config import require_api_key, require_provider, settings


class VideoService:
    def __init__(self) -> None:
        self._provider = settings.video_provider

    def generate_video(self, prompt: str) -> str:
        provider = require_provider(self._provider, {"runway", "pika", "sora"}, "VIDEO_PROVIDER")
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
