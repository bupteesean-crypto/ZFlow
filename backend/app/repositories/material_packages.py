from typing import Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.events import emit_event
from app.db.models import MaterialPackage, Project, to_material_package_dict, utc_now
from app.store import new_id


def list_packages_for_project(db: Session, project_id: str) -> list[dict]:
    items = (
        db.query(MaterialPackage)
        .filter(MaterialPackage.project_id == project_id)
        .order_by(MaterialPackage.created_at.desc())
        .all()
    )
    return [to_material_package_dict(item) for item in items]


def create_package(
    db: Session,
    project_id: str,
    package_name: str,
    status: str,
    materials: dict,
) -> dict:
    project = db.execute(select(Project).where(Project.id == project_id)).scalar_one_or_none()
    if not project:
        raise ValueError("Project not found")
    now = utc_now()
    db.query(MaterialPackage).filter(MaterialPackage.project_id == project_id).update(
        {MaterialPackage.is_active: False},
        synchronize_session=False,
    )
    package = MaterialPackage(
        id=new_id(),
        project_id=project_id,
        parent_id=None,
        package_name=package_name,
        status=status,
        is_active=True,
        summary=None,
        materials=materials or {},
        generated_at=None,
        created_at=now,
        updated_at=now,
    )
    db.add(package)
    db.commit()
    db.refresh(package)
    emit_event(
        "material_package.created",
        {
            "project_id": project_id,
            "material_package_id": package.id,
            "status": package.status,
        },
    )
    emit_event(
        "material_package.activated",
        {
            "project_id": project_id,
            "material_package_id": package.id,
        },
    )
    return to_material_package_dict(package)


def get_package(db: Session, package_id: str) -> Optional[dict]:
    package = db.execute(select(MaterialPackage).where(MaterialPackage.id == package_id)).scalar_one_or_none()
    return to_material_package_dict(package) if package else None


def update_package(db: Session, package_id: str, payload: dict) -> Optional[dict]:
    package = db.execute(select(MaterialPackage).where(MaterialPackage.id == package_id)).scalar_one_or_none()
    if not package:
        return None
    was_active = package.is_active
    was_completed = package.status == "completed"
    if payload.get("is_active") is True:
        db.query(MaterialPackage).filter(
            MaterialPackage.project_id == package.project_id,
            MaterialPackage.id != package.id,
        ).update({MaterialPackage.is_active: False}, synchronize_session=False)
    if payload.get("status") == "completed" and "generated_at" not in payload:
        payload["generated_at"] = utc_now()
    for key in ["package_name", "summary", "status", "materials", "generated_at", "is_active"]:
        if key in payload:
            setattr(package, key, payload[key])
    package.updated_at = utc_now()
    db.commit()
    db.refresh(package)
    if payload.get("is_active") is True and not was_active:
        emit_event(
            "material_package.activated",
            {
                "project_id": package.project_id,
                "material_package_id": package.id,
            },
        )
    if payload.get("status") == "completed" and not was_completed:
        emit_event(
            "material_package.completed",
            {
                "project_id": package.project_id,
                "material_package_id": package.id,
            },
        )
    return to_material_package_dict(package)
