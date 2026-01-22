from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, Dict

from fastapi import APIRouter, Body, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.api.v1.response import ok
from app.db.session import get_db
from app.repositories import material_packages as package_repo
from app.repositories import projects as project_repo
from app.services.tts_service import synthesize_silent_wav
from app.store import new_id, utc_now

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/tts", tags=["tts"])

UPLOAD_ROOT = Path(__file__).resolve().parents[3] / "uploads" / "tts"

VOICE_LIBRARY = [
    {
        "id": "voice_youth_male",
        "name": "真诚青年",
        "gender": "男性",
        "age_group": "青年",
        "locale": "普通话",
        "description": "清晰自然，适合旁白",
    },
    {
        "id": "voice_gentle_female",
        "name": "温柔女生",
        "gender": "女性",
        "age_group": "青年",
        "locale": "普通话",
        "description": "轻柔温暖，适合情感叙述",
    },
    {
        "id": "voice_calm_male",
        "name": "稳重男声",
        "gender": "男性",
        "age_group": "成年",
        "locale": "普通话",
        "description": "低沉稳健，适合讲述类视频",
    },
]


def _ensure_project(db: Session, project_id: str) -> None:
    project = project_repo.get_project(db, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")


def _audio_file_path(project_id: str, audio_id: str) -> Path:
    return UPLOAD_ROOT / project_id / f"{audio_id}.wav"


@router.get("/voices")
async def list_voices() -> Dict[str, Any]:
    return ok({"list": VOICE_LIBRARY})


@router.get("/audio/{project_id}/{audio_id}")
async def fetch_audio(project_id: str, audio_id: str, db: Session = Depends(get_db)) -> FileResponse:
    if not project_id.strip() or not audio_id.strip():
        raise HTTPException(status_code=400, detail="project_id and audio_id required")
    try:
        _ensure_project(db, project_id)
    except SQLAlchemyError:
        db.rollback()
        raise HTTPException(status_code=500, detail="Database error")
    path = _audio_file_path(project_id, audio_id)
    if not path.exists():
        raise HTTPException(status_code=404, detail="Audio not found")
    return FileResponse(str(path), filename=f"{audio_id}.wav")


@router.post("/preview")
async def preview_tts(
    payload: Dict[str, Any] = Body(default_factory=dict),
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    project_id = payload.get("project_id")
    text = payload.get("text")
    if not isinstance(project_id, str) or not project_id.strip():
        raise HTTPException(status_code=400, detail="project_id required")
    if not isinstance(text, str) or not text.strip():
        raise HTTPException(status_code=400, detail="text required")
    voice_id = payload.get("voice_id")
    emotion = payload.get("emotion")
    speed = payload.get("speed", 1.0)
    volume = payload.get("volume", 100)
    if voice_id is not None and not isinstance(voice_id, str):
        raise HTTPException(status_code=400, detail="voice_id must be a string")
    if emotion is not None and not isinstance(emotion, str):
        raise HTTPException(status_code=400, detail="emotion must be a string")
    if not isinstance(speed, (int, float)) or speed <= 0:
        raise HTTPException(status_code=400, detail="speed must be > 0")
    if not isinstance(volume, int) or volume < 0 or volume > 100:
        raise HTTPException(status_code=400, detail="volume must be 0-100")

    try:
        _ensure_project(db, project_id)
    except SQLAlchemyError:
        db.rollback()
        raise HTTPException(status_code=500, detail="Database error")

    audio_id = new_id()
    output_path = _audio_file_path(project_id, audio_id)
    duration_sec = synthesize_silent_wav(text, float(speed), output_path)
    return ok(
        {
            "audio": {
                "id": audio_id,
                "url": f"/api/v1/tts/audio/{project_id}/{audio_id}",
                "duration_sec": duration_sec,
                "text": text.strip(),
                "voice_id": voice_id.strip() if isinstance(voice_id, str) and voice_id.strip() else None,
                "emotion": emotion.strip() if isinstance(emotion, str) and emotion.strip() else None,
                "speed": float(speed),
                "volume": volume,
            }
        }
    )


@router.post("/storyboard/{package_id}/{shot_id}")
async def generate_storyboard_audio(
    package_id: str,
    shot_id: str,
    payload: Dict[str, Any] = Body(default_factory=dict),
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    if not package_id.strip() or not shot_id.strip():
        raise HTTPException(status_code=400, detail="package_id and shot_id required")
    text = payload.get("text")
    if not isinstance(text, str) or not text.strip():
        raise HTTPException(status_code=400, detail="text required")
    voice_id = payload.get("voice_id")
    emotion = payload.get("emotion")
    speed = payload.get("speed", 1.0)
    volume = payload.get("volume", 100)
    role_id = payload.get("role_id")
    if voice_id is not None and not isinstance(voice_id, str):
        raise HTTPException(status_code=400, detail="voice_id must be a string")
    if emotion is not None and not isinstance(emotion, str):
        raise HTTPException(status_code=400, detail="emotion must be a string")
    if role_id is not None and not isinstance(role_id, str):
        raise HTTPException(status_code=400, detail="role_id must be a string")
    if not isinstance(speed, (int, float)) or speed <= 0:
        raise HTTPException(status_code=400, detail="speed must be > 0")
    if not isinstance(volume, int) or volume < 0 or volume > 100:
        raise HTTPException(status_code=400, detail="volume must be 0-100")

    try:
        package = package_repo.get_package(db, package_id)
    except SQLAlchemyError:
        db.rollback()
        raise HTTPException(status_code=500, detail="Database error")
    if not package:
        raise HTTPException(status_code=404, detail="Material package not found")

    project_id = package.get("project_id")
    if not isinstance(project_id, str) or not project_id.strip():
        raise HTTPException(status_code=400, detail="project_id missing")

    audio_id = new_id()
    output_path = _audio_file_path(project_id, audio_id)
    duration_sec = synthesize_silent_wav(text, float(speed), output_path)

    materials = package.get("materials") if isinstance(package.get("materials"), dict) else {}
    metadata = materials.get("metadata") if isinstance(materials.get("metadata"), dict) else {}
    audios = metadata.get("audios") if isinstance(metadata.get("audios"), list) else []
    audios = [audio for audio in audios if isinstance(audio, dict)]
    for audio in audios:
        if audio.get("type") == "storyboard_audio" and audio.get("shot_id") == shot_id:
            audio["is_active"] = False

    audio_item = {
        "id": audio_id,
        "type": "storyboard_audio",
        "shot_id": shot_id,
        "url": f"/api/v1/tts/audio/{project_id}/{audio_id}",
        "text": text.strip(),
        "voice_id": voice_id.strip() if isinstance(voice_id, str) and voice_id.strip() else None,
        "emotion": emotion.strip() if isinstance(emotion, str) and emotion.strip() else None,
        "speed": float(speed),
        "volume": volume,
        "role_id": role_id.strip() if isinstance(role_id, str) and role_id.strip() else None,
        "duration_sec": duration_sec,
        "is_active": True,
        "created_at": utc_now(),
    }
    audios.append(audio_item)
    metadata["audios"] = audios
    materials["metadata"] = metadata

    try:
        package_repo.update_package(db, package_id, {"materials": materials})
    except SQLAlchemyError:
        db.rollback()
        raise HTTPException(status_code=500, detail="Database error")

    return ok({"audio": audio_item, "material_package_id": package_id})
