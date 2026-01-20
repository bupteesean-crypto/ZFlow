import logging
import time
from typing import Any, Dict

from fastapi import APIRouter, BackgroundTasks, Body, Depends, HTTPException
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.api.v1.response import ok
from app.db.session import SessionLocal, get_db
from app.repositories import projects as project_repo
from app.store import EXPORT_FILES, EXPORT_TASKS, new_id, utc_now

router = APIRouter(tags=["exports"])
logger = logging.getLogger(__name__)

_EXPORT_STATUSES = {"pending", "running", "completed", "failed", "canceled"}
_EXPORT_FORMATS = {"mp4", "mov"}
_EXPORT_RESOLUTIONS = {"720p", "1080p", "4k"}
_EXPORT_ASPECTS = {"16:9", "9:16", "1:1"}


def _estimate_minutes(resolution: str) -> int:
    if resolution == "4k":
        return 8
    if resolution == "1080p":
        return 5
    return 3


def _simulate_export_task(task_id: str, project_id: str) -> None:
    task = EXPORT_TASKS.get(task_id)
    if not task:
        return
    task["status"] = "running"
    task["updated_at"] = utc_now()
    task["progress"] = 10
    time.sleep(2)
    task["progress"] = 60
    task["updated_at"] = utc_now()
    time.sleep(2)
    task["progress"] = 90
    task["updated_at"] = utc_now()
    time.sleep(1)
    task["status"] = "completed"
    task["progress"] = 100
    task["updated_at"] = utc_now()

    export_file_id = new_id()
    export_config = task.get("export_config") if isinstance(task.get("export_config"), dict) else {}
    fmt = export_config.get("format") or "mp4"
    EXPORT_FILES[export_file_id] = {
        "id": export_file_id,
        "project_id": project_id,
        "task_id": task_id,
        "format": fmt,
        "resolution": export_config.get("resolution"),
        "aspect_ratio": export_config.get("aspect_ratio"),
        "url": f"https://example.com/exports/{export_file_id}.{fmt}",
        "created_at": utc_now(),
    }
    task["file_id"] = export_file_id

    db = SessionLocal()
    try:
        project_repo.update_project(
            db,
            project_id,
            {"status": "exported", "stage": "completed", "progress": 100},
        )
    except SQLAlchemyError:
        db.rollback()
        logger.exception("Failed to update project export status project_id=%s", project_id)
    finally:
        db.close()


@router.post("/projects/{project_id}/export")
async def create_export_task(
    project_id: str,
    background_tasks: BackgroundTasks,
    payload: Dict[str, Any] = Body(default_factory=dict),
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

    resolution = payload.get("resolution") or "1080p"
    fmt = payload.get("format") or "mp4"
    aspect_ratio = payload.get("aspect_ratio") or "16:9"
    subtitle_enabled = payload.get("subtitle_enabled") is True
    subtitle_burn_in = payload.get("subtitle_burn_in") is True
    subtitle_style = payload.get("subtitle_style") if isinstance(payload.get("subtitle_style"), dict) else {}
    cover_mode = payload.get("cover_mode") or "auto"

    if resolution not in _EXPORT_RESOLUTIONS:
        raise HTTPException(status_code=400, detail="resolution invalid")
    if fmt not in _EXPORT_FORMATS:
        raise HTTPException(status_code=400, detail="format invalid")
    if aspect_ratio not in _EXPORT_ASPECTS:
        raise HTTPException(status_code=400, detail="aspect_ratio invalid")
    if cover_mode not in {"auto", "none"}:
        raise HTTPException(status_code=400, detail="cover_mode invalid")

    task_id = new_id()
    estimated_minutes = _estimate_minutes(resolution)
    export_config = {
        "resolution": resolution,
        "format": fmt,
        "aspect_ratio": aspect_ratio,
        "subtitle": {
            "enabled": subtitle_enabled,
            "burn_in": subtitle_burn_in,
            "style": subtitle_style,
        },
        "cover": {"mode": cover_mode},
    }

    EXPORT_TASKS[task_id] = {
        "id": task_id,
        "project_id": project_id,
        "status": "pending",
        "progress": 0,
        "export_config": export_config,
        "estimated_minutes": estimated_minutes,
        "created_at": utc_now(),
        "updated_at": utc_now(),
    }

    background_tasks.add_task(_simulate_export_task, task_id, project_id)
    return ok({"export_task_id": task_id, "estimated_minutes": estimated_minutes})


@router.get("/export-tasks/{task_id}")
async def get_export_task(task_id: str) -> Dict[str, Any]:
    if not task_id.strip():
        raise HTTPException(status_code=400, detail="task_id required")
    task = EXPORT_TASKS.get(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Export task not found")
    if task.get("status") not in _EXPORT_STATUSES:
        task["status"] = "failed"
    return ok(task)


@router.get("/projects/{project_id}/export-files")
async def list_export_files(project_id: str) -> Dict[str, Any]:
    if not project_id.strip():
        raise HTTPException(status_code=400, detail="project_id required")
    files = [item for item in EXPORT_FILES.values() if item.get("project_id") == project_id]
    files = sorted(files, key=lambda item: item.get("created_at") or "", reverse=True)
    return ok({"list": files})


@router.get("/export-files/{file_id}/download-url")
async def get_export_download_url(file_id: str) -> Dict[str, Any]:
    if not file_id.strip():
        raise HTTPException(status_code=400, detail="file_id required")
    export_file = EXPORT_FILES.get(file_id)
    if not export_file:
        raise HTTPException(status_code=404, detail="Export file not found")
    return ok({"url": export_file.get("url")})
