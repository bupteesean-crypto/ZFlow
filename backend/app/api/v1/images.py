import logging
from typing import Any, Dict, Optional

from fastapi import APIRouter, Body, Depends, HTTPException
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.api.v1.response import ok
from app.db.models import MaterialPackage
from app.db.session import get_db
from app.repositories import material_packages as package_repo
from app.services.feedback_service import FeedbackService
from app.services.image_service import ImageService
from app.store import new_id

router = APIRouter(prefix="/images", tags=["images"])
image_service = ImageService()
feedback_service = FeedbackService()
logger = logging.getLogger(__name__)
STORYBOARD_REFERENCE_IMAGE_LIMIT = 10


def _normalize_text(value: object) -> str:
    if isinstance(value, str):
        return value.strip()
    return ""


def _select_active_image(images: list[dict]) -> dict | None:
    for image in images:
        if image.get("is_active") is True:
            return image
    return images[0] if images else None


def _scene_reference_url(images: list[dict], scene_id: str) -> str:
    if not scene_id:
        return ""
    matches = [
        image
        for image in images
        if image.get("type") == "scene" and image.get("scene_id") == scene_id and image.get("url")
    ]
    chosen = _select_active_image(matches)
    return chosen.get("url") if isinstance(chosen, dict) else ""


def _subject_reference_urls(images: list[dict], subject_id: str) -> list[str]:
    if not subject_id:
        return []
    candidates = [
        image
        for image in images
        if image.get("subject_id") == subject_id
        and image.get("url")
        and image.get("type") in {"character_view", "character_sheet"}
    ]
    if not candidates:
        return []
    active = [image for image in candidates if image.get("is_active") is True] or candidates

    sheet = [image.get("url") for image in active if image.get("type") == "character_sheet"]
    sheet = [url for url in sheet if isinstance(url, str) and url.strip()]
    if sheet:
        return sheet[:1]

    urls = []
    for view in ("front", "side", "back"):
        match = next((image for image in active if image.get("view") == view), None)
        if match and match.get("url"):
            urls.append(match["url"])
    if urls:
        return urls

    first = active[0]
    return [first.get("url")] if first.get("url") else []


def _extract_subject_ids(shot: dict, subjects: list[dict]) -> list[str]:
    if isinstance(shot.get("subject_ids"), list):
        provided = [str(item).strip() for item in shot.get("subject_ids") if str(item).strip()]
        if provided:
            return list(dict.fromkeys(provided))
    if isinstance(shot.get("subject_names"), list):
        names = [str(item).strip() for item in shot.get("subject_names") if str(item).strip()]
        if names:
            matched = []
            for subject in subjects:
                if not isinstance(subject, dict):
                    continue
                subject_id = _normalize_text(subject.get("id"))
                name = _normalize_text(subject.get("name"))
                if subject_id and name and name in names:
                    matched.append(subject_id)
            if matched:
                return list(dict.fromkeys(matched))
    text_parts = []
    for key in ("description", "prompt_hint", "prompt"):
        value = shot.get(key)
        if isinstance(value, str) and value.strip():
            text_parts.append(value.strip())
    full_text = " ".join(text_parts)
    matched: list[str] = []
    for subject in subjects:
        if not isinstance(subject, dict):
            continue
        subject_id = _normalize_text(subject.get("id"))
        name = _normalize_text(subject.get("name"))
        if not subject_id or not name:
            continue
        if name in full_text:
            matched.append(subject_id)
    return list(dict.fromkeys(matched))


def _active_storyboard_url(images: list[dict], shot_id: str) -> str:
    if not shot_id:
        return ""
    matches = [
        image
        for image in images
        if image.get("type") == "storyboard" and image.get("shot_id") == shot_id and image.get("url")
    ]
    chosen = _select_active_image(matches)
    return chosen.get("url") if isinstance(chosen, dict) else ""


def _dedupe_urls(urls: list[str], limit: int) -> list[str]:
    cleaned = [url.strip() for url in urls if isinstance(url, str) and url.strip()]
    if not cleaned:
        return []
    deduped = list(dict.fromkeys(cleaned))
    return deduped[:limit]


def _find_image(
    db: Session,
    image_id: str,
) -> tuple[Optional[MaterialPackage], Optional[dict], Optional[list]]:
    packages = db.query(MaterialPackage).all()
    for package in packages:
        materials = package.materials or {}
        metadata = materials.get("metadata") if isinstance(materials, dict) else {}
        images = metadata.get("images") if isinstance(metadata, dict) else []
        if not isinstance(images, list):
            continue
        for image in images:
            if isinstance(image, dict) and image.get("id") == image_id:
                return package, image, images
    return None, None, None


def _group_key(image: dict) -> tuple:
    image_type = image.get("type") or ""
    shot_id = image.get("shot_id")
    subject_id = image.get("subject_id")
    view = image.get("view")
    scene_id = image.get("scene_id")
    if image_type == "storyboard" and shot_id:
        return ("storyboard", shot_id, image_type)
    if subject_id and image_type == "character_sheet":
        return ("subject", subject_id, image_type)
    if subject_id and view:
        return ("subject", subject_id, view, image_type)
    if scene_id:
        return ("scene", scene_id, image_type)
    return ("single", image.get("id") or "", image_type)


@router.post("/{image_id}/regenerate")
async def regenerate_image(
    image_id: str,
    payload: Dict[str, Any] = Body(default_factory=dict),
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    if not image_id.strip():
        raise HTTPException(status_code=400, detail="image_id required")
    prompt = payload.get("prompt")
    if not isinstance(prompt, str) or not prompt.strip():
        raise HTTPException(status_code=400, detail="prompt required")
    prompt = prompt.strip()
    prompt_source = payload.get("prompt_source")
    if prompt_source is not None and not isinstance(prompt_source, str):
        raise HTTPException(status_code=400, detail="prompt_source must be a string")
    prompt_source = prompt_source.strip() if isinstance(prompt_source, str) and prompt_source.strip() else "user_edit"
    size = payload.get("size")
    if size is not None and not isinstance(size, str):
        raise HTTPException(status_code=400, detail="size must be a string")

    try:
        package, source_image, images = _find_image(db, image_id)
    except SQLAlchemyError:
        db.rollback()
        raise HTTPException(status_code=500, detail="Database error")
    if not package or not source_image or images is None:
        raise HTTPException(status_code=404, detail="Image not found")

    materials = dict(package.materials or {})
    metadata = dict(materials.get("metadata") or {})
    if not size:
        size = metadata.get("image_size") if isinstance(metadata.get("image_size"), str) else None
    ref_images: list[str] = []
    if source_image.get("type") == "storyboard":
        blueprint = metadata.get("blueprint_v1") if isinstance(metadata, dict) else {}
        storyboard = blueprint.get("storyboard") if isinstance(blueprint.get("storyboard"), list) else []
        subjects = blueprint.get("subjects") if isinstance(blueprint.get("subjects"), list) else []
        if not subjects and isinstance(materials.get("characters"), list):
            subjects = materials.get("characters") or []

        shot_id = _normalize_text(source_image.get("shot_id"))
        shot = next((item for item in storyboard if isinstance(item, dict) and item.get("id") == shot_id), None)
        scene_id = _normalize_text(source_image.get("scene_id"))
        if isinstance(shot, dict):
            scene_id = _normalize_text(shot.get("scene_id")) or scene_id
            scene_url = _scene_reference_url(images, scene_id)
            if scene_url:
                ref_images.append(scene_url)
            for subject_id in _extract_subject_ids(shot, subjects):
                ref_images.extend(_subject_reference_urls(images, subject_id))

            prev_shot_id = ""
            for index, item in enumerate(storyboard):
                if not isinstance(item, dict):
                    continue
                if item.get("id") == shot_id:
                    if index > 0 and isinstance(storyboard[index - 1], dict):
                        prev_shot_id = _normalize_text(storyboard[index - 1].get("id"))
                    break
            if prev_shot_id:
                prev_url = _active_storyboard_url(images, prev_shot_id)
                if prev_url:
                    ref_images.append(prev_url)
        else:
            scene_url = _scene_reference_url(images, scene_id)
            if scene_url:
                ref_images.append(scene_url)

        ref_images = _dedupe_urls(ref_images, STORYBOARD_REFERENCE_IMAGE_LIMIT)

    try:
        if ref_images:
            image_result = image_service.generate_image_with_refs(prompt, ref_images, size=size)
        else:
            image_result = image_service.generate_image(prompt, size=size)
    except Exception:
        logger.exception("image regeneration failed image_id=%s", image_id)
        raise HTTPException(status_code=502, detail="Image generation failed")

    if not isinstance(image_result, dict) or not image_result.get("url"):
        raise HTTPException(status_code=502, detail="Image generation failed")

    image_type = source_image.get("type") or "scene"
    new_image = {
        "id": new_id(),
        "type": image_type,
        "shot_id": source_image.get("shot_id"),
        "scene_id": source_image.get("scene_id"),
        "scene_name": source_image.get("scene_name"),
        "subject_id": source_image.get("subject_id"),
        "subject_name": source_image.get("subject_name"),
        "view": source_image.get("view"),
        "url": image_result.get("url"),
        "prompt": prompt,
        "prompt_parts": {"content": prompt, "style": "", "constraints": ""},
        "prompt_source": prompt_source,
        "prompt_version": None,
        "regenerated_from": image_id,
        "provider": image_result.get("provider"),
        "model": image_result.get("model"),
        "size": image_result.get("size"),
    }

    materials = dict(package.materials or {})
    metadata = dict(materials.get("metadata") or {})
    existing_images = list(metadata.get("images") or [])
    existing_images.append(new_image)
    metadata["images"] = existing_images
    if size:
        metadata["image_size"] = size
        image_plan = metadata.get("image_plan") if isinstance(metadata.get("image_plan"), dict) else {}
        if isinstance(image_plan, dict):
            image_plan["size"] = size
            metadata["image_plan"] = image_plan
    materials["metadata"] = metadata

    try:
        package_repo.update_package(db, package.id, {"materials": materials})
    except SQLAlchemyError:
        db.rollback()
        raise HTTPException(status_code=500, detail="Database error")

    return ok({"image": new_image, "material_package_id": package.id})


@router.post("/{image_id}/feedback")
async def rewrite_image_prompt(
    image_id: str,
    payload: Dict[str, Any] = Body(default_factory=dict),
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    if not image_id.strip():
        raise HTTPException(status_code=400, detail="image_id required")
    feedback = payload.get("feedback")
    if not isinstance(feedback, str) or not feedback.strip():
        raise HTTPException(status_code=400, detail="feedback required")
    feedback = feedback.strip()

    try:
        _, source_image, _ = _find_image(db, image_id)
    except SQLAlchemyError:
        db.rollback()
        raise HTTPException(status_code=500, detail="Database error")
    if not source_image:
        raise HTTPException(status_code=404, detail="Image not found")

    original_prompt = source_image.get("prompt") or ""
    prompt_parts = source_image.get("prompt_parts") if isinstance(source_image.get("prompt_parts"), dict) else None
    rewritten_prompt = feedback_service.rewrite_prompt("image", original_prompt, feedback, prompt_parts)
    return ok({"rewritten_prompt": rewritten_prompt, "source_image_id": image_id})


@router.post("/{image_id}/adopt")
async def adopt_image(
    image_id: str,
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    if not image_id.strip():
        raise HTTPException(status_code=400, detail="image_id required")
    try:
        package, source_image, images = _find_image(db, image_id)
    except SQLAlchemyError:
        db.rollback()
        raise HTTPException(status_code=500, detail="Database error")
    if not package or not source_image or images is None:
        raise HTTPException(status_code=404, detail="Image not found")

    target_group = _group_key(source_image)
    updated = False
    for image in images:
        if not isinstance(image, dict):
            continue
        if _group_key(image) != target_group:
            continue
        image["is_active"] = image.get("id") == image_id
        updated = True

    if not updated:
        raise HTTPException(status_code=404, detail="Image not found")

    materials = dict(package.materials or {})
    metadata = dict(materials.get("metadata") or {})
    metadata["images"] = images
    materials["metadata"] = metadata

    try:
        package_repo.update_package(db, package.id, {"materials": materials})
    except SQLAlchemyError:
        db.rollback()
        raise HTTPException(status_code=500, detail="Database error")

    return ok({"image_id": image_id, "material_package_id": package.id})
