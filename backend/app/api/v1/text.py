import logging
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from fastapi import APIRouter, Body, Depends, HTTPException
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.api.v1.deps import get_current_user
from app.api.v1.response import ok
from app.db.models import MaterialPackage
from app.db.session import get_db
from app.repositories import material_packages as package_repo
from app.services.feedback_service import FeedbackService
from app.services.llm_service import LLMService
from app.services.user_llm_settings import resolve_llm_overrides
from app.store import new_id

router = APIRouter(prefix="/text", tags=["text"])
logger = logging.getLogger(__name__)


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _build_feedback_service(user: object) -> FeedbackService:
    overrides = resolve_llm_overrides(user)
    if not overrides.get("api_key") and not overrides.get("allow_fallback"):
        raise HTTPException(status_code=400, detail="api_key required")
    return FeedbackService(
        LLMService(
            api_key=overrides.get("api_key"),
            api_base=overrides.get("api_base"),
            allow_env_fallback=bool(overrides.get("allow_fallback")),
        )
    )


def _get_package(db: Session, package_id: str) -> Optional[MaterialPackage]:
    return db.query(MaterialPackage).filter(MaterialPackage.id == package_id).one_or_none()


def _ensure_text_candidates(metadata: dict) -> dict:
    container = metadata.get("text_candidates_v1")
    if isinstance(container, dict):
        if container.get("version") != "v1":
            container["version"] = "v1"
        container.setdefault("summary", {"active_id": None, "candidates": []})
        container.setdefault("art_style", {"active_id": None, "candidates": []})
        container.setdefault("subjects", {})
        container.setdefault("scenes", {})
        container.setdefault("storyboard", {})
        return container
    container = {
        "version": "v1",
        "summary": {"active_id": None, "candidates": []},
        "art_style": {"active_id": None, "candidates": []},
        "subjects": {},
        "scenes": {},
        "storyboard": {},
    }
    metadata["text_candidates_v1"] = container
    return container


def _get_blueprint(materials: dict) -> dict:
    metadata = materials.get("metadata") if isinstance(materials, dict) else {}
    blueprint = metadata.get("blueprint_v1") if isinstance(metadata, dict) else {}
    return blueprint if isinstance(blueprint, dict) else {}


def _resolve_summary(text_candidates: dict, blueprint: dict) -> str:
    summary = blueprint.get("summary") if isinstance(blueprint.get("summary"), dict) else {}
    current = summary.get("logline") or summary.get("synopsis") or ""
    group = text_candidates.get("summary") if isinstance(text_candidates.get("summary"), dict) else {}
    active_id = group.get("active_id")
    candidates = group.get("candidates") if isinstance(group.get("candidates"), list) else []
    if active_id:
        for cand in candidates:
            if isinstance(cand, dict) and cand.get("id") == active_id:
                value = cand.get("value") if isinstance(cand.get("value"), dict) else {}
                return value.get("summary") or current
    return current


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


def _resolve_subject(text_candidates: dict, blueprint: dict, subject_id: str) -> dict:
    subjects = blueprint.get("subjects") if isinstance(blueprint.get("subjects"), list) else []
    current: dict[str, Any] = {}
    for subject in subjects:
        if isinstance(subject, dict) and subject.get("id") == subject_id:
            current = subject
            break
    group = text_candidates.get("subjects") if isinstance(text_candidates.get("subjects"), dict) else {}
    subject_group = group.get(subject_id) if isinstance(group.get(subject_id), dict) else {}
    active_id = subject_group.get("active_id")
    candidates = subject_group.get("candidates") if isinstance(subject_group.get("candidates"), list) else []
    if active_id:
        for cand in candidates:
            if isinstance(cand, dict) and cand.get("id") == active_id:
                value = cand.get("value") if isinstance(cand.get("value"), dict) else {}
                return value or current
    return current


def _resolve_scene(text_candidates: dict, blueprint: dict, scene_id: str) -> dict:
    scenes = blueprint.get("scenes") if isinstance(blueprint.get("scenes"), list) else []
    current: dict[str, Any] = {}
    for scene in scenes:
        if isinstance(scene, dict) and scene.get("id") == scene_id:
            current = scene
            break
    group = text_candidates.get("scenes") if isinstance(text_candidates.get("scenes"), dict) else {}
    scene_group = group.get(scene_id) if isinstance(group.get(scene_id), dict) else {}
    active_id = scene_group.get("active_id")
    candidates = scene_group.get("candidates") if isinstance(scene_group.get("candidates"), list) else []
    if active_id:
        for cand in candidates:
            if isinstance(cand, dict) and cand.get("id") == active_id:
                value = cand.get("value") if isinstance(cand.get("value"), dict) else {}
                return value or current
    return current


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
    current_user: object = Depends(get_current_user),
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
    feedback_service = _build_feedback_service(current_user)
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
    group["active_id"] = candidate["id"]
    # NOTE: blueprint_v1 is immutable; store edits in text_candidates_v1 only.
    metadata["text_candidates_v1"] = text_candidates
    materials["metadata"] = metadata

    try:
        package_repo.update_package(db, package.id, {"materials": materials})
    except SQLAlchemyError:
        db.rollback()
        raise HTTPException(status_code=500, detail="Database error")

    return ok({"candidate": candidate, "material_package_id": package.id})


@router.post("/summary/feedback")
async def summary_feedback(
    payload: Dict[str, Any] = Body(default_factory=dict),
    current_user: object = Depends(get_current_user),
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
    current_summary = _resolve_summary(text_candidates, blueprint)
    feedback_service = _build_feedback_service(current_user)
    rewritten = feedback_service.rewrite_prompt("summary", current_summary, feedback)
    if not isinstance(rewritten, str):
        logger.warning("Summary rewrite returned invalid payload; falling back to current summary.")
        rewritten = current_summary

    candidate = {
        "id": new_id(),
        "source": "user_feedback",
        "feedback": feedback,
        "value": {"summary": rewritten},
        "created_at": _utc_now(),
    }
    group = text_candidates.setdefault("summary", {"active_id": None, "candidates": []})
    group_candidates = group.get("candidates")
    if not isinstance(group_candidates, list):
        group_candidates = []
        group["candidates"] = group_candidates
    group_candidates.append(candidate)
    group["active_id"] = candidate["id"]
    metadata["text_candidates_v1"] = text_candidates
    materials["metadata"] = metadata

    try:
        package_repo.update_package(db, package.id, {"materials": materials})
    except SQLAlchemyError:
        db.rollback()
        raise HTTPException(status_code=500, detail="Database error")

    return ok({"candidate": candidate, "material_package_id": package.id})


@router.post("/subjects/{subject_id}/feedback")
async def subject_feedback(
    subject_id: str,
    payload: Dict[str, Any] = Body(default_factory=dict),
    current_user: object = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    if not subject_id.strip():
        raise HTTPException(status_code=400, detail="subject_id required")
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
    subjects = blueprint.get("subjects") if isinstance(blueprint.get("subjects"), list) else []
    if not any(isinstance(subject, dict) and subject.get("id") == subject_id for subject in subjects):
        raise HTTPException(status_code=404, detail="Subject not found")

    current_subject = _resolve_subject(text_candidates, blueprint, subject_id)
    feedback_service = _build_feedback_service(current_user)
    rewritten = feedback_service.rewrite_prompt("subject", current_subject, feedback)
    if not isinstance(rewritten, dict):
        logger.warning("Subject rewrite returned invalid payload; falling back to current subject.")
        rewritten = current_subject

    candidate = {
        "id": new_id(),
        "source": "user_feedback",
        "feedback": feedback,
        "value": rewritten,
        "created_at": _utc_now(),
    }
    group = text_candidates.setdefault("subjects", {})
    subject_group = group.setdefault(subject_id, {"active_id": None, "candidates": []})
    group_candidates = subject_group.get("candidates")
    if not isinstance(group_candidates, list):
        group_candidates = []
        subject_group["candidates"] = group_candidates
    group_candidates.append(candidate)
    subject_group["active_id"] = candidate["id"]
    metadata["text_candidates_v1"] = text_candidates
    materials["metadata"] = metadata

    try:
        package_repo.update_package(db, package.id, {"materials": materials})
    except SQLAlchemyError:
        db.rollback()
        raise HTTPException(status_code=500, detail="Database error")

    return ok({"candidate": candidate, "material_package_id": package.id})


@router.post("/scenes/{scene_id}/feedback")
async def scene_feedback(
    scene_id: str,
    payload: Dict[str, Any] = Body(default_factory=dict),
    current_user: object = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    if not scene_id.strip():
        raise HTTPException(status_code=400, detail="scene_id required")
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
    scenes = blueprint.get("scenes") if isinstance(blueprint.get("scenes"), list) else []
    if not any(isinstance(scene, dict) and scene.get("id") == scene_id for scene in scenes):
        raise HTTPException(status_code=404, detail="Scene not found")

    current_scene = _resolve_scene(text_candidates, blueprint, scene_id)
    feedback_service = _build_feedback_service(current_user)
    rewritten = feedback_service.rewrite_prompt("scene", current_scene, feedback)
    if not isinstance(rewritten, dict):
        logger.warning("Scene rewrite returned invalid payload; falling back to current scene.")
        rewritten = current_scene

    candidate = {
        "id": new_id(),
        "source": "user_feedback",
        "feedback": feedback,
        "value": rewritten,
        "created_at": _utc_now(),
    }
    group = text_candidates.setdefault("scenes", {})
    scene_group = group.setdefault(scene_id, {"active_id": None, "candidates": []})
    group_candidates = scene_group.get("candidates")
    if not isinstance(group_candidates, list):
        group_candidates = []
        scene_group["candidates"] = group_candidates
    group_candidates.append(candidate)
    scene_group["active_id"] = candidate["id"]
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
    current_user: object = Depends(get_current_user),
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
    feedback_service = _build_feedback_service(current_user)
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
    shot_group["active_id"] = candidate["id"]

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
    subject_id = payload.get("subject_id")
    scene_id = payload.get("scene_id")

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
    elif target == "summary":
        group = text_candidates.setdefault("summary", {"active_id": None, "candidates": []})
        candidates = group.get("candidates") if isinstance(group.get("candidates"), list) else []
        if not any(isinstance(cand, dict) and cand.get("id") == candidate_id for cand in candidates):
            raise HTTPException(status_code=404, detail="Candidate not found")
        group["active_id"] = candidate_id
    elif target == "subject":
        if not isinstance(subject_id, str) or not subject_id.strip():
            raise HTTPException(status_code=400, detail="subject_id required")
        group = text_candidates.setdefault("subjects", {})
        subject_group = group.get(subject_id)
        if not isinstance(subject_group, dict):
            raise HTTPException(status_code=404, detail="Subject candidate group not found")
        candidates = subject_group.get("candidates") if isinstance(subject_group.get("candidates"), list) else []
        if not any(isinstance(cand, dict) and cand.get("id") == candidate_id for cand in candidates):
            raise HTTPException(status_code=404, detail="Candidate not found")
        subject_group["active_id"] = candidate_id
    elif target == "scene":
        if not isinstance(scene_id, str) or not scene_id.strip():
            raise HTTPException(status_code=400, detail="scene_id required")
        group = text_candidates.setdefault("scenes", {})
        scene_group = group.get(scene_id)
        if not isinstance(scene_group, dict):
            raise HTTPException(status_code=404, detail="Scene candidate group not found")
        candidates = scene_group.get("candidates") if isinstance(scene_group.get("candidates"), list) else []
        if not any(isinstance(cand, dict) and cand.get("id") == candidate_id for cand in candidates):
            raise HTTPException(status_code=404, detail="Candidate not found")
        scene_group["active_id"] = candidate_id
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
