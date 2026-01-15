import json
from queue import Queue
from threading import Lock
from typing import Any, Dict, List, Tuple

HISTORY_LIMIT = 200
_event_history: Dict[str, List[Dict[str, Any]]] = {}
_subscribers: Dict[str, List[Queue]] = {}
_lock = Lock()


def reset_generation_events(project_id: str) -> None:
    with _lock:
        _event_history[project_id] = []


def publish_generation_event(project_id: str, payload: Dict[str, Any]) -> None:
    with _lock:
        history = _event_history.setdefault(project_id, [])
        history.append(payload)
        if len(history) > HISTORY_LIMIT:
            _event_history[project_id] = history[-HISTORY_LIMIT:]
        subscribers = list(_subscribers.get(project_id, []))
    for queue in subscribers:
        queue.put_nowait(payload)


def subscribe_generation_events(project_id: str) -> Tuple[Queue, List[Dict[str, Any]]]:
    queue: Queue = Queue()
    with _lock:
        _subscribers.setdefault(project_id, []).append(queue)
        history = list(_event_history.get(project_id, []))
    return queue, history


def unsubscribe_generation_events(project_id: str, queue: Queue) -> None:
    with _lock:
        queues = _subscribers.get(project_id, [])
        if queue in queues:
            queues.remove(queue)
        if not queues and project_id in _subscribers:
            _subscribers.pop(project_id, None)


def format_sse(payload: Dict[str, Any]) -> str:
    return f"data: {json.dumps(payload, ensure_ascii=False)}\n\n"
