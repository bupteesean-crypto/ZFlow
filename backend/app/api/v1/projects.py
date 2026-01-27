from typing import Any, Dict

import logging

from fastapi import APIRouter, Body, Depends, HTTPException, Query
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.api.v1.deps import get_current_user
from app.api.v1.response import ok
from app.db.session import get_db
from app.repositories import projects as project_repo
from app.services.access_control import can_access_project, can_manage_project

router = APIRouter(prefix="/projects", tags=["projects"])
logger = logging.getLogger(__name__)

PROJECT_STATUSES = {"draft", "generating", "editing", "completed", "exported"}
PROJECT_STAGES = {"input", "generating", "editing", "completed"}


@router.get("")
async def list_projects(
    current_user: object = Depends(get_current_user),
    db: Session = Depends(get_db),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
) -> Dict[str, Any]:
    try:
        items, total = project_repo.list_projects_for_user(db, current_user, page, page_size)
    except SQLAlchemyError:
        db.rollback()
        raise HTTPException(status_code=500, detail="Database error")
    return ok({"list": items, "total": total, "page": page, "page_size": page_size})


@router.post("")
async def create_project(
    payload: Dict[str, Any] = Body(default_factory=dict),
    current_user: object = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    name = payload.get("name")
    if name is not None and not isinstance(name, str):
        raise HTTPException(status_code=400, detail="name must be a string")
    space_type = payload.get("space_type")
    if space_type is not None and space_type not in {"personal", "team"}:
        raise HTTPException(status_code=400, detail="space_type invalid")
    team_space_id = payload.get("team_space_id")
    if team_space_id is not None and not isinstance(team_space_id, str):
        raise HTTPException(status_code=400, detail="team_space_id must be a string")
    visibility = payload.get("visibility")
    if visibility is not None and visibility not in {"private", "company"}:
        raise HTTPException(status_code=400, detail="visibility invalid")
    company_id = getattr(current_user, "company_id", None)
    if visibility == "company" and not company_id:
        raise HTTPException(status_code=400, detail="company visibility requires company membership")
    if visibility is None:
        visibility = "company" if company_id else "private"
    try:
        project = project_repo.create_project(
            db,
            name,
            space_type,
            team_space_id,
            owner_user_id=getattr(current_user, "id", None),
            company_id=company_id,
            visibility=visibility,
        )
        return ok(project)
    except SQLAlchemyError:
        db.rollback()
        logger.exception("Failed to create project")
        raise HTTPException(status_code=500, detail="Database error")


@router.get("/{project_id}")
async def get_project(
    project_id: str,
    current_user: object = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    try:
        project = project_repo.get_project(db, project_id)
    except SQLAlchemyError:
        db.rollback()
        raise HTTPException(status_code=500, detail="Database error")
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    if not can_access_project(current_user, project):
        raise HTTPException(status_code=403, detail="Forbidden")
    return ok(project)


@router.put("/{project_id}")
async def update_project(
    project_id: str,
    payload: Dict[str, Any] = Body(default_factory=dict),
    current_user: object = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    if "name" in payload and payload["name"] is not None and not isinstance(payload["name"], str):
        raise HTTPException(status_code=400, detail="name must be a string")
    if "description" in payload and payload["description"] is not None and not isinstance(payload["description"], str):
        raise HTTPException(status_code=400, detail="description must be a string")
    if "tags" in payload and payload["tags"] is not None and not isinstance(payload["tags"], list):
        raise HTTPException(status_code=400, detail="tags must be a list")
    if "metadata" in payload and payload["metadata"] is not None and not isinstance(payload["metadata"], dict):
        raise HTTPException(status_code=400, detail="metadata must be an object")
    if "input_config" in payload and payload["input_config"] is not None and not isinstance(payload["input_config"], dict):
        raise HTTPException(status_code=400, detail="input_config must be an object")
    if "status" in payload and payload["status"] not in PROJECT_STATUSES:
        raise HTTPException(status_code=400, detail="status invalid")
    if "stage" in payload and payload["stage"] not in PROJECT_STAGES:
        raise HTTPException(status_code=400, detail="stage invalid")
    if "progress" in payload:
        progress = payload["progress"]
        if not isinstance(progress, int) or progress < 0 or progress > 100:
            raise HTTPException(status_code=400, detail="progress must be 0-100")
    if "visibility" in payload and payload["visibility"] not in {"private", "company"}:
        raise HTTPException(status_code=400, detail="visibility invalid")
    try:
        project = project_repo.get_project(db, project_id)
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")
        if not can_manage_project(current_user, project):
            raise HTTPException(status_code=403, detail="Forbidden")
        project = project_repo.update_project(db, project_id, payload)
    except SQLAlchemyError:
        db.rollback()
        raise HTTPException(status_code=500, detail="Database error")
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return ok(project)


@router.delete("/{project_id}")
async def delete_project(
    project_id: str,
    current_user: object = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    try:
        project = project_repo.get_project(db, project_id)
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")
        if not can_manage_project(current_user, project):
            raise HTTPException(status_code=403, detail="Forbidden")
        deleted = project_repo.delete_project(db, project_id)
    except SQLAlchemyError:
        db.rollback()
        raise HTTPException(status_code=500, detail="Database error")
    if not deleted:
        raise HTTPException(status_code=404, detail="Project not found")
    return ok({"deleted": True})
