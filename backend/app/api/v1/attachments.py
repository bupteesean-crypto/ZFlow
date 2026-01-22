from __future__ import annotations

import logging
import mimetypes
import shutil
from pathlib import Path
from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.api.v1.response import ok
from app.db.session import get_db
from app.repositories import projects as project_repo
from app.store import new_id, utc_now

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/projects", tags=["attachments"])

UPLOAD_ROOT = Path(__file__).resolve().parents[3] / "uploads"
MAX_TEXT_CHARS = 20000


def _ensure_upload_dir(project_id: str) -> Path:
    path = UPLOAD_ROOT / project_id
    path.mkdir(parents=True, exist_ok=True)
    return path


def _safe_filename(name: str) -> str:
    cleaned = Path(name).name
    return cleaned or "upload"


def _guess_category(content_type: str, filename: str) -> str:
    if content_type.startswith("image/"):
        return "image"
    if content_type.startswith("audio/"):
        return "audio"
    if content_type.startswith("video/"):
        return "video"
    ext = Path(filename).suffix.lower()
    if ext in {".pdf", ".doc", ".docx", ".txt", ".md", ".csv", ".json"}:
        return "document"
    return "document"


def _read_text_file(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return ""


def _extract_text_from_pdf(path: Path) -> str:
    try:
        import PyPDF2  # type: ignore
    except Exception:
        return ""
    try:
        reader = PyPDF2.PdfReader(str(path))
        parts = []
        for page in reader.pages:
            text = page.extract_text() if page else ""
            if text:
                parts.append(text)
        return "\n".join(parts)
    except Exception:
        logger.exception("Failed to parse PDF")
        return ""


def _extract_text_from_docx(path: Path) -> str:
    try:
        import docx  # type: ignore
    except Exception:
        return ""
    try:
        document = docx.Document(str(path))
        return "\n".join([para.text for para in document.paragraphs if para.text])
    except Exception:
        logger.exception("Failed to parse DOCX")
        return ""


def _extract_text(path: Path, content_type: str, filename: str) -> tuple[str, str]:
    ext = path.suffix.lower()
    if content_type.startswith("text/") or ext in {".txt", ".md", ".csv", ".json"}:
        text = _read_text_file(path)
        return text, "ok" if text else "empty"
    if ext == ".pdf":
        text = _extract_text_from_pdf(path)
        return text, "ok" if text else "unsupported"
    if ext == ".docx":
        text = _extract_text_from_docx(path)
        return text, "ok" if text else "unsupported"
    return "", "skipped"


def _extract_image_meta(path: Path) -> dict:
    try:
        from PIL import Image  # type: ignore
    except Exception:
        return {}
    try:
        with Image.open(path) as image:
            width, height = image.size
            return {"width": width, "height": height}
    except Exception:
        logger.exception("Failed to parse image")
        return {}


def _ensure_attachments(metadata: dict) -> list[dict]:
    items = metadata.get("attachments")
    if isinstance(items, list):
        return items
    items = []
    metadata["attachments"] = items
    return items


def _get_project(db: Session, project_id: str) -> Optional[dict]:
    return project_repo.get_project(db, project_id)


@router.get("/{project_id}/attachments")
async def list_attachments(project_id: str, db: Session = Depends(get_db)) -> Dict[str, Any]:
    if not project_id.strip():
        raise HTTPException(status_code=400, detail="project_id required")
    try:
        project = _get_project(db, project_id)
    except SQLAlchemyError:
        db.rollback()
        raise HTTPException(status_code=500, detail="Database error")
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    metadata = project.get("metadata") if isinstance(project.get("metadata"), dict) else {}
    attachments = metadata.get("attachments") if isinstance(metadata.get("attachments"), list) else []
    return ok({"list": attachments})


@router.post("/{project_id}/attachments")
async def upload_attachment(
    project_id: str,
    file: UploadFile = File(...),
    label: str = Form(""),
    bind_type: str = Form(""),
    tags: str = Form(""),
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    if not project_id.strip():
        raise HTTPException(status_code=400, detail="project_id required")
    if not file.filename:
        raise HTTPException(status_code=400, detail="filename required")
    try:
        project = _get_project(db, project_id)
    except SQLAlchemyError:
        db.rollback()
        raise HTTPException(status_code=500, detail="Database error")
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    safe_name = _safe_filename(file.filename)
    attachment_id = new_id()
    project_dir = _ensure_upload_dir(project_id)
    stored_name = f"{attachment_id}_{safe_name}"
    stored_path = project_dir / stored_name

    try:
        with stored_path.open("wb") as target:
            shutil.copyfileobj(file.file, target)
    except Exception:
        logger.exception("Failed to save uploaded file")
        raise HTTPException(status_code=500, detail="File upload failed")

    size = stored_path.stat().st_size if stored_path.exists() else 0
    content_type = file.content_type or mimetypes.guess_type(safe_name)[0] or "application/octet-stream"
    category = _guess_category(content_type, safe_name)

    parsed_text = ""
    parse_status = "skipped"
    if category == "document":
        parsed_text, parse_status = _extract_text(stored_path, content_type, safe_name)
    image_meta = _extract_image_meta(stored_path) if category == "image" else {}

    tag_list = [item.strip() for item in tags.split(",") if item.strip()]
    attachment = {
        "id": attachment_id,
        "filename": safe_name,
        "content_type": content_type,
        "size": size,
        "category": category,
        "url": f"/api/v1/projects/{project_id}/attachments/{attachment_id}/file",
        "label": label.strip(),
        "bind_type": bind_type.strip(),
        "tags": tag_list,
        "parsed_text": parsed_text[:MAX_TEXT_CHARS],
        "parse_status": parse_status,
        "image_meta": image_meta,
        "created_at": utc_now(),
        "storage_path": str(stored_path),
    }

    metadata = project.get("metadata") if isinstance(project.get("metadata"), dict) else {}
    attachments = _ensure_attachments(metadata)
    attachments.append(attachment)
    try:
        project_repo.update_project(db, project_id, {"metadata": metadata})
    except SQLAlchemyError:
        db.rollback()
        raise HTTPException(status_code=500, detail="Database error")

    return ok({"attachment": attachment})


@router.patch("/{project_id}/attachments/{attachment_id}")
async def update_attachment(
    project_id: str,
    attachment_id: str,
    payload: Dict[str, Any],
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    if not project_id.strip() or not attachment_id.strip():
        raise HTTPException(status_code=400, detail="project_id and attachment_id required")
    try:
        project = _get_project(db, project_id)
    except SQLAlchemyError:
        db.rollback()
        raise HTTPException(status_code=500, detail="Database error")
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    metadata = project.get("metadata") if isinstance(project.get("metadata"), dict) else {}
    attachments = _ensure_attachments(metadata)
    attachment = next((item for item in attachments if item.get("id") == attachment_id), None)
    if not attachment:
        raise HTTPException(status_code=404, detail="Attachment not found")

    if "label" in payload and isinstance(payload.get("label"), str):
        attachment["label"] = payload["label"].strip()
    if "bind_type" in payload and isinstance(payload.get("bind_type"), str):
        attachment["bind_type"] = payload["bind_type"].strip()
    if "tags" in payload:
        tags = payload.get("tags")
        if isinstance(tags, list):
            attachment["tags"] = [str(item).strip() for item in tags if str(item).strip()]

    try:
        project_repo.update_project(db, project_id, {"metadata": metadata})
    except SQLAlchemyError:
        db.rollback()
        raise HTTPException(status_code=500, detail="Database error")

    return ok({"attachment": attachment})


@router.get("/{project_id}/attachments/{attachment_id}/file")
async def download_attachment(
    project_id: str,
    attachment_id: str,
    db: Session = Depends(get_db),
) -> FileResponse:
    if not project_id.strip() or not attachment_id.strip():
        raise HTTPException(status_code=400, detail="project_id and attachment_id required")
    try:
        project = _get_project(db, project_id)
    except SQLAlchemyError:
        db.rollback()
        raise HTTPException(status_code=500, detail="Database error")
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    metadata = project.get("metadata") if isinstance(project.get("metadata"), dict) else {}
    attachments = metadata.get("attachments") if isinstance(metadata.get("attachments"), list) else []
    attachment = next((item for item in attachments if item.get("id") == attachment_id), None)
    if not attachment:
        raise HTTPException(status_code=404, detail="Attachment not found")
    storage_path = attachment.get("storage_path")
    if not storage_path or not Path(storage_path).exists():
        raise HTTPException(status_code=404, detail="File not found")
    filename = attachment.get("filename") or "attachment"
    return FileResponse(storage_path, filename=filename)
