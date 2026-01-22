from typing import Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.events import emit_event
from app.db.models import VoiceRole, to_voice_role_dict, utc_now
from app.store import new_id


def list_voice_roles(db: Session, project_id: str) -> list[dict]:
    items = (
        db.execute(select(VoiceRole).where(VoiceRole.project_id == project_id).order_by(VoiceRole.created_at.desc()))
        .scalars()
        .all()
    )
    return [to_voice_role_dict(item) for item in items]


def create_voice_role(
    db: Session,
    project_id: str,
    name: str,
    voice_id: Optional[str] = None,
    emotion: Optional[str] = None,
    volume: int = 100,
    speed: float = 1.0,
    metadata: Optional[dict] = None,
) -> dict:
    now = utc_now()
    role = VoiceRole(
        id=new_id(),
        project_id=project_id,
        name=name,
        voice_id=voice_id,
        emotion=emotion,
        volume=volume,
        speed=speed,
        metadata_json=metadata or {},
        created_at=now,
        updated_at=now,
    )
    db.add(role)
    db.commit()
    db.refresh(role)
    emit_event("voice_role.created", {"role_id": role.id, "project_id": project_id})
    return to_voice_role_dict(role)


def update_voice_role(db: Session, role_id: str, payload: dict) -> Optional[dict]:
    role = db.execute(select(VoiceRole).where(VoiceRole.id == role_id)).scalar_one_or_none()
    if not role:
        return None
    updated_fields = []
    for key in ["name", "voice_id", "emotion", "volume", "speed", "metadata"]:
        if key not in payload:
            continue
        if key == "metadata":
            role.metadata_json = payload[key] or {}
        else:
            setattr(role, key, payload[key])
        updated_fields.append(key)
    role.updated_at = utc_now()
    db.commit()
    db.refresh(role)
    emit_event("voice_role.updated", {"role_id": role.id, "fields": updated_fields})
    return to_voice_role_dict(role)
