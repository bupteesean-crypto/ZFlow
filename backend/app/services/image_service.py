from app.core.config import require_api_key, require_provider, settings


class ImageService:
    def __init__(self) -> None:
        self._provider = settings.image_provider

    def generate_image(self, prompt: str) -> str:
        provider = require_provider(self._provider, {"stability", "dalle"}, "IMAGE_PROVIDER")
        if provider == "stability":
            require_api_key(settings.stability_api_key, "STABILITY_API_KEY")
            raise NotImplementedError("Stability provider not implemented")
        if provider == "dalle":
            require_api_key(settings.dalle_api_key, "DALLE_API_KEY")
            raise NotImplementedError("DALL-E provider not implemented")
        raise RuntimeError("Unsupported image provider")
