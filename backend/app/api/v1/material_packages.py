from typing import Any, Dict, List

from fastapi import APIRouter, Body, HTTPException

from app.api.v1.response import ok
from app.store import MATERIAL_PACKAGES, PROJECTS, utc_now

router = APIRouter(tags=["material-packages"])


@router.get("/projects/{project_id}/material-packages")
async def list_material_packages(project_id: str) -> Dict[str, Any]:
    if project_id not in PROJECTS:
        raise HTTPException(status_code=404, detail="Project not found")
    items: List[Dict[str, Any]] = [
        pkg for pkg in MATERIAL_PACKAGES.values() if pkg["project_id"] == project_id
    ]
    return ok({"list": items, "total": len(items)})


@router.get("/material-packages/{package_id}")
async def get_material_package(package_id: str) -> Dict[str, Any]:
    package = MATERIAL_PACKAGES.get(package_id)
    if not package:
        raise HTTPException(status_code=404, detail="Material package not found")
    return ok(package)


@router.put("/material-packages/{package_id}")
async def update_material_package(
    package_id: str,
    payload: Dict[str, Any] = Body(default_factory=dict),
) -> Dict[str, Any]:
    package = MATERIAL_PACKAGES.get(package_id)
    if not package:
        raise HTTPException(status_code=404, detail="Material package not found")

    for key in ["package_name", "summary"]:
        if key in payload:
            package[key] = payload[key]
    package["updated_at"] = utc_now()
    return ok(package)
