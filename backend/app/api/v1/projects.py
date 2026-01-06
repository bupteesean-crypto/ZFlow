from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Body, HTTPException, Query

from app.api.v1.response import ok
from app.store import PROJECTS, new_id, utc_now

router = APIRouter(prefix="/projects", tags=["projects"])


def _default_project(name: Optional[str], space_type: Optional[str], team_space_id: Optional[str]) -> Dict[str, Any]:
    now = utc_now()
    return {
        "id": new_id(),
        "user_id": None,
        "team_space_id": team_space_id,
        "name": name or "Untitled Project",
        "description": None,
        "status": "draft",
        "stage": "input",
        "progress": 0,
        "tags": [],
        "input_config": {},
        "thumbnail_url": None,
        "last_material_package_id": None,
        "metadata": {},
        "updated_at": now,
        "created_at": now,
    }


@router.get("")
async def list_projects(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
) -> Dict[str, Any]:
    items: List[Dict[str, Any]] = list(PROJECTS.values())
    total = len(items)
    start = (page - 1) * page_size
    end = start + page_size
    return ok({"list": items[start:end], "total": total, "page": page, "page_size": page_size})


@router.post("")
async def create_project(payload: Dict[str, Any] = Body(default_factory=dict)) -> Dict[str, Any]:
    project = _default_project(
        payload.get("name"),
        payload.get("space_type"),
        payload.get("team_space_id"),
    )
    PROJECTS[project["id"]] = project
    return ok(project)


@router.get("/{project_id}")
async def get_project(project_id: str) -> Dict[str, Any]:
    project = PROJECTS.get(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return ok(project)


@router.put("/{project_id}")
async def update_project(
    project_id: str,
    payload: Dict[str, Any] = Body(default_factory=dict),
) -> Dict[str, Any]:
    project = PROJECTS.get(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    for key in ["name", "description", "tags"]:
        if key in payload:
            project[key] = payload[key]
    project["updated_at"] = utc_now()
    return ok(project)


@router.delete("/{project_id}")
async def delete_project(project_id: str) -> Dict[str, Any]:
    project = PROJECTS.pop(project_id, None)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return ok({"deleted": True})
