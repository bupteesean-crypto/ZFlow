import base64
import hashlib
import logging

from cryptography.fernet import Fernet, InvalidToken

from app.core.config import settings

logger = logging.getLogger(__name__)


def _build_fernet() -> Fernet:
    secret = (settings.llm_key_encryption_key or "").strip()
    if not secret:
        raise RuntimeError("Missing required environment variable: LLM_KEY_ENCRYPTION_KEY")
    # Accept either a raw secret or an already base64-encoded Fernet key.
    if len(secret) >= 32:
        try:
            return Fernet(secret.encode("utf-8"))
        except Exception:
            pass
    derived = hashlib.sha256(secret.encode("utf-8")).digest()
    key = base64.urlsafe_b64encode(derived)
    return Fernet(key)


def encrypt_secret(value: str) -> str:
    if not value:
        return ""
    fernet = _build_fernet()
    return fernet.encrypt(value.encode("utf-8")).decode("utf-8")


def decrypt_secret(value: str) -> str:
    if not value:
        return ""
    fernet = _build_fernet()
    try:
        return fernet.decrypt(value.encode("utf-8")).decode("utf-8")
    except InvalidToken:
        logger.warning("Failed to decrypt secret: invalid token")
        return ""
