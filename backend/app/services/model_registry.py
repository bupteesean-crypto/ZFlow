from __future__ import annotations

from dataclasses import dataclass

from app.core.config import settings


@dataclass(frozen=True)
class ModelSpec:
    id: str
    type: str
    provider: str
    model: str
    label: str
    is_default: bool = False
    requires_key: str | None = None


def _parse_allowlist(value: str) -> set[str]:
    if not isinstance(value, str):
        return set()
    return {item.strip() for item in value.split(",") if item.strip()}


def _api_key_present(env_name: str | None) -> bool:
    if not env_name:
        return True
    key_map = {
        "SEEDREAM_API_KEY": settings.seedream_api_key,
        "VIDU_API_KEY": settings.vidu_api_key,
        "RUNWAY_API_KEY": settings.runway_api_key,
        "PIKA_API_KEY": settings.pika_api_key,
        "SORA_API_KEY": settings.sora_api_key,
    }
    return bool(key_map.get(env_name, ""))


IMAGE_MODEL_ALLOWLIST = _parse_allowlist(settings.image_model_allowlist)
VIDEO_MODEL_ALLOWLIST = _parse_allowlist(settings.video_model_allowlist)


def _image_models() -> list[ModelSpec]:
    default_model = settings.seedream_model or "doubao-seedream-4.0"
    models = [
        ModelSpec(
            id="seedream-default",
            type="image",
            provider="seedream",
            model=default_model,
            label="Seedream 默认",
            is_default=True,
            requires_key="SEEDREAM_API_KEY",
        ),
        ModelSpec(
            id="seedream-4.0",
            type="image",
            provider="seedream",
            model="doubao-seedream-4.0",
            label="Seedream 4.0",
            requires_key="SEEDREAM_API_KEY",
        ),
        ModelSpec(
            id="seedream-3.0",
            type="image",
            provider="seedream",
            model="doubao-seedream-3.0",
            label="Seedream 3.0",
            requires_key="SEEDREAM_API_KEY",
        ),
    ]
    return _dedupe_models(models)


def _video_models() -> list[ModelSpec]:
    default_model = settings.vidu_video_model or "viduq2-pro-img2video"
    models = [
        ModelSpec(
            id="vidu-default",
            type="video",
            provider="vidu",
            model=default_model,
            label="Vidu 默认",
            is_default=True,
            requires_key="VIDU_API_KEY",
        ),
        ModelSpec(
            id="vidu-q2-pro",
            type="video",
            provider="vidu",
            model="viduq2-pro-img2video",
            label="Vidu Q2 Pro",
            requires_key="VIDU_API_KEY",
        ),
        ModelSpec(
            id="vidu-q2-fast",
            type="video",
            provider="vidu",
            model="viduq2-fast-img2video",
            label="Vidu Q2 Fast",
            requires_key="VIDU_API_KEY",
        ),
    ]
    return _dedupe_models(models)


def _dedupe_models(models: list[ModelSpec]) -> list[ModelSpec]:
    seen = set()
    deduped: list[ModelSpec] = []
    for spec in models:
        if not spec.model:
            continue
        key = (spec.type, spec.provider, spec.model)
        if key in seen:
            continue
        seen.add(key)
        deduped.append(spec)
    return deduped


def _is_enabled(spec: ModelSpec) -> tuple[bool, str | None]:
    if spec.requires_key and not _api_key_present(spec.requires_key):
        return False, "missing_key"
    allowlist = IMAGE_MODEL_ALLOWLIST if spec.type == "image" else VIDEO_MODEL_ALLOWLIST
    if allowlist:
        return spec.id in allowlist or spec.is_default, None if spec.id in allowlist or spec.is_default else "not_enabled"
    if spec.is_default:
        return True, None
    return False, "not_enabled"


def list_models(model_type: str | None = None) -> list[dict]:
    models = _image_models() + _video_models()
    if model_type:
        models = [spec for spec in models if spec.type == model_type]
    output = []
    for spec in models:
        enabled, reason = _is_enabled(spec)
        output.append(
            {
                "id": spec.id,
                "type": spec.type,
                "provider": spec.provider,
                "model": spec.model,
                "label": spec.label,
                "enabled": enabled,
                "is_default": spec.is_default,
                "disabled_reason": None if enabled else reason,
            }
        )
    return output


def get_default_model(model_type: str) -> ModelSpec | None:
    candidates = _image_models() if model_type == "image" else _video_models()
    for spec in candidates:
        if spec.is_default:
            return spec
    return candidates[0] if candidates else None


def resolve_model(model_id: str, model_type: str) -> ModelSpec | None:
    candidates = _image_models() if model_type == "image" else _video_models()
    for spec in candidates:
        if spec.id == model_id:
            return spec
    return None


def select_enabled_model(model_id: str | None, model_type: str) -> ModelSpec | None:
    if model_type not in {"image", "video"}:
        raise ValueError("model_type_invalid")
    spec = None
    if model_id:
        spec = resolve_model(model_id, model_type)
        if not spec:
            raise ValueError("model_id_not_found")
    else:
        spec = get_default_model(model_type)
    if not spec:
        return None
    enabled, _ = _is_enabled(spec)
    if not enabled:
        raise ValueError("model_id_not_enabled")
    return spec
