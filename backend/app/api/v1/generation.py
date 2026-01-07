import time
from typing import Any, Dict

from fastapi import APIRouter, BackgroundTasks, Body, Depends, HTTPException
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.api.v1.response import ok
from app.core.events import emit_event, new_trace_id
from app.db.models import utc_now as db_utc_now
from app.db.session import SessionLocal, get_db
from app.repositories import material_packages as package_repo
from app.repositories import projects as project_repo
from app.store import GENERATION_TASKS, GENERATION_TRACES, new_id, utc_now

router = APIRouter(prefix="/generation", tags=["generation"])


def _simulate_generation(task_id: str) -> None:
    task = GENERATION_TASKS.get(task_id)
    if not task:
        return
    trace_id = GENERATION_TRACES.get(task_id)
    db = SessionLocal()
    try:
        try:
            project = project_repo.get_project(db, task["project_id"])
        except SQLAlchemyError:
            db.rollback()
            return
        if not project:
            return

        task["status"] = "running"
        task["progress"] = 10
        task["updated_at"] = utc_now()
        emit_event(
            "generation.progressed",
            {
                "project_id": task["project_id"],
                "task_id": task_id,
                "progress": task["progress"],
                "status": task["status"],
            },
            trace_id=trace_id,
        )
        time.sleep(1)

        task["progress"] = 60
        task["updated_at"] = utc_now()
        emit_event(
            "generation.progressed",
            {
                "project_id": task["project_id"],
                "task_id": task_id,
                "progress": task["progress"],
                "status": task["status"],
            },
            trace_id=trace_id,
        )
        time.sleep(1)

        task["status"] = "completed"
        task["progress"] = 100
        task["updated_at"] = utc_now()
        emit_event(
            "generation.completed",
            {
                "project_id": task["project_id"],
                "task_id": task_id,
                "progress": task["progress"],
                "status": task["status"],
            },
            trace_id=trace_id,
        )

        package_id = task.get("material_package_id")
        if package_id:
            try:
                package_repo.update_package(
                    db,
                    package_id,
                    {
                        "status": "completed",
                        "summary": "Mock material package generated",
                        "generated_at": db_utc_now(),
                    },
                )
            except SQLAlchemyError:
                db.rollback()
                return

        try:
            project_repo.update_project(
                db,
                task["project_id"],
                {"status": "editing", "stage": "editing", "progress": 50},
            )
        except SQLAlchemyError:
            db.rollback()
            return
    finally:
        db.close()


@router.post("/start")
async def start_generation(
    background_tasks: BackgroundTasks,
    payload: Dict[str, Any] = Body(default_factory=dict),
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    project_id = payload.get("project_id")
    if not isinstance(project_id, str) or not project_id.strip():
        raise HTTPException(status_code=400, detail="project_id required")
    try:
        project = project_repo.get_project(db, project_id)
    except SQLAlchemyError:
        db.rollback()
        raise HTTPException(status_code=500, detail="Database error")
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    try:
        package = package_repo.create_package(
            db,
            project_id=project_id,
            package_name="Package v1",
            status="generating",
            materials={
                "storyline": {"title": "Mock Story", "content": "Demo content", "summary": "Demo summary"},
                "art_style": {"style_name": "Minimal", "description": "Clean visuals"},
                "characters": [],
                "scenes": [],
                "storyboards": [],
            },
        )
        project_repo.update_project(
            db,
            project_id,
            {
                "last_material_package_id": package["id"],
                "status": "generating",
                "stage": "generating",
                "progress": 5,
            },
        )
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except SQLAlchemyError:
        db.rollback()
        raise HTTPException(status_code=500, detail="Database error")

    task_id = new_id()
    trace_id = new_trace_id()
    task = {
        "id": task_id,
        "project_id": project_id,
        "material_package_id": package["id"],
        "status": "pending",
        "progress": 0,
        "created_at": utc_now(),
        "updated_at": utc_now(),
    }
    GENERATION_TASKS[task_id] = task
    GENERATION_TRACES[task_id] = trace_id
    emit_event(
        "generation.started",
        {
            "project_id": project_id,
            "task_id": task_id,
            "material_package_id": package["id"],
        },
        trace_id=trace_id,
    )

    background_tasks.add_task(_simulate_generation, task_id)
    return ok(task)


@router.get("/progress/{project_id}")
async def get_generation_progress(
    project_id: str,
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    if not project_id.strip():
        raise HTTPException(status_code=400, detail="project_id required")
    try:
        project = project_repo.get_project(db, project_id)
    except SQLAlchemyError:
        db.rollback()
        raise HTTPException(status_code=500, detail="Database error")
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    tasks = [task for task in GENERATION_TASKS.values() if task["project_id"] == project_id]
    return ok({"list": tasks})


@router.post("/retry/{task_id}")
async def retry_generation(
    task_id: str,
    background_tasks: BackgroundTasks,
) -> Dict[str, Any]:
    if not task_id.strip():
        raise HTTPException(status_code=400, detail="task_id required")
    task = GENERATION_TASKS.get(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    task["status"] = "pending"
    task["progress"] = 0
    task["updated_at"] = utc_now()
    trace_id = GENERATION_TRACES.get(task_id)
    emit_event(
        "generation.started",
        {
            "project_id": task["project_id"],
            "task_id": task_id,
            "material_package_id": task.get("material_package_id"),
            "retry": True,
        },
        trace_id=trace_id,
    )
    background_tasks.add_task(_simulate_generation, task_id)
    return ok(task)


@router.post("/skip/{task_id}")
async def skip_generation(task_id: str) -> Dict[str, Any]:
    if not task_id.strip():
        raise HTTPException(status_code=400, detail="task_id required")
    task = GENERATION_TASKS.get(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    task["status"] = "failed"
    task["updated_at"] = utc_now()
    trace_id = GENERATION_TRACES.get(task_id)
    emit_event(
        "generation.completed",
        {
            "project_id": task["project_id"],
            "task_id": task_id,
            "status": task["status"],
            "skipped": True,
        },
        trace_id=trace_id,
    )
    return ok(task)
