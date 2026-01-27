import asyncio
import json
import time
from collections import deque
from threading import Lock
from typing import Any, Dict, List, Tuple

HISTORY_LIMIT = 200
EVENT_TTL_SECONDS = 600

_event_history: Dict[str, deque[Dict[str, Any]]] = {}
_subscribers: Dict[str, List[Tuple[asyncio.Queue, asyncio.AbstractEventLoop]]] = {}
_done_at: Dict[str, float] = {}
_lock = Lock()


def _maybe_cleanup(now: float) -> None:
    expired = [key for key, ts in _done_at.items() if now - ts > EVENT_TTL_SECONDS]
    for key in expired:
        _event_history.pop(key, None)
        _subscribers.pop(key, None)
        _done_at.pop(key, None)


def publish_package_event(package_id: str, payload: Dict[str, Any]) -> None:
    now = time.time()
    with _lock:
        history = _event_history.setdefault(package_id, deque(maxlen=HISTORY_LIMIT))
        history.append(payload)
        subscribers = list(_subscribers.get(package_id, []))
        if payload.get("event") in {"done", "error"}:
            _done_at[package_id] = now
        _maybe_cleanup(now)
    for queue, loop in subscribers:
        loop.call_soon_threadsafe(queue.put_nowait, payload)


def subscribe_package_events(package_id: str) -> Tuple[asyncio.Queue, List[Dict[str, Any]]]:
    queue: asyncio.Queue = asyncio.Queue()
    loop = asyncio.get_running_loop()
    with _lock:
        _subscribers.setdefault(package_id, []).append((queue, loop))
        history = list(_event_history.get(package_id, []))
    return queue, history


def unsubscribe_package_events(package_id: str, queue: asyncio.Queue) -> None:
    with _lock:
        queues = _subscribers.get(package_id, [])
        remaining = [(item_queue, loop) for item_queue, loop in queues if item_queue is not queue]
        if remaining:
            _subscribers[package_id] = remaining
        else:
            _subscribers.pop(package_id, None)


def format_package_sse(payload: Dict[str, Any]) -> str:
    event_name = payload.get("event") or "message"
    return f"event: {event_name}\ndata: {json.dumps(payload, ensure_ascii=False)}\n\n"
