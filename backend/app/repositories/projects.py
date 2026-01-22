from typing import Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.events import emit_event
from app.db.models import MaterialPackage, Project, to_project_dict, utc_now
from app.store import new_id


def list_projects(db: Session, page: int, page_size: int) -> tuple[list[dict], int]:
    total = db.query(Project).count()
    items = (
        db.query(Project)
        .order_by(Project.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )
    return [to_project_dict(item) for item in items], total


def create_project(
    db: Session,
    name: Optional[str],
    space_type: Optional[str],
    team_space_id: Optional[str],
) -> dict:
    now = utc_now()
    project = Project(
        id=new_id(),
        name=name or "Untitled Project",
        team_space_id=team_space_id,
        status="draft",
        stage="input",
        progress=0,
        tags=[],
        input_config={},
        thumbnail_url=None,
        last_material_package_id=None,
        metadata_json={"space_type": space_type or "personal"},
        created_at=now,
        updated_at=now,
    )
    db.add(project)
    db.commit()
    db.refresh(project)
    emit_event(
        "project.created",
        {"project_id": project.id, "name": project.name, "status": project.status},
    )
    return to_project_dict(project)


def get_project(db: Session, project_id: str) -> Optional[dict]:
    project = db.execute(select(Project).where(Project.id == project_id)).scalar_one_or_none()
    return to_project_dict(project) if project else None


def update_project(db: Session, project_id: str, payload: dict) -> Optional[dict]:
    project = db.execute(select(Project).where(Project.id == project_id)).scalar_one_or_none()
    if not project:
        return None
    updated_fields = []
    for key in [
        "name",
        "description",
        "tags",
        "status",
        "stage",
        "progress",
        "last_material_package_id",
        "input_config",
        "metadata",
    ]:
        if key in payload:
            if key == "metadata":
                project.metadata_json = payload[key]
            elif key == "input_config":
                project.input_config = payload[key]
            else:
                setattr(project, key, payload[key])
            updated_fields.append(key)
    project.updated_at = utc_now()
    db.commit()
    db.refresh(project)
    emit_event(
        "project.updated",
        {"project_id": project.id, "fields": updated_fields},
    )
    return to_project_dict(project)


def delete_project(db: Session, project_id: str) -> bool:
    project = db.execute(select(Project).where(Project.id == project_id)).scalar_one_or_none()
    if not project:
        return False
    db.query(MaterialPackage).filter(MaterialPackage.project_id == project_id).delete(synchronize_session=False)
    db.delete(project)
    db.commit()
    emit_event("project.deleted", {"project_id": project_id})
    return True
