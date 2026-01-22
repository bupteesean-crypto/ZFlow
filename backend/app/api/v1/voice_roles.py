from typing import Any, Dict

import logging

from fastapi import APIRouter, Body, Depends, HTTPException, Query
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.api.v1.response import ok
from app.db.session import get_db
from app.repositories import projects as project_repo
from app.repositories import voice_roles as voice_role_repo

router = APIRouter(prefix="/voice-roles", tags=["voice-roles"])
logger = logging.getLogger(__name__)


@router.get("")
async def list_voice_roles(
    project_id: str = Query(...),
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
    try:
        roles = voice_role_repo.list_voice_roles(db, project_id)
    except SQLAlchemyError:
        db.rollback()
        raise HTTPException(status_code=500, detail="Database error")
    return ok({"list": roles})


@router.post("")
async def create_voice_role(
    payload: Dict[str, Any] = Body(default_factory=dict),
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    project_id = payload.get("project_id")
    name = payload.get("name")
    if not isinstance(project_id, str) or not project_id.strip():
        raise HTTPException(status_code=400, detail="project_id required")
    if not isinstance(name, str) or not name.strip():
        raise HTTPException(status_code=400, detail="name required")
    voice_id = payload.get("voice_id")
    if voice_id is not None and not isinstance(voice_id, str):
        raise HTTPException(status_code=400, detail="voice_id must be a string")
    emotion = payload.get("emotion")
    if emotion is not None and not isinstance(emotion, str):
        raise HTTPException(status_code=400, detail="emotion must be a string")
    volume = payload.get("volume", 100)
    speed = payload.get("speed", 1.0)
    if not isinstance(volume, int) or volume < 0 or volume > 100:
        raise HTTPException(status_code=400, detail="volume must be 0-100")
    if not isinstance(speed, (int, float)) or speed <= 0:
        raise HTTPException(status_code=400, detail="speed must be > 0")

    try:
        project = project_repo.get_project(db, project_id)
    except SQLAlchemyError:
        db.rollback()
        raise HTTPException(status_code=500, detail="Database error")
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    try:
        role = voice_role_repo.create_voice_role(
            db,
            project_id,
            name=name.strip(),
            voice_id=voice_id.strip() if isinstance(voice_id, str) and voice_id.strip() else None,
            emotion=emotion.strip() if isinstance(emotion, str) and emotion.strip() else None,
            volume=volume,
            speed=float(speed),
            metadata=payload.get("metadata") if isinstance(payload.get("metadata"), dict) else None,
        )
    except SQLAlchemyError:
        db.rollback()
        raise HTTPException(status_code=500, detail="Database error")
    return ok({"role": role})


@router.put("/{role_id}")
async def update_voice_role(
    role_id: str,
    payload: Dict[str, Any] = Body(default_factory=dict),
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    if not role_id.strip():
        raise HTTPException(status_code=400, detail="role_id required")
    if "name" in payload and payload["name"] is not None and not isinstance(payload["name"], str):
        raise HTTPException(status_code=400, detail="name must be a string")
    if "voice_id" in payload and payload["voice_id"] is not None and not isinstance(payload["voice_id"], str):
        raise HTTPException(status_code=400, detail="voice_id must be a string")
    if "emotion" in payload and payload["emotion"] is not None and not isinstance(payload["emotion"], str):
        raise HTTPException(status_code=400, detail="emotion must be a string")
    if "volume" in payload and payload["volume"] is not None:
        volume = payload["volume"]
        if not isinstance(volume, int) or volume < 0 or volume > 100:
            raise HTTPException(status_code=400, detail="volume must be 0-100")
    if "speed" in payload and payload["speed"] is not None:
        speed = payload["speed"]
        if not isinstance(speed, (int, float)) or speed <= 0:
            raise HTTPException(status_code=400, detail="speed must be > 0")
    if "metadata" in payload and payload["metadata"] is not None and not isinstance(payload["metadata"], dict):
        raise HTTPException(status_code=400, detail="metadata must be an object")

    try:
        role = voice_role_repo.update_voice_role(db, role_id, payload)
    except SQLAlchemyError:
        db.rollback()
        raise HTTPException(status_code=500, detail="Database error")
    if not role:
        raise HTTPException(status_code=404, detail="Voice role not found")
    return ok({"role": role})
