from datetime import datetime, timezone
from typing import Any, Dict
from uuid import uuid4


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def new_id() -> str:
    return str(uuid4())


USERS_BY_PHONE: Dict[str, Dict[str, Any]] = {}
SESSIONS: Dict[str, Dict[str, Any]] = {}
GENERATION_TASKS: Dict[str, Dict[str, Any]] = {}
GENERATION_TRACES: Dict[str, str] = {}
EXPORT_TASKS: Dict[str, Dict[str, Any]] = {}
EXPORT_FILES: Dict[str, Dict[str, Any]] = {}
