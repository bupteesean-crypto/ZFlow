from typing import Any, Dict

from fastapi import APIRouter, Body, Depends, HTTPException
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.api.v1.response import ok
from app.db.session import get_db
from app.repositories import material_packages as package_repo
from app.repositories import projects as project_repo

router = APIRouter(tags=["material-packages"])

PACKAGE_STATUSES = {"generating", "completed", "failed"}


@router.get("/projects/{project_id}/material-packages")
async def list_material_packages(
    project_id: str,
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    try:
        project = project_repo.get_project(db, project_id)
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")
        items = package_repo.list_packages_for_project(db, project_id)
    except HTTPException:
        raise
    except SQLAlchemyError:
        db.rollback()
        raise HTTPException(status_code=500, detail="Database error")
    return ok({"list": items, "total": len(items)})


@router.get("/material-packages/{package_id}")
async def get_material_package(
    package_id: str,
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    try:
        package = package_repo.get_package(db, package_id)
    except SQLAlchemyError:
        db.rollback()
        raise HTTPException(status_code=500, detail="Database error")
    if not package:
        raise HTTPException(status_code=404, detail="Material package not found")
    return ok(package)


@router.put("/material-packages/{package_id}")
async def update_material_package(
    package_id: str,
    payload: Dict[str, Any] = Body(default_factory=dict),
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    if "package_name" in payload and payload["package_name"] is not None and not isinstance(payload["package_name"], str):
        raise HTTPException(status_code=400, detail="package_name must be a string")
    if "summary" in payload and payload["summary"] is not None and not isinstance(payload["summary"], str):
        raise HTTPException(status_code=400, detail="summary must be a string")
    if "materials" in payload and payload["materials"] is not None and not isinstance(payload["materials"], dict):
        raise HTTPException(status_code=400, detail="materials must be an object")
    if "status" in payload and payload["status"] not in PACKAGE_STATUSES:
        raise HTTPException(status_code=400, detail="status invalid")
    if "is_active" in payload and not isinstance(payload["is_active"], bool):
        raise HTTPException(status_code=400, detail="is_active must be a boolean")
    try:
        package = package_repo.update_package(db, package_id, payload)
    except SQLAlchemyError:
        db.rollback()
        raise HTTPException(status_code=500, detail="Database error")
    if not package:
        raise HTTPException(status_code=404, detail="Material package not found")
    return ok(package)
