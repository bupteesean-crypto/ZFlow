import logging
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from fastapi import APIRouter, Body, Depends, HTTPException
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.api.v1.response import ok
from app.db.models import MaterialPackage
from app.db.session import get_db
from app.repositories import material_packages as package_repo
from app.services.feedback_service import FeedbackService
from app.store import new_id

router = APIRouter(prefix="/text", tags=["text"])
feedback_service = FeedbackService()
logger = logging.getLogger(__name__)


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _get_package(db: Session, package_id: str) -> Optional[MaterialPackage]:
    return db.query(MaterialPackage).filter(MaterialPackage.id == package_id).one_or_none()


def _ensure_text_candidates(metadata: dict) -> dict:
    container = metadata.get("text_candidates_v1")
    if isinstance(container, dict):
        if container.get("version") != "v1":
            container["version"] = "v1"
        return container
    container = {"version": "v1", "art_style": {"active_id": None, "candidates": []}, "storyboard": {}}
    metadata["text_candidates_v1"] = container
    return container


def _get_blueprint(materials: dict) -> dict:
    metadata = materials.get("metadata") if isinstance(materials, dict) else {}
    blueprint = metadata.get("blueprint_v1") if isinstance(metadata, dict) else {}
    return blueprint if isinstance(blueprint, dict) else {}


def _resolve_art_style(text_candidates: dict, blueprint: dict) -> dict:
    art_style = blueprint.get("art_style") if isinstance(blueprint.get("art_style"), dict) else {}
    group = text_candidates.get("art_style") if isinstance(text_candidates.get("art_style"), dict) else {}
    active_id = group.get("active_id")
    candidates = group.get("candidates") if isinstance(group.get("candidates"), list) else []
    if active_id:
        for cand in candidates:
            if isinstance(cand, dict) and cand.get("id") == active_id:
                value = cand.get("value")
                return value if isinstance(value, dict) else art_style
    return art_style


def _resolve_storyboard_description(text_candidates: dict, blueprint: dict, shot_id: str) -> str:
    storyboard = blueprint.get("storyboard") if isinstance(blueprint.get("storyboard"), list) else []
    current = ""
    for shot in storyboard:
        if isinstance(shot, dict) and shot.get("id") == shot_id:
            current = shot.get("description") or ""
            break
    group = text_candidates.get("storyboard") if isinstance(text_candidates.get("storyboard"), dict) else {}
    shot_group = group.get(shot_id) if isinstance(group.get(shot_id), dict) else {}
    active_id = shot_group.get("active_id")
    candidates = shot_group.get("candidates") if isinstance(shot_group.get("candidates"), list) else []
    if active_id:
        for cand in candidates:
            if isinstance(cand, dict) and cand.get("id") == active_id:
                value = cand.get("value") if isinstance(cand.get("value"), dict) else {}
                return value.get("description") or current
    return current


@router.post("/art-style/feedback")
async def art_style_feedback(
    payload: Dict[str, Any] = Body(default_factory=dict),
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    package_id = payload.get("material_package_id")
    if not isinstance(package_id, str) or not package_id.strip():
        raise HTTPException(status_code=400, detail="material_package_id required")
    feedback = payload.get("feedback")
    if not isinstance(feedback, str) or not feedback.strip():
        raise HTTPException(status_code=400, detail="feedback required")
    feedback = feedback.strip()

    try:
        package = _get_package(db, package_id)
    except SQLAlchemyError:
        db.rollback()
        raise HTTPException(status_code=500, detail="Database error")
    if not package:
        raise HTTPException(status_code=404, detail="Material package not found")

    materials = dict(package.materials or {})
    metadata = dict(materials.get("metadata") or {})
    text_candidates = _ensure_text_candidates(metadata)
    blueprint = _get_blueprint(materials)
    current_style = _resolve_art_style(text_candidates, blueprint)
    rewritten = feedback_service.rewrite_prompt("art_style", current_style, feedback)
    if not isinstance(rewritten, dict):
        logger.warning("Art style rewrite returned invalid payload; falling back to current style.")
        rewritten = current_style

    candidate = {
        "id": new_id(),
        "source": "user_feedback",
        "feedback": feedback,
        "value": rewritten,
        "created_at": _utc_now(),
    }
    group = text_candidates.setdefault("art_style", {"active_id": None, "candidates": []})
    group_candidates = group.get("candidates")
    if not isinstance(group_candidates, list):
        group_candidates = []
        group["candidates"] = group_candidates
    group_candidates.append(candidate)
    # NOTE: blueprint_v1 is immutable; store edits in text_candidates_v1 only.
    metadata["text_candidates_v1"] = text_candidates
    materials["metadata"] = metadata

    try:
        package_repo.update_package(db, package.id, {"materials": materials})
    except SQLAlchemyError:
        db.rollback()
        raise HTTPException(status_code=500, detail="Database error")

    return ok({"candidate": candidate, "material_package_id": package.id})


@router.post("/storyboard/{shot_id}/feedback")
async def storyboard_feedback(
    shot_id: str,
    payload: Dict[str, Any] = Body(default_factory=dict),
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    if not shot_id.strip():
        raise HTTPException(status_code=400, detail="shot_id required")
    package_id = payload.get("material_package_id")
    if not isinstance(package_id, str) or not package_id.strip():
        raise HTTPException(status_code=400, detail="material_package_id required")
    feedback = payload.get("feedback")
    if not isinstance(feedback, str) or not feedback.strip():
        raise HTTPException(status_code=400, detail="feedback required")
    feedback = feedback.strip()

    try:
        package = _get_package(db, package_id)
    except SQLAlchemyError:
        db.rollback()
        raise HTTPException(status_code=500, detail="Database error")
    if not package:
        raise HTTPException(status_code=404, detail="Material package not found")

    materials = dict(package.materials or {})
    metadata = dict(materials.get("metadata") or {})
    text_candidates = _ensure_text_candidates(metadata)
    blueprint = _get_blueprint(materials)
    storyboard = blueprint.get("storyboard") if isinstance(blueprint.get("storyboard"), list) else []
    if not any(isinstance(shot, dict) and shot.get("id") == shot_id for shot in storyboard):
        raise HTTPException(status_code=404, detail="Storyboard shot not found")

    current_description = _resolve_storyboard_description(text_candidates, blueprint, shot_id)
    rewritten = feedback_service.rewrite_prompt("storyboard_description", current_description, feedback)
    if not isinstance(rewritten, str):
        logger.warning("Storyboard rewrite returned invalid payload; falling back to current description.")
        rewritten = current_description

    candidate = {
        "id": new_id(),
        "source": "user_feedback",
        "feedback": feedback,
        "value": {"description": rewritten},
        "created_at": _utc_now(),
    }
    group = text_candidates.setdefault("storyboard", {})
    shot_group = group.setdefault(shot_id, {"active_id": None, "candidates": []})
    group_candidates = shot_group.get("candidates")
    if not isinstance(group_candidates, list):
        group_candidates = []
        shot_group["candidates"] = group_candidates
    group_candidates.append(candidate)

    # NOTE: blueprint_v1 is immutable; store edits in text_candidates_v1 only.
    metadata["text_candidates_v1"] = text_candidates
    materials["metadata"] = metadata

    try:
        package_repo.update_package(db, package.id, {"materials": materials})
    except SQLAlchemyError:
        db.rollback()
        raise HTTPException(status_code=500, detail="Database error")

    return ok({"candidate": candidate, "material_package_id": package.id})


@router.post("/adopt")
async def adopt_text_candidate(
    payload: Dict[str, Any] = Body(default_factory=dict),
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    package_id = payload.get("material_package_id")
    if not isinstance(package_id, str) or not package_id.strip():
        raise HTTPException(status_code=400, detail="material_package_id required")
    target_type = payload.get("target_type")
    if not isinstance(target_type, str) or not target_type.strip():
        raise HTTPException(status_code=400, detail="target_type required")
    candidate_id = payload.get("candidate_id")
    if not isinstance(candidate_id, str) or not candidate_id.strip():
        raise HTTPException(status_code=400, detail="candidate_id required")
    shot_id = payload.get("shot_id")

    try:
        package = _get_package(db, package_id)
    except SQLAlchemyError:
        db.rollback()
        raise HTTPException(status_code=500, detail="Database error")
    if not package:
        raise HTTPException(status_code=404, detail="Material package not found")

    materials = dict(package.materials or {})
    metadata = dict(materials.get("metadata") or {})
    text_candidates = _ensure_text_candidates(metadata)

    target = target_type.strip().lower()
    if target == "art_style":
        group = text_candidates.setdefault("art_style", {"active_id": None, "candidates": []})
        candidates = group.get("candidates") if isinstance(group.get("candidates"), list) else []
        if not any(isinstance(cand, dict) and cand.get("id") == candidate_id for cand in candidates):
            raise HTTPException(status_code=404, detail="Candidate not found")
        group["active_id"] = candidate_id
    elif target == "storyboard_description":
        if not isinstance(shot_id, str) or not shot_id.strip():
            raise HTTPException(status_code=400, detail="shot_id required")
        group = text_candidates.setdefault("storyboard", {})
        shot_group = group.get(shot_id)
        if not isinstance(shot_group, dict):
            raise HTTPException(status_code=404, detail="Storyboard candidate group not found")
        candidates = shot_group.get("candidates") if isinstance(shot_group.get("candidates"), list) else []
        if not any(isinstance(cand, dict) and cand.get("id") == candidate_id for cand in candidates):
            raise HTTPException(status_code=404, detail="Candidate not found")
        shot_group["active_id"] = candidate_id
    else:
        raise HTTPException(status_code=400, detail="target_type invalid")

    # NOTE: blueprint_v1 is immutable; store edits in text_candidates_v1 only.
    metadata["text_candidates_v1"] = text_candidates
    materials["metadata"] = metadata

    try:
        package_repo.update_package(db, package.id, {"materials": materials})
    except SQLAlchemyError:
        db.rollback()
        raise HTTPException(status_code=500, detail="Database error")

    return ok({"candidate_id": candidate_id, "material_package_id": package.id})
