import mimetypes
import shutil
from pathlib import Path
from typing import Any, Dict

from fastapi import APIRouter, Body, Depends, File, HTTPException, UploadFile
from fastapi.responses import FileResponse
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.api.v1.deps import get_current_user, require_platform_admin
from app.api.v1.response import ok
from app.db.session import get_db
from app.repositories import users as user_repo
from app.services.crypto import encrypt_secret
from app.services.user_llm_settings import normalize_llm_base, has_llm_key

router = APIRouter(prefix="/users", tags=["user-settings"])

UPLOAD_ROOT = Path(__file__).resolve().parents[3] / "uploads" / "users"


def _ensure_user_dir(user_id: str) -> Path:
    path = UPLOAD_ROOT / user_id
    path.mkdir(parents=True, exist_ok=True)
    return path


def _safe_filename(name: str) -> str:
    cleaned = Path(name).name
    return cleaned or "avatar"


def _guess_extension(filename: str, content_type: str | None) -> str:
    ext = Path(filename).suffix.lower()
    if ext:
        return ext
    if content_type:
        guessed = mimetypes.guess_extension(content_type)
        if guessed:
            return guessed
    return ".png"


@router.get("/me/llm-settings")
async def get_llm_settings(
    current_user: object = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    user = user_repo.get_user(db, getattr(current_user, "id", ""))
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return ok(
        {
            "api_base": user.llm_api_base or "",
            "has_api_key": has_llm_key(user),
        }
    )


@router.get("/me/profile")
async def get_profile(
    current_user: object = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    user = user_repo.get_user(db, getattr(current_user, "id", ""))
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return ok(
        {
            "id": user.id,
            "username": user.username,
            "display_name": user.display_name or user.username,
            "avatar_url": user.avatar_url or "",
        }
    )


@router.put("/me/profile")
async def update_profile(
    payload: Dict[str, Any] = Body(default_factory=dict),
    current_user: object = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    display_name = payload.get("display_name")
    avatar_url = payload.get("avatar_url")
    if display_name is not None and not isinstance(display_name, str):
        raise HTTPException(status_code=400, detail="display_name must be a string")
    if avatar_url is not None and not isinstance(avatar_url, str):
        raise HTTPException(status_code=400, detail="avatar_url must be a string")

    user = user_repo.get_user(db, getattr(current_user, "id", ""))
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    display_name = display_name.strip() if isinstance(display_name, str) else None
    avatar_url = avatar_url.strip() if isinstance(avatar_url, str) else None

    try:
        updated = user_repo.update_user_profile(db, user, display_name=display_name, avatar_url=avatar_url)
    except SQLAlchemyError:
        db.rollback()
        raise HTTPException(status_code=500, detail="Database error")

    return ok(updated)


@router.post("/me/avatar")
async def upload_avatar(
    file: UploadFile = File(...),
    current_user: object = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    if not file.filename:
        raise HTTPException(status_code=400, detail="filename required")
    user = user_repo.get_user(db, getattr(current_user, "id", ""))
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    safe_name = _safe_filename(file.filename)
    avatar_id = user.id[:8]
    ext = _guess_extension(safe_name, file.content_type)
    stored_name = f"{avatar_id}{ext}"
    stored_path = _ensure_user_dir(user.id) / stored_name

    try:
        with stored_path.open("wb") as target:
            shutil.copyfileobj(file.file, target)
    except Exception:
        raise HTTPException(status_code=500, detail="File upload failed")

    avatar_url = f"/api/v1/users/avatar/{user.id}/{stored_name}"
    try:
        updated = user_repo.update_user_profile(db, user, avatar_url=avatar_url)
    except SQLAlchemyError:
        db.rollback()
        raise HTTPException(status_code=500, detail="Database error")
    return ok({"avatar_url": avatar_url, "user": updated})


@router.get("/avatar/{user_id}/{filename}")
async def get_avatar(
    user_id: str,
    filename: str,
) -> FileResponse:
    safe_name = _safe_filename(filename)
    path = _ensure_user_dir(user_id) / safe_name
    if not path.exists():
        raise HTTPException(status_code=404, detail="File not found")
    return FileResponse(path, filename=safe_name)


@router.put("/{user_id}/profile")
async def update_user_profile_by_admin(
    user_id: str,
    payload: Dict[str, Any] = Body(default_factory=dict),
    current_user: object = Depends(require_platform_admin),
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    display_name = payload.get("display_name")
    avatar_url = payload.get("avatar_url")
    if display_name is not None and not isinstance(display_name, str):
        raise HTTPException(status_code=400, detail="display_name must be a string")
    if avatar_url is not None and not isinstance(avatar_url, str):
        raise HTTPException(status_code=400, detail="avatar_url must be a string")
    user = user_repo.get_user(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    display_name = display_name.strip() if isinstance(display_name, str) else None
    avatar_url = avatar_url.strip() if isinstance(avatar_url, str) else None
    try:
        updated = user_repo.update_user_profile(db, user, display_name=display_name, avatar_url=avatar_url)
    except SQLAlchemyError:
        db.rollback()
        raise HTTPException(status_code=500, detail="Database error")
    return ok(updated)


@router.post("/{user_id}/avatar")
async def upload_avatar_by_admin(
    user_id: str,
    file: UploadFile = File(...),
    current_user: object = Depends(require_platform_admin),
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    if not file.filename:
        raise HTTPException(status_code=400, detail="filename required")
    user = user_repo.get_user(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    safe_name = _safe_filename(file.filename)
    avatar_id = user.id[:8]
    ext = _guess_extension(safe_name, file.content_type)
    stored_name = f"{avatar_id}{ext}"
    stored_path = _ensure_user_dir(user.id) / stored_name

    try:
        with stored_path.open("wb") as target:
            shutil.copyfileobj(file.file, target)
    except Exception:
        raise HTTPException(status_code=500, detail="File upload failed")

    avatar_url = f"/api/v1/users/avatar/{user.id}/{stored_name}"
    try:
        updated = user_repo.update_user_profile(db, user, avatar_url=avatar_url)
    except SQLAlchemyError:
        db.rollback()
        raise HTTPException(status_code=500, detail="Database error")
    return ok({"avatar_url": avatar_url, "user": updated})


@router.put("/me/llm-settings")
async def update_llm_settings(
    payload: Dict[str, Any] = Body(default_factory=dict),
    current_user: object = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    api_base = payload.get("api_base")
    api_key = payload.get("api_key")
    if not isinstance(api_base, str) or not api_base.strip():
        raise HTTPException(status_code=400, detail="api_base required")
    try:
        normalized_base = normalize_llm_base(api_base)
    except ValueError:
        raise HTTPException(status_code=400, detail="api_base not supported")
    if api_key is not None and not isinstance(api_key, str):
        raise HTTPException(status_code=400, detail="api_key must be a string")

    user = user_repo.get_user(db, getattr(current_user, "id", ""))
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    encrypted = None
    if isinstance(api_key, str) and api_key.strip():
        encrypted = encrypt_secret(api_key.strip())
    elif not has_llm_key(user):
        raise HTTPException(status_code=400, detail="api_key required")

    try:
        user_repo.update_user_llm_settings(db, user, normalized_base, encrypted)
    except RuntimeError as exc:
        raise HTTPException(status_code=500, detail=str(exc))
    except SQLAlchemyError:
        db.rollback()
        raise HTTPException(status_code=500, detail="Database error")

    return ok({"api_base": normalized_base, "has_api_key": True})
