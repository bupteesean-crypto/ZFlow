from __future__ import annotations

import logging
import mimetypes
from pathlib import Path
from typing import Any, Dict

from fastapi import APIRouter, Body, Depends, File, Form, HTTPException, Query, UploadFile
from fastapi.responses import FileResponse
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.api.v1.response import ok
from app.db.session import get_db
from app.repositories import material_packages as package_repo
from app.repositories import projects as project_repo
from app.services.music_service import read_wav_duration, synthesize_silent_wav
from app.store import new_id, utc_now

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/music", tags=["music"])

UPLOAD_ROOT = Path(__file__).resolve().parents[3] / "uploads" / "music"

MUSIC_LIBRARY = [
    {
        "id": "lib_relax",
        "title": "自然治愈",
        "duration_sec": 145,
        "cover_style": "linear-gradient(135deg, #d9f99d, #a7f3d0)",
    },
    {
        "id": "lib_energy",
        "title": "动感节奏",
        "duration_sec": 155,
        "cover_style": "linear-gradient(135deg, #fca5a5, #fcd34d)",
    },
    {
        "id": "lib_mellow",
        "title": "青涩夏风",
        "duration_sec": 140,
        "cover_style": "linear-gradient(135deg, #93c5fd, #fbcfe8)",
    },
    {
        "id": "lib_regret",
        "title": "伤感遗憾",
        "duration_sec": 160,
        "cover_style": "linear-gradient(135deg, #94a3b8, #cbd5f5)",
    },
    {
        "id": "lib_city",
        "title": "城市夜色",
        "duration_sec": 150,
        "cover_style": "linear-gradient(135deg, #a78bfa, #60a5fa)",
    },
]


def _ensure_project(db: Session, project_id: str) -> dict:
    project = project_repo.get_project(db, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return project


def _music_path(project_id: str, music_id: str, ext: str = ".wav") -> Path:
    return UPLOAD_ROOT / project_id / f"{music_id}{ext}"


def _ensure_library_files() -> None:
    for item in MUSIC_LIBRARY:
        music_id = item["id"]
        duration = float(item.get("duration_sec") or 120)
        path = _music_path("library", music_id)
        if not path.exists():
            synthesize_silent_wav(duration, path)


def _load_project_music(metadata: dict) -> list[dict]:
    items = metadata.get("music_assets")
    if isinstance(items, list):
        return [item for item in items if isinstance(item, dict)]
    return []


def _store_project_music(db: Session, project_id: str, metadata: dict, items: list[dict]) -> None:
    metadata["music_assets"] = items
    project_repo.update_project(db, project_id, {"metadata": metadata})


def _resolve_music_asset(project_music: list[dict], music_id: str) -> dict | None:
    for item in project_music:
        if item.get("id") == music_id:
            return item
    for item in MUSIC_LIBRARY:
        if item.get("id") == music_id:
            asset = item.copy()
            asset.update(
                {
                    "url": f"/api/v1/music/audio/library/{item['id']}",
                    "source": "library",
                }
            )
            return asset
    return None


@router.get("/library")
async def list_music_library(
    project_id: str = Query(...),
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    if not project_id.strip():
        raise HTTPException(status_code=400, detail="project_id required")
    try:
        project = _ensure_project(db, project_id)
    except SQLAlchemyError:
        db.rollback()
        raise HTTPException(status_code=500, detail="Database error")
    _ensure_library_files()
    metadata = project.get("metadata") if isinstance(project.get("metadata"), dict) else {}
    project_music = _load_project_music(metadata)
    library_items = [
        {
            **item,
            "url": f"/api/v1/music/audio/library/{item['id']}",
            "source": "library",
        }
        for item in MUSIC_LIBRARY
    ]
    return ok({"list": library_items + project_music})


@router.get("/audio/{project_id}/{music_id}")
async def fetch_music_audio(
    project_id: str,
    music_id: str,
    db: Session = Depends(get_db),
) -> FileResponse:
    if not project_id.strip() or not music_id.strip():
        raise HTTPException(status_code=400, detail="project_id and music_id required")
    if project_id != "library":
        try:
            _ensure_project(db, project_id)
        except SQLAlchemyError:
            db.rollback()
            raise HTTPException(status_code=500, detail="Database error")
    else:
        _ensure_library_files()
    path = _music_path(project_id, music_id)
    if not path.exists():
        raise HTTPException(status_code=404, detail="Audio not found")
    return FileResponse(str(path), filename=f"{music_id}.wav")


@router.post("/generate")
async def generate_music(
    payload: Dict[str, Any] = Body(default_factory=dict),
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    project_id = payload.get("project_id")
    prompt = payload.get("prompt")
    if not isinstance(project_id, str) or not project_id.strip():
        raise HTTPException(status_code=400, detail="project_id required")
    if not isinstance(prompt, str) or not prompt.strip():
        raise HTTPException(status_code=400, detail="prompt required")
    try:
        project = _ensure_project(db, project_id)
    except SQLAlchemyError:
        db.rollback()
        raise HTTPException(status_code=500, detail="Database error")

    music_id = new_id()
    duration_sec = float(payload.get("duration_sec") or 150)
    path = _music_path(project_id, music_id)
    synthesize_silent_wav(duration_sec, path)
    title = prompt.strip()[:10] + " BGM"
    cover_style = "linear-gradient(135deg, #c7d2fe, #fbcfe8)"
    asset = {
        "id": music_id,
        "title": title,
        "prompt": prompt.strip(),
        "url": f"/api/v1/music/audio/{project_id}/{music_id}",
        "duration_sec": duration_sec,
        "cover_style": cover_style,
        "source": "ai",
        "created_at": utc_now(),
    }

    metadata = project.get("metadata") if isinstance(project.get("metadata"), dict) else {}
    items = _load_project_music(metadata)
    items.insert(0, asset)
    try:
        _store_project_music(db, project_id, metadata, items)
    except SQLAlchemyError:
        db.rollback()
        raise HTTPException(status_code=500, detail="Database error")
    return ok({"music": asset})


@router.post("/upload")
async def upload_music(
    project_id: str = Form(...),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    if not project_id.strip():
        raise HTTPException(status_code=400, detail="project_id required")
    if not file.filename:
        raise HTTPException(status_code=400, detail="filename required")
    try:
        project = _ensure_project(db, project_id)
    except SQLAlchemyError:
        db.rollback()
        raise HTTPException(status_code=500, detail="Database error")

    music_id = new_id()
    suffix = Path(file.filename).suffix.lower() or ".wav"
    safe_suffix = suffix if suffix in {".wav", ".mp3", ".aac", ".m4a"} else ".wav"
    stored_path = _music_path(project_id, music_id, safe_suffix)
    stored_path.parent.mkdir(parents=True, exist_ok=True)
    try:
        content = await file.read()
        stored_path.write_bytes(content)
    except Exception:
        logger.exception("Failed to save music upload")
        raise HTTPException(status_code=500, detail="File upload failed")

    duration_sec = read_wav_duration(stored_path) if safe_suffix == ".wav" else None
    title = Path(file.filename).stem
    content_type = file.content_type or mimetypes.guess_type(file.filename)[0] or "audio/mpeg"
    asset = {
        "id": music_id,
        "title": title,
        "url": f"/api/v1/music/audio/{project_id}/{music_id}",
        "duration_sec": duration_sec,
        "cover_style": "linear-gradient(135deg, #f8fafc, #e2e8f0)",
        "source": "upload",
        "content_type": content_type,
        "created_at": utc_now(),
    }

    metadata = project.get("metadata") if isinstance(project.get("metadata"), dict) else {}
    items = _load_project_music(metadata)
    items.insert(0, asset)
    try:
        _store_project_music(db, project_id, metadata, items)
    except SQLAlchemyError:
        db.rollback()
        raise HTTPException(status_code=500, detail="Database error")
    return ok({"music": asset})


@router.post("/storyboard/{package_id}/{shot_id}/apply")
async def apply_storyboard_music(
    package_id: str,
    shot_id: str,
    payload: Dict[str, Any] = Body(default_factory=dict),
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    if not package_id.strip() or not shot_id.strip():
        raise HTTPException(status_code=400, detail="package_id and shot_id required")
    music_id = payload.get("music_id")
    if not isinstance(music_id, str) or not music_id.strip():
        raise HTTPException(status_code=400, detail="music_id required")
    volume = payload.get("volume", 35)
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

    try:
        project = _ensure_project(db, project_id)
    except SQLAlchemyError:
        db.rollback()
        raise HTTPException(status_code=500, detail="Database error")

    metadata = project.get("metadata") if isinstance(project.get("metadata"), dict) else {}
    project_music = _load_project_music(metadata)
    asset = _resolve_music_asset(project_music, music_id)
    if not asset:
        raise HTTPException(status_code=404, detail="Music not found")

    materials = package.get("materials") if isinstance(package.get("materials"), dict) else {}
    pkg_meta = materials.get("metadata") if isinstance(materials.get("metadata"), dict) else {}
    bindings = pkg_meta.get("music_bindings") if isinstance(pkg_meta.get("music_bindings"), list) else []
    bindings = [item for item in bindings if isinstance(item, dict)]
    for item in bindings:
        if item.get("shot_id") == shot_id and item.get("type") == "storyboard_music":
            item["is_active"] = False

    binding = {
        "id": new_id(),
        "type": "storyboard_music",
        "shot_id": shot_id,
        "music_id": asset.get("id"),
        "music_title": asset.get("title"),
        "music_url": asset.get("url"),
        "duration_sec": asset.get("duration_sec"),
        "cover_style": asset.get("cover_style"),
        "volume": volume,
        "is_active": True,
        "created_at": utc_now(),
    }
    bindings.append(binding)
    pkg_meta["music_bindings"] = bindings
    materials["metadata"] = pkg_meta

    try:
        package_repo.update_package(db, package_id, {"materials": materials})
    except SQLAlchemyError:
        db.rollback()
        raise HTTPException(status_code=500, detail="Database error")
    return ok({"binding": binding, "material_package_id": package_id})
