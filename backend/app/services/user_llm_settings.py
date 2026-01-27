import logging

from app.services.crypto import decrypt_secret

logger = logging.getLogger(__name__)

ALLOWED_LLM_BASES = {
    "https://bigmodel.cn",
    "https://chat.z.ai",
}


def normalize_llm_base(value: str) -> str:
    base = (value or "").strip().rstrip("/")
    if base in ALLOWED_LLM_BASES:
        return base
    raise ValueError("api_base not supported")


def has_llm_key(user: object) -> bool:
    return bool(getattr(user, "llm_api_key_encrypted", None))


def resolve_llm_overrides(user: object) -> dict:
    api_base = getattr(user, "llm_api_base", None)
    api_base = api_base.strip().rstrip("/") if isinstance(api_base, str) and api_base.strip() else None
    encrypted = getattr(user, "llm_api_key_encrypted", None)
    api_key = None
    if isinstance(encrypted, str) and encrypted.strip():
        try:
            api_key = decrypt_secret(encrypted.strip())
        except RuntimeError:
            logger.exception("LLM key decryption failed")
            api_key = None
    return {
        "api_base": api_base,
        "api_key": api_key,
        "allow_fallback": bool(getattr(user, "is_platform_admin", False)),
    }
