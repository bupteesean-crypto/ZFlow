import time
from typing import Any, Dict, Optional

from fastapi import APIRouter, BackgroundTasks, Body, HTTPException

from app.api.v1.response import ok
from app.store import GENERATION_TASKS, MATERIAL_PACKAGES, PROJECTS, new_id, utc_now

router = APIRouter(prefix="/generation", tags=["generation"])


def _simulate_generation(task_id: str) -> None:
    task = GENERATION_TASKS.get(task_id)
    if not task:
        return
    project = PROJECTS.get(task["project_id"])
    if not project:
        return

    task["status"] = "running"
    task["progress"] = 10
    task["updated_at"] = utc_now()
    time.sleep(1)

    task["progress"] = 60
    task["updated_at"] = utc_now()
    time.sleep(1)

    task["status"] = "completed"
    task["progress"] = 100
    task["updated_at"] = utc_now()

    package_id = task.get("material_package_id")
    package = MATERIAL_PACKAGES.get(package_id) if package_id else None
    if package:
        package["status"] = "completed"
        package["summary"] = "Mock material package generated"
        package["generated_at"] = utc_now()
        package["updated_at"] = utc_now()

    project["status"] = "editing"
    project["stage"] = "editing"
    project["progress"] = 50
    project["updated_at"] = utc_now()


def _build_material_package(project_id: str) -> Dict[str, Any]:
    now = utc_now()
    return {
        "id": new_id(),
        "project_id": project_id,
        "parent_id": None,
        "package_name": "Package v1",
        "status": "generating",
        "is_active": True,
        "summary": None,
        "materials": {
            "storyline": {"title": "Mock Story", "content": "Demo content", "summary": "Demo summary"},
            "art_style": {"style_name": "Minimal", "description": "Clean visuals"},
            "characters": [],
            "scenes": [],
            "storyboards": [],
        },
        "generated_at": None,
        "created_at": now,
        "updated_at": now,
    }


@router.post("/start")
async def start_generation(
    background_tasks: BackgroundTasks,
    payload: Dict[str, Any] = Body(default_factory=dict),
) -> Dict[str, Any]:
    project_id = payload.get("project_id")
    if not project_id:
        raise HTTPException(status_code=400, detail="project_id required")
    project = PROJECTS.get(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    package = _build_material_package(project_id)
    MATERIAL_PACKAGES[package["id"]] = package
    project["last_material_package_id"] = package["id"]

    task_id = new_id()
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

    project["status"] = "generating"
    project["stage"] = "generating"
    project["progress"] = 5
    project["updated_at"] = utc_now()

    background_tasks.add_task(_simulate_generation, task_id)
    return ok(task)


@router.get("/progress/{project_id}")
async def get_generation_progress(project_id: str) -> Dict[str, Any]:
    if project_id not in PROJECTS:
        raise HTTPException(status_code=404, detail="Project not found")
    tasks = [task for task in GENERATION_TASKS.values() if task["project_id"] == project_id]
    return ok({"list": tasks})


@router.post("/retry/{task_id}")
async def retry_generation(
    task_id: str,
    background_tasks: BackgroundTasks,
) -> Dict[str, Any]:
    task = GENERATION_TASKS.get(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    task["status"] = "pending"
    task["progress"] = 0
    task["updated_at"] = utc_now()
    background_tasks.add_task(_simulate_generation, task_id)
    return ok(task)


@router.post("/skip/{task_id}")
async def skip_generation(task_id: str) -> Dict[str, Any]:
    task = GENERATION_TASKS.get(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    task["status"] = "failed"
    task["updated_at"] = utc_now()
    return ok(task)
