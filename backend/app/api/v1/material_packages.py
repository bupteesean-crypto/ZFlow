import logging
from typing import Any, Dict

from fastapi import APIRouter, Body, Depends, HTTPException
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.api.v1.response import ok
from app.core.config import settings
from app.db.session import get_db
from app.repositories import material_packages as package_repo
from app.repositories import projects as project_repo
from app.services.blueprint_service import build_blueprint
from app.services.generation_events import publish_generation_event, reset_generation_events
from app.services.image_service import ImageService
from app.services.llm_service import LLMService
from app.services.video_service import VideoService
from app.store import new_id, utc_now

router = APIRouter(tags=["material-packages"])
image_service = ImageService()
llm_service = LLMService()
video_service = VideoService()
logger = logging.getLogger(__name__)

PACKAGE_STATUSES = {"generating", "completed", "failed"}
SCENE_QUALITY_CONSTRAINTS = (
    "no text, no captions, no logos, no watermark\n"
    "no people, no characters, empty environment\n"
    "avoid low-quality artifacts or distortion\n"
    "avoid malformed anatomy or extra limbs\n"
    "no busy patterns"
)
CHARACTER_QUALITY_CONSTRAINTS = (
    "no text, no captions, no logos, no watermark\n"
    "avoid low-quality artifacts or distortion\n"
    "avoid malformed anatomy or extra limbs\n"
    "front view, side view, back view in one canvas\n"
    "front shows face and torso, side shows profile silhouette, back shows hair and back details\n"
    "evenly spaced, same scale and proportions\n"
    "consistent line weight and lighting\n"
    "neutral background"
)
STORYBOARD_QUALITY_CONSTRAINTS = (
    "no text, no captions, no logos, no watermark\n"
    "avoid low-quality artifacts or distortion\n"
    "avoid malformed anatomy or extra limbs\n"
    "clear focal subject, cinematic framing\n"
    "consistent style, balanced lighting"
)
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


def _active_storyboard_url(images: list[dict]) -> str:
    chosen = _select_active_image(images)
    if isinstance(chosen, dict):
        return chosen.get("url") or ""
    return ""


def _select_active_video(videos: list[dict]) -> dict | None:
    for video in videos:
        if video.get("is_active") is True:
            return video
    return videos[0] if videos else None


def _extract_subject_ids(shot: dict, subjects: list[dict]) -> list[str]:
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


def _dedupe_urls(urls: list[str], limit: int) -> list[str]:
    cleaned = [url.strip() for url in urls if isinstance(url, str) and url.strip()]
    if not cleaned:
        return []
    deduped = list(dict.fromkeys(cleaned))
    return deduped[:limit]


def _emit_step(project_id: str, step: str, status: str, message: str) -> None:
    publish_generation_event(
        project_id,
        {
            "type": "generation.step",
            "step": step,
            "status": status,
            "message": message,
        },
    )


def _next_package_version(items: list[dict]) -> int:
    max_version = 0
    for item in items:
        materials = item.get("materials") if isinstance(item, dict) else {}
        metadata = materials.get("metadata") if isinstance(materials, dict) else {}
        version = metadata.get("package_version") if isinstance(metadata, dict) else None
        if isinstance(version, int) and version > max_version:
            max_version = version
    if max_version == 0 and items:
        return len(items) + 1
    return max_version + 1


def _extract_source_prompt(materials: dict) -> str:
    metadata = materials.get("metadata") if isinstance(materials, dict) else {}
    blueprint = metadata.get("blueprint_v1") if isinstance(metadata, dict) else {}
    if isinstance(blueprint, dict):
        generation = blueprint.get("generation") if isinstance(blueprint.get("generation"), dict) else {}
        source_prompt = generation.get("source_prompt") if isinstance(generation, dict) else ""
        if isinstance(source_prompt, str) and source_prompt.strip():
            return source_prompt.strip()
    summary = metadata.get("summary") if isinstance(metadata, dict) else ""
    return summary if isinstance(summary, str) else ""


def _join_keywords(items: list[str]) -> str:
    return ", ".join([item for item in items if isinstance(item, str) and item.strip()])


def _build_character_prompt_parts(subject: dict, blueprint: dict, sheet_prompt: str) -> dict:
    art_style = blueprint.get("art_style", {}) if isinstance(blueprint, dict) else {}
    name = subject.get("name") or "Character"
    description = subject.get("description") or ""
    traits = subject.get("visual_traits") if isinstance(subject.get("visual_traits"), list) else []
    traits_text = _join_keywords([str(item) for item in traits]) if traits else ""
    content_lines = [
        f"Character: {name}",
        f"Description: {description}",
        "Turnaround: front / side / back in one canvas",
        "Front: face and torso details; Side: profile and silhouette; Back: hair and back details",
    ]
    if traits_text:
        content_lines.append(f"Visual traits: {traits_text}")
    if sheet_prompt:
        content_lines.append(f"Prompt: {sheet_prompt}")

    style_prompt = art_style.get("style_prompt") if isinstance(art_style, dict) else ""
    style_prompt = style_prompt.strip() if isinstance(style_prompt, str) else ""
    palette = art_style.get("palette") if isinstance(art_style, dict) else []
    palette = [str(item).strip() for item in palette if str(item).strip()] if isinstance(palette, list) else []
    if palette:
        palette_line = f"Palette: {', '.join(palette)}"
        style_prompt = f"{style_prompt}\n{palette_line}".strip() if style_prompt else palette_line

    return {
        "content": "\n".join(content_lines).strip(),
        "style": style_prompt or "",
        "constraints": CHARACTER_QUALITY_CONSTRAINTS,
    }


def _build_character_sheet_prompt(subject: dict, blueprint: dict) -> str:
    art_style = blueprint.get("art_style", {}) if isinstance(blueprint, dict) else {}
    name = subject.get("name") or "Character"
    description = subject.get("description") or ""
    traits = subject.get("visual_traits") if isinstance(subject.get("visual_traits"), list) else []
    traits_text = _join_keywords([str(item) for item in traits]) if traits else ""
    style_prompt = art_style.get("style_prompt") if isinstance(art_style, dict) else ""
    style_prompt = style_prompt.strip() if isinstance(style_prompt, str) else ""
    palette = art_style.get("palette") if isinstance(art_style, dict) else []
    palette = [str(item).strip() for item in palette if str(item).strip()] if isinstance(palette, list) else []
    if palette:
        palette_line = f"Palette: {', '.join(palette)}"
        style_prompt = f"{style_prompt}\n{palette_line}".strip() if style_prompt else palette_line

    lines = [
        "Create a clean 3:4 portrait character turnaround sheet for a single character.",
        "",
        f"Character: {name}",
        f"Description: {description}",
    ]
    if traits_text:
        lines.append(f"Visual traits: {traits_text}")
    if style_prompt:
        lines.append(f"Style: {style_prompt}")
    lines.extend(
        [
            "",
            "Composition:",
            "- front view, side view, back view in one canvas",
            "- front shows facial features and torso; side shows profile silhouette; back shows hair and back details",
            "- evenly spaced, same scale, consistent proportions",
            "- full-body views, centered",
            "- neutral background, uniform lighting",
            "",
            "Constraints:",
            "- no text, no captions, no logos, no watermark",
            "- avoid extra limbs or distorted anatomy",
        ]
    )
    return "\n".join([line for line in lines if line is not None]).strip()


def _build_storyboard_prompt_parts(shot: dict, scene: dict, blueprint: dict) -> dict:
    summary = blueprint.get("summary", {}) if isinstance(blueprint, dict) else {}
    art_style = blueprint.get("art_style", {}) if isinstance(blueprint, dict) else {}
    subjects = blueprint.get("subjects") if isinstance(blueprint.get("subjects"), list) else []

    description = shot.get("description") or ""
    camera = shot.get("camera") or ""
    scene_summary = scene.get("description") or summary.get("synopsis") or ""
    mood = scene.get("mood") or "neutral"
    keywords = summary.get("keywords") if isinstance(summary.get("keywords"), list) else []

    content_lines = []
    if description:
        content_lines.append(f"Shot description: {description}")
    if scene_summary:
        content_lines.append(f"Scene summary: {scene_summary}")
    if mood:
        content_lines.append(f"Mood: {mood}")
    if camera:
        content_lines.append(f"Camera: {camera}")
    keywords_text = _join_keywords([str(item) for item in keywords]) if keywords else ""
    if keywords_text:
        content_lines.append(f"Keywords: {keywords_text}")

    if subjects:
        subject_lines = []
        for subject in subjects:
            name = subject.get("name") or "Character"
            desc = subject.get("description") or ""
            traits = subject.get("visual_traits") if isinstance(subject.get("visual_traits"), list) else []
            traits_text = _join_keywords([str(item) for item in traits]) if traits else ""
            line = f"{name}: {desc}".strip()
            if traits_text:
                line = f"{line} (Traits: {traits_text})"
            subject_lines.append(line)
        if subject_lines:
            content_lines.append("Characters: " + " | ".join(subject_lines))

    style_prompt = art_style.get("style_prompt") if isinstance(art_style, dict) else ""
    style_prompt = style_prompt.strip() if isinstance(style_prompt, str) else ""
    palette = art_style.get("palette") if isinstance(art_style.get("palette"), list) else []
    palette = [str(item).strip() for item in palette if str(item).strip()] if isinstance(palette, list) else []
    if palette:
        palette_line = f"Palette: {', '.join(palette)}"
        style_prompt = f"{style_prompt}\n{palette_line}".strip() if style_prompt else palette_line

    return {
        "content": "\n".join(content_lines).strip(),
        "style": style_prompt or "",
        "constraints": STORYBOARD_QUALITY_CONSTRAINTS,
    }


def _render_storyboard_prompt(parts: dict) -> str:
    content = parts.get("content") or ""
    style = parts.get("style") or ""
    constraints = parts.get("constraints") or ""
    sections = ["Create a clean storyboard frame for a short video."]
    if content:
        sections.append(content)
    if style:
        sections.append(f"Style:\n{style}")
    if constraints:
        sections.append(f"Constraints:\n{constraints}")
    return "\n\n".join(sections).strip()


@router.get("/projects/{project_id}/material-packages")
async def list_material_packages(
    project_id: str,
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    try:
        project = project_repo.get_project(db, project_id)
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")
        items = package_repo.list_packages_for_project(db, project_id)
    except HTTPException:
        raise
    except SQLAlchemyError:
        db.rollback()
        raise HTTPException(status_code=500, detail="Database error")
    return ok({"list": items, "total": len(items)})


@router.get("/material-packages/{package_id}")
async def get_material_package(
    package_id: str,
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    try:
        package = package_repo.get_package(db, package_id)
    except SQLAlchemyError:
        db.rollback()
        raise HTTPException(status_code=500, detail="Database error")
    if not package:
        raise HTTPException(status_code=404, detail="Material package not found")
    return ok(package)


@router.put("/material-packages/{package_id}")
async def update_material_package(
    package_id: str,
    payload: Dict[str, Any] = Body(default_factory=dict),
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    if "package_name" in payload and payload["package_name"] is not None and not isinstance(payload["package_name"], str):
        raise HTTPException(status_code=400, detail="package_name must be a string")
    if "summary" in payload and payload["summary"] is not None and not isinstance(payload["summary"], str):
        raise HTTPException(status_code=400, detail="summary must be a string")
    if "materials" in payload and payload["materials"] is not None and not isinstance(payload["materials"], dict):
        raise HTTPException(status_code=400, detail="materials must be an object")
    if "status" in payload and payload["status"] not in PACKAGE_STATUSES:
        raise HTTPException(status_code=400, detail="status invalid")
    if "is_active" in payload and not isinstance(payload["is_active"], bool):
        raise HTTPException(status_code=400, detail="is_active must be a boolean")
    try:
        package = package_repo.update_package(db, package_id, payload)
    except SQLAlchemyError:
        db.rollback()
        raise HTTPException(status_code=500, detail="Database error")
    if not package:
        raise HTTPException(status_code=404, detail="Material package not found")
    return ok(package)


@router.post("/material-packages/{package_id}/storyboard-images")
async def generate_storyboard_images(
    package_id: str,
    payload: Dict[str, Any] = Body(default_factory=dict),
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    force = payload.get("force") is True
    size = payload.get("size")
    if size is not None and not isinstance(size, str):
        raise HTTPException(status_code=400, detail="size must be a string")
    try:
        package = package_repo.get_package(db, package_id)
    except SQLAlchemyError:
        db.rollback()
        raise HTTPException(status_code=500, detail="Database error")
    if not package:
        raise HTTPException(status_code=404, detail="Material package not found")

    materials = package.get("materials") if isinstance(package.get("materials"), dict) else {}
    metadata = materials.get("metadata") if isinstance(materials.get("metadata"), dict) else {}
    blueprint = metadata.get("blueprint_v1") if isinstance(metadata.get("blueprint_v1"), dict) else {}
    storyboard = blueprint.get("storyboard") if isinstance(blueprint.get("storyboard"), list) else []
    scenes = blueprint.get("scenes") if isinstance(blueprint.get("scenes"), list) else []
    subjects = blueprint.get("subjects") if isinstance(blueprint.get("subjects"), list) else []
    if not subjects and isinstance(materials.get("characters"), list):
        subjects = materials.get("characters") or []

    if not storyboard:
        return ok({"generated": [], "material_package_id": package_id})

    scene_by_id = {}
    for scene in scenes:
        if isinstance(scene, dict) and scene.get("id"):
            scene_by_id[scene["id"]] = scene

    images = metadata.get("images") if isinstance(metadata.get("images"), list) else []
    images = [image for image in images if isinstance(image, dict)]
    if not size:
        size = metadata.get("image_size") if isinstance(metadata.get("image_size"), str) else None
    existing_by_shot: dict[str, list[dict]] = {}
    for image in images:
        if image.get("type") != "storyboard":
            continue
        shot_id = image.get("shot_id")
        if isinstance(shot_id, str) and shot_id:
            existing_by_shot.setdefault(shot_id, []).append(image)

    generated = []
    last_storyboard_url = ""
    for shot in storyboard:
        if not isinstance(shot, dict):
            continue
        shot_id = shot.get("id")
        if not isinstance(shot_id, str) or not shot_id:
            continue
        existing_images = existing_by_shot.get(shot_id, [])
        active_existing_url = _active_storyboard_url(existing_images)
        if existing_images and not force:
            has_real = False
            for existing in existing_images:
                if not isinstance(existing, dict):
                    continue
                prompt_source = existing.get("prompt_source") or existing.get("promptSource") or ""
                provider = existing.get("provider") or ""
                if prompt_source != "demo_seed" and provider != "demo":
                    has_real = True
                    break
            if has_real:
                if active_existing_url:
                    last_storyboard_url = active_existing_url
                continue

        scene_id = shot.get("scene_id") if isinstance(shot.get("scene_id"), str) else ""
        scene = scene_by_id.get(scene_id, {}) if scene_id else {}
        prompt_parts = _build_storyboard_prompt_parts(shot, scene, blueprint)
        prompt = _render_storyboard_prompt(prompt_parts)
        ref_images = []
        scene_url = _scene_reference_url(images, scene_id)
        if scene_url:
            ref_images.append(scene_url)
        for subject_id in _extract_subject_ids(shot, subjects):
            ref_images.extend(_subject_reference_urls(images, subject_id))
        if last_storyboard_url:
            ref_images.append(last_storyboard_url)
        ref_images = _dedupe_urls(ref_images, STORYBOARD_REFERENCE_IMAGE_LIMIT)
        image_result = None
        try:
            if ref_images:
                image_result = image_service.generate_image_with_refs(prompt, ref_images, size=size)
            else:
                image_result = image_service.generate_image(prompt, size=size)
        except Exception:
            logger.exception("storyboard image generation failed package_id=%s shot_id=%s", package_id, shot_id)
        if not isinstance(image_result, dict) or not image_result.get("url"):
            continue

        for image in images:
            if image.get("type") == "storyboard" and image.get("shot_id") == shot_id:
                image["is_active"] = False

        new_image = {
            "id": new_id(),
            "type": "storyboard",
            "shot_id": shot_id,
            "scene_id": scene_id,
            "scene_name": scene.get("name") if isinstance(scene, dict) else None,
            "url": image_result.get("url"),
            "prompt": image_result.get("prompt") or prompt,
            "prompt_parts": prompt_parts,
            "prompt_source": "storyboard_autogen",
            "provider": image_result.get("provider"),
            "model": image_result.get("model"),
            "size": image_result.get("size"),
            "is_active": True,
        }
        images.append(new_image)
        generated.append(new_image)
        last_storyboard_url = new_image.get("url") or last_storyboard_url

    metadata["images"] = images
    if size:
        metadata["image_size"] = size
        image_plan = metadata.get("image_plan") if isinstance(metadata.get("image_plan"), dict) else {}
        if isinstance(image_plan, dict):
            image_plan["size"] = size
            metadata["image_plan"] = image_plan
    materials["metadata"] = metadata

    try:
        package_repo.update_package(db, package_id, {"materials": materials})
    except SQLAlchemyError:
        db.rollback()
        raise HTTPException(status_code=500, detail="Database error")

    return ok({"generated": generated, "material_package_id": package_id})


@router.post("/material-packages/{package_id}/storyboard-videos")
async def generate_storyboard_videos(
    package_id: str,
    payload: Dict[str, Any] = Body(default_factory=dict),
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    force = payload.get("force") is True
    shot_id = payload.get("shot_id")
    prompt_override = payload.get("prompt")
    feedback = payload.get("feedback")
    model = payload.get("model")
    size = payload.get("size")

    if shot_id is not None and not isinstance(shot_id, str):
        raise HTTPException(status_code=400, detail="shot_id must be a string")
    if prompt_override is not None and not isinstance(prompt_override, str):
        raise HTTPException(status_code=400, detail="prompt must be a string")
    if feedback is not None and not isinstance(feedback, str):
        raise HTTPException(status_code=400, detail="feedback must be a string")
    if model is not None and not isinstance(model, str):
        raise HTTPException(status_code=400, detail="model must be a string")
    if size is not None and not isinstance(size, str):
        raise HTTPException(status_code=400, detail="size must be a string")
    if (prompt_override or feedback) and not (isinstance(shot_id, str) and shot_id.strip()):
        raise HTTPException(status_code=400, detail="shot_id required when prompt or feedback is provided")

    try:
        package = package_repo.get_package(db, package_id)
    except SQLAlchemyError:
        db.rollback()
        raise HTTPException(status_code=500, detail="Database error")
    if not package:
        raise HTTPException(status_code=404, detail="Material package not found")

    materials = package.get("materials") if isinstance(package.get("materials"), dict) else {}
    metadata = materials.get("metadata") if isinstance(materials.get("metadata"), dict) else {}
    blueprint = metadata.get("blueprint_v1") if isinstance(metadata.get("blueprint_v1"), dict) else {}
    storyboard = blueprint.get("storyboard") if isinstance(blueprint.get("storyboard"), list) else []
    scenes = blueprint.get("scenes") if isinstance(blueprint.get("scenes"), list) else []

    if not storyboard:
        return ok({"generated": [], "material_package_id": package_id})

    scene_by_id = {}
    for scene in scenes:
        if isinstance(scene, dict) and scene.get("id"):
            scene_by_id[scene["id"]] = scene

    images = metadata.get("images") if isinstance(metadata.get("images"), list) else []
    images = [image for image in images if isinstance(image, dict)]
    videos = metadata.get("videos") if isinstance(metadata.get("videos"), list) else []
    if not size:
        size = metadata.get("video_size") if isinstance(metadata.get("video_size"), str) else None
    if not size:
        size = metadata.get("image_size") if isinstance(metadata.get("image_size"), str) else None
    videos = [video for video in videos if isinstance(video, dict)]

    existing_by_shot: dict[str, list[dict]] = {}
    for video in videos:
        if video.get("type") != "storyboard_video":
            continue
        existing_shot = video.get("shot_id")
        if isinstance(existing_shot, str) and existing_shot:
            existing_by_shot.setdefault(existing_shot, []).append(video)

    target_shots = []
    if isinstance(shot_id, str) and shot_id:
        target = next((shot for shot in storyboard if isinstance(shot, dict) and shot.get("id") == shot_id), None)
        if not target:
            raise HTTPException(status_code=404, detail="Shot not found")
        target_shots = [target]
    else:
        target_shots = [shot for shot in storyboard if isinstance(shot, dict)]

    generated = []
    skipped = []
    for shot in target_shots:
        shot_key = shot.get("id")
        if not isinstance(shot_key, str) or not shot_key:
            continue

        existing_videos = existing_by_shot.get(shot_key, [])
        should_force = force or bool(shot_id) or bool(prompt_override) or bool(feedback)
        if existing_videos and not should_force and not shot_id:
            continue

        shot_images = [
            image for image in images if image.get("type") == "storyboard" and image.get("shot_id") == shot_key
        ]
        image_url = _active_storyboard_url(shot_images)
        if not image_url:
            skipped.append({"shot_id": shot_key, "reason": "missing_storyboard_image"})
            continue

        scene_id = shot.get("scene_id") if isinstance(shot.get("scene_id"), str) else ""
        scene = scene_by_id.get(scene_id, {}) if scene_id else {}
        prompt_parts = _build_storyboard_prompt_parts(shot, scene, blueprint)
        base_prompt = _render_storyboard_prompt(prompt_parts)
        prompt = (prompt_override or base_prompt or "").strip()
        prompt_source = "storyboard_video_autogen"

        if feedback:
            prompt = llm_service.rewrite_prompt(prompt, feedback, prompt_parts)
            prompt_source = "user_feedback"
        elif prompt_override:
            prompt_source = "user_edit"

        video_result = None
        try:
            video_result = video_service.generate_video_from_image(prompt, [image_url], size=size, model=model)
        except Exception:
            logger.exception("storyboard video generation failed package_id=%s shot_id=%s", package_id, shot_key)
        if not isinstance(video_result, dict) or not video_result.get("task_id"):
            skipped.append({"shot_id": shot_key, "reason": "video_generation_failed"})
            continue

        for video in videos:
            if video.get("type") == "storyboard_video" and video.get("shot_id") == shot_key:
                video["is_active"] = False

        new_video = {
            "id": new_id(),
            "type": "storyboard_video",
            "shot_id": shot_key,
            "scene_id": scene_id,
            "scene_name": scene.get("name") if isinstance(scene, dict) else None,
            "image_url": image_url,
            "prompt": prompt,
            "prompt_parts": prompt_parts,
            "prompt_source": prompt_source,
            "provider": video_result.get("provider"),
            "model": video_result.get("model"),
            "size": video_result.get("size"),
            "task_id": video_result.get("task_id"),
            "request_id": video_result.get("request_id"),
            "task_status": video_result.get("task_status") or "PROCESSING",
            "is_active": True,
            "created_at": utc_now(),
        }
        videos.append(new_video)
        generated.append(new_video)

    metadata["videos"] = videos
    materials["metadata"] = metadata

    try:
        package_repo.update_package(db, package_id, {"materials": materials})
    except SQLAlchemyError:
        db.rollback()
        raise HTTPException(status_code=500, detail="Database error")

    return ok({"generated": generated, "skipped": skipped, "material_package_id": package_id})


@router.post("/material-packages/{package_id}/feedback")
async def regenerate_from_feedback(
    package_id: str,
    payload: Dict[str, Any] = Body(default_factory=dict),
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    if not package_id.strip():
        raise HTTPException(status_code=400, detail="package_id required")
    feedback = payload.get("feedback")
    if not isinstance(feedback, str) or not feedback.strip():
        raise HTTPException(status_code=400, detail="feedback required")
    feedback = feedback.strip()

    try:
        package = package_repo.get_package(db, package_id)
    except SQLAlchemyError:
        db.rollback()
        raise HTTPException(status_code=500, detail="Database error")
    if not package:
        raise HTTPException(status_code=404, detail="Material package not found")

    project_id = package.get("project_id")
    if not project_id:
        raise HTTPException(status_code=404, detail="Project not found")

    current_step = "outline"
    error_sent = False
    reset_generation_events(project_id)
    _emit_step(project_id, "outline", "started", "正在理解你的修改意见…")

    try:
        items = package_repo.list_packages_for_project(db, project_id)
    except SQLAlchemyError:
        db.rollback()
        publish_generation_event(
            project_id,
            {"type": "generation.error", "step": current_step, "message": "生成失败"},
        )
        raise HTTPException(status_code=500, detail="Database error")
    next_version = _next_package_version(items)

    materials = package.get("materials") if isinstance(package.get("materials"), dict) else {}
    metadata = materials.get("metadata") if isinstance(materials, dict) else {}
    previous_blueprint = metadata.get("blueprint_v1") if isinstance(metadata, dict) else {}
    previous_blueprint = previous_blueprint if isinstance(previous_blueprint, dict) else {}
    source_prompt = _extract_source_prompt(materials) or package.get("summary") or ""

    mode = metadata.get("generation_mode") if isinstance(metadata, dict) else None
    mode = mode.strip().lower() if isinstance(mode, str) else "general"
    if mode not in {"general", "pro"}:
        mode = "general"
    image_size = metadata.get("image_size") if isinstance(metadata.get("image_size"), str) else None
    image_size = image_size or settings.seedream_default_size or "960x1280"
    previous_package_context = {
        "blueprint_v1": previous_blueprint,
        "summary": metadata.get("summary") if isinstance(metadata, dict) else "",
        "keywords": metadata.get("keywords") if isinstance(metadata, dict) else [],
        "art_style": materials.get("art_style") if isinstance(materials, dict) else {},
        "subjects": materials.get("characters") if isinstance(materials, dict) else [],
        "scenes": materials.get("scenes") if isinstance(materials, dict) else [],
        "storyboard": materials.get("storyboards") if isinstance(materials, dict) else [],
    }
    logger.info(
        "llm.call stage=material_package_feedback package_id=%s mode=%s feedback_chars=%s",
        package_id,
        mode,
        len(feedback),
    )
    try:
        llm_struct = llm_service.generate_material_package(
            str(source_prompt),
            mode,
            previous_package=previous_package_context,
            feedback=feedback,
        )
        blueprint = build_blueprint(llm_struct, source_prompt=str(source_prompt))

        _emit_step(project_id, "outline", "completed", "故事梗概已完成")
        current_step = "outline"
        _emit_step(project_id, "art_style", "completed", "美术风格已确定")
        current_step = "art_style"
        _emit_step(project_id, "characters", "completed", "角色设定已完成")
        current_step = "characters"

        images: list[dict] = []
        _emit_step(project_id, "character_images", "started", "正在生成角色三视图…")
        current_step = "character_images"
        for subject in blueprint.get("subjects", []):
            subject_id = subject.get("id")
            subject_name = subject.get("name")
            sheet_prompt = _build_character_sheet_prompt(subject, blueprint)
            if not sheet_prompt:
                sheet_prompt = blueprint["summary"]["logline"]
            image_result = None
            try:
                image_result = image_service.generate_image(sheet_prompt, size=image_size)
            except Exception:
                logger.exception(
                    "generation stage=character_sheet failed package_id=%s subject_id=%s",
                    package_id,
                    subject_id,
                )
            if not isinstance(image_result, dict) or not image_result.get("url"):
                raise HTTPException(status_code=502, detail="Character image generation failed")
            prompt_parts = _build_character_prompt_parts(subject, blueprint, sheet_prompt)
            images.append(
                {
                    "id": new_id(),
                    "type": "character_sheet",
                    "subject_id": subject_id,
                    "subject_name": subject_name,
                    "url": image_result.get("url"),
                    "prompt": image_result.get("prompt") or sheet_prompt,
                    "prompt_parts": prompt_parts,
                    "provider": image_result.get("provider"),
                    "model": image_result.get("model"),
                    "size": image_result.get("size"),
                }
            )
        _emit_step(project_id, "character_images", "completed", "角色三视图已生成")
        current_step = "character_images"

        _emit_step(project_id, "scenes", "completed", "场景设定已完成")
        current_step = "scenes"
        _emit_step(project_id, "scene_images", "started", "正在生成场景空间图…")
        current_step = "scene_images"
        for scene in blueprint.get("scenes", []):
            scene_id = scene.get("id")
            scene_prompt = scene.get("prompt_hint") or scene.get("description") or blueprint["summary"]["logline"]
            image_result = None
            try:
                image_result = image_service.generate_image(scene_prompt, size=image_size)
            except Exception:
                image_result = None
            if isinstance(image_result, dict) and image_result.get("url"):
                images.append(
                    {
                        "id": new_id(),
                        "type": "scene",
                        "scene_id": scene_id,
                        "url": image_result.get("url"),
                        "prompt": image_result.get("prompt") or scene_prompt,
                        "prompt_parts": {
                            "content": scene_prompt,
                            "style": blueprint.get("art_style", {}).get("style_prompt") or "",
                            "constraints": SCENE_QUALITY_CONSTRAINTS,
                        },
                        "provider": image_result.get("provider"),
                        "model": image_result.get("model"),
                        "size": image_result.get("size"),
                    }
                )
        _emit_step(project_id, "scene_images", "completed", "场景空间图已生成")
        current_step = "scene_images"

        _emit_step(project_id, "storyboard", "completed", "分镜剧本已完成")
        current_step = "storyboard"

        package_name = llm_service.generate_package_name(
            str(source_prompt),
            blueprint["summary"]["logline"],
        )
        image_size = metadata.get("image_size") if isinstance(metadata.get("image_size"), str) else None
        image_size = image_size or settings.seedream_default_size or "960x1280"
        materials_payload = {
            "metadata": {
                "summary": blueprint["summary"]["logline"],
                "keywords": blueprint["summary"]["keywords"],
                "blueprint_v1": blueprint,
                "image_plan": {
                    "prompt": blueprint["scenes"][0]["prompt_hint"]
                    if blueprint.get("scenes")
                    else blueprint["summary"]["synopsis"],
                    "style": None,
                    "aspect_ratio": "3:4",
                    "size": image_size,
                    "seed": None,
                },
                "image_size": image_size,
                "images": images,
                "video_plan": {"status": "pending", "items": []},
                "package_version": next_version,
                "package_name": package_name,
                "parent_package_id": package_id,
                "user_prompt": str(source_prompt),
                "user_feedback": feedback,
                "generation_mode": mode,
            },
            "art_style": {
                "style_name": blueprint.get("art_style", {}).get("style_name", ""),
                "description": blueprint.get("art_style", {}).get("style_prompt", ""),
            },
            "characters": [],
            "scenes": [],
            "storyboards": [],
        }

        new_package = package_repo.create_package(
            db,
            project_id=project_id,
            package_name=package_name,
            status="completed",
            materials=materials_payload,
            parent_id=package_id,
        )

        project_repo.update_project(
            db,
            project_id,
            {"last_material_package_id": new_package["id"]},
        )
        _emit_step(project_id, "done", "completed", "素材包已生成")
        current_step = "done"
        return ok(new_package)
    except HTTPException:
        if not error_sent:
            error_sent = True
            publish_generation_event(
                project_id,
                {"type": "generation.error", "step": current_step, "message": "生成失败"},
            )
        raise
    except (RuntimeError, ValueError) as exc:
        logger.exception("LLM feedback generation failed for package_id=%s", package_id)
        if not error_sent:
            error_sent = True
            publish_generation_event(
                project_id,
                {"type": "generation.error", "step": current_step, "message": "生成失败"},
            )
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    except SQLAlchemyError:
        db.rollback()
        if not error_sent:
            error_sent = True
            publish_generation_event(
                project_id,
                {"type": "generation.error", "step": current_step, "message": "生成失败"},
            )
        raise HTTPException(status_code=500, detail="Database error")
    except Exception as exc:
        logger.exception("LLM feedback generation failed for package_id=%s", package_id)
        if not error_sent:
            error_sent = True
            publish_generation_event(
                project_id,
                {"type": "generation.error", "step": current_step, "message": "生成失败"},
            )
        raise HTTPException(status_code=502, detail="LLM generation failed") from exc
