from datetime import datetime, timezone
from typing import Any

from sqlalchemy import JSON, Boolean, Column, DateTime, ForeignKey, Integer, String, Text

from app.db.base import Base


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class Project(Base):
    __tablename__ = "projects"

    id = Column(String(36), primary_key=True, index=True)
    team_space_id = Column(String(36), nullable=True)
    name = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    status = Column(String(20), nullable=False, default="draft")
    stage = Column(String(20), nullable=False, default="input")
    progress = Column(Integer, nullable=False, default=0)
    tags = Column(JSON, nullable=False, default=list)
    input_config = Column(JSON, nullable=False, default=dict)
    thumbnail_url = Column(String(500), nullable=True)
    last_material_package_id = Column(String(36), nullable=True)
    metadata_json = Column("metadata", JSON, nullable=False, default=dict)
    created_at = Column(DateTime(timezone=True), nullable=False, default=utc_now)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=utc_now)


class MaterialPackage(Base):
    __tablename__ = "material_packages"

    id = Column(String(36), primary_key=True, index=True)
    project_id = Column(String(36), ForeignKey("projects.id"), nullable=False, index=True)
    parent_id = Column(String(36), nullable=True)
    package_name = Column(String(200), nullable=False)
    status = Column(String(20), nullable=False, default="generating")
    is_active = Column(Boolean, nullable=False, default=True)
    summary = Column(Text, nullable=True)
    materials = Column(JSON, nullable=False, default=dict)
    generated_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=utc_now)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=utc_now)


def to_project_dict(project: Project) -> dict[str, Any]:
    return {
        "id": project.id,
        "user_id": getattr(project, "user_id", None),
        "team_space_id": project.team_space_id,
        "name": project.name,
        "description": project.description,
        "status": project.status,
        "stage": project.stage,
        "progress": project.progress,
        "tags": project.tags or [],
        "input_config": project.input_config or {},
        "thumbnail_url": project.thumbnail_url,
        "last_material_package_id": project.last_material_package_id,
        "metadata": project.metadata_json or {},
        "created_at": project.created_at.isoformat() if project.created_at else None,
        "updated_at": project.updated_at.isoformat() if project.updated_at else None,
    }


def to_material_package_dict(package: MaterialPackage) -> dict[str, Any]:
    return {
        "id": package.id,
        "project_id": package.project_id,
        "parent_id": package.parent_id,
        "package_name": package.package_name,
        "status": package.status,
        "is_active": package.is_active,
        "summary": package.summary,
        "materials": package.materials or {},
        "generated_at": package.generated_at.isoformat() if package.generated_at else None,
        "created_at": package.created_at.isoformat() if package.created_at else None,
        "updated_at": package.updated_at.isoformat() if package.updated_at else None,
    }
