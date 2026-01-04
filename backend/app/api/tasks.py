from fastapi import APIRouter, HTTPException

router = APIRouter(prefix="/tasks", tags=["tasks"])


@router.post("")
async def create_task() -> dict:
    # TODO: validate request, persist task, enqueue worker job.
    raise HTTPException(status_code=501, detail="Task creation not implemented")


@router.get("/{task_id}")
async def get_task(task_id: str) -> dict:
    # TODO: retrieve task status and artifact metadata.
    raise HTTPException(status_code=501, detail="Task lookup not implemented")
