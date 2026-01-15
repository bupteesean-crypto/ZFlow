import os
from dataclasses import dataclass


def normalize_provider(value: str) -> str:
    return (value or "").strip().lower()


def require_provider(value: str, allowed: set[str], name: str) -> str:
    provider = normalize_provider(value)
    if not provider:
        raise RuntimeError(f"Missing required environment variable: {name}")
    if provider not in allowed:
        allowed_list = ", ".join(sorted(allowed))
        raise RuntimeError(f"Invalid {name}. Allowed: {allowed_list}")
    return provider


def require_api_key(value: str, env_name: str) -> str:
    if not value:
        raise RuntimeError(f"Missing required environment variable: {env_name}")
    return value


@dataclass(frozen=True)
class Settings:
    app_name: str = "ZFlow API"
    environment: str = os.getenv("APP_ENV", "local")
    log_level: str = os.getenv("LOG_LEVEL", "info")
    llm_provider: str = os.getenv("LLM_PROVIDER", "")
    image_provider: str = os.getenv("IMAGE_PROVIDER", "")
    video_provider: str = os.getenv("VIDEO_PROVIDER", "")
    openai_api_key: str = os.getenv("OPENAI_API_KEY", "")
    anthropic_api_key: str = os.getenv("ANTHROPIC_API_KEY", "")
    glm_api_key: str = os.getenv("GLM_API_KEY", "")
    glm_model: str = os.getenv("GLM_MODEL", "")
    stability_api_key: str = os.getenv("STABILITY_API_KEY", "")
    dalle_api_key: str = os.getenv("DALLE_API_KEY", "")
    seedream_api_key: str = os.getenv("SEEDREAM_API_KEY", "")
    seedream_model: str = os.getenv("SEEDREAM_MODEL", "doubao-seedream-4.0")
    seedream_api_base: str = os.getenv("SEEDREAM_API_BASE", "https://open.bigmodel.cn/api/paas/v4")
    seedream_image_endpoint: str = os.getenv("SEEDREAM_IMAGE_ENDPOINT", "")
    seedream_default_size: str = os.getenv("SEEDREAM_DEFAULT_SIZE", "960x1280")
    vidu_api_base: str = os.getenv("VIDU_API_BASE", "https://open.bigmodel.cn/api/paas/v4")
    vidu_api_key: str = os.getenv("VIDU_API_KEY", "")
    vidu_video_endpoint: str = os.getenv("VIDU_VIDEO_ENDPOINT", "")
    vidu_async_result_endpoint: str = os.getenv("VIDU_ASYNC_RESULT_ENDPOINT", "")
    vidu_video_model: str = os.getenv("VIDU_VIDEO_MODEL", "viduq2-pro-img2video")
    vidu_video_default_size: str = os.getenv("VIDU_VIDEO_DEFAULT_SIZE", "960x1280")
    runway_api_key: str = os.getenv("RUNWAY_API_KEY", "")
    pika_api_key: str = os.getenv("PIKA_API_KEY", "")
    sora_api_key: str = os.getenv("SORA_API_KEY", "")


settings = Settings()
