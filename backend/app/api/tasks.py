import itertools
import time
from datetime import datetime, timezone
from typing import Any, Dict, List

from fastapi import APIRouter, BackgroundTasks, Body, HTTPException

router = APIRouter(prefix="/tasks", tags=["tasks"])

TASKS: Dict[str, Dict[str, Any]] = {}
TASK_COUNTER = itertools.count(1)


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _simulate_task_lifecycle(task_id: str) -> None:
    task = TASKS.get(task_id)
    if not task:
        return
    task["status"] = "running"
    time.sleep(2)
    task["status"] = "done"
    task["output"] = {
        "artifact_url": f"/artifacts/{task_id}.mp4",
        "summary": "Mock render complete",
    }


@router.post("")
async def create_task(
    background_tasks: BackgroundTasks,
    payload: Dict[str, Any] = Body(default_factory=dict),
) -> Dict[str, Any]:
    task_id = str(next(TASK_COUNTER))
    pipeline = str(payload.get("pipeline") or "video-basic-v1")
    task_input = payload.get(
        "input",
        {
            "prompt": payload.get("prompt", "Create a 15s product intro"),
            "style": payload.get("style", "minimal"),
            "duration_seconds": payload.get("duration_seconds", 15),
        },
    )
    task = {
        "id": task_id,
        "status": "pending",
        "created_at": _utc_now(),
        "pipeline": pipeline,
        "input": task_input,
        "output": None,
    }
    TASKS[task_id] = task

    # Simulate async execution without a real worker.
    background_tasks.add_task(_simulate_task_lifecycle, task_id)
    return task


@router.get("")
async def list_tasks() -> List[Dict[str, Any]]:
    return list(TASKS.values())


@router.get("/{task_id}")
async def get_task(task_id: str) -> Dict[str, Any]:
    task = TASKS.get(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task
