from app.db.base import Base
from sqlalchemy import JSON, Boolean, Column, DateTime, ForeignKey, String
from sqlalchemy.sql import func


class MaterialPackage(Base):
    __tablename__ = "material_packages"

    id = Column(String, primary_key=True)
    project_id = Column(String, ForeignKey("projects.id"), nullable=False)

    package_name = Column(String, nullable=False)
    status = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)

    materials = Column(JSON, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )
