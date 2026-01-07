import json
import logging
from datetime import datetime, timezone
from typing import Any, Dict, Optional
from uuid import uuid4

logger = logging.getLogger("app.events")

MAX_EVENTS = 200
EVENTS: list[Dict[str, Any]] = []


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def new_trace_id() -> str:
    return str(uuid4())


def emit_event(event_type: str, payload: Dict[str, Any], trace_id: Optional[str] = None) -> Dict[str, Any]:
    event = {
        "type": event_type,
        "trace_id": trace_id,
        "payload": payload,
        "ts": _utc_now(),
    }
    EVENTS.append(event)
    if len(EVENTS) > MAX_EVENTS:
        del EVENTS[: len(EVENTS) - MAX_EVENTS]
    logger.info("event=%s", json.dumps(event, ensure_ascii=True))
    return event
