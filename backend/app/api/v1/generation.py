import logging
from pathlib import Path
import time
from queue import Empty
from typing import Any, Dict

from fastapi import APIRouter, BackgroundTasks, Body, Depends, HTTPException
from starlette.responses import StreamingResponse
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.api.v1.response import ok
from app.core.config import settings
from app.core.events import emit_event, new_trace_id
from app.db.models import utc_now as db_utc_now
from app.db.session import SessionLocal, get_db
from app.repositories import material_packages as package_repo
from app.repositories import projects as project_repo
from app.services.blueprint_service import build_blueprint
from app.services.generation_events import (
    format_sse,
    publish_generation_event,
    reset_generation_events,
    subscribe_generation_events,
    unsubscribe_generation_events,
)
from app.services.image_service import ImageService
from app.services.llm_service import LLMService
from app.store import GENERATION_TASKS, GENERATION_TRACES, new_id, utc_now

router = APIRouter(prefix="/generation", tags=["generation"])
llm_service = LLMService()
image_service = ImageService()
logger = logging.getLogger(__name__)

_DEFAULT_SCENE_QUALITY_CONSTRAINTS = (
    "no text, no captions, no logos, no watermark\n"
    "no people, no characters, empty environment\n"
    "avoid low-quality artifacts or distortion\n"
    "avoid malformed anatomy or extra limbs\n"
    "no busy patterns"
)
_DEFAULT_CHARACTER_QUALITY_CONSTRAINTS = (
    "no text, no captions, no logos, no watermark\n"
    "avoid low-quality artifacts or distortion\n"
    "avoid malformed anatomy or extra limbs\n"
    "front view, side view, back view in one canvas\n"
    "front shows face and torso, side shows profile silhouette, back shows hair and back details\n"
    "evenly spaced, same scale and proportions\n"
    "consistent line weight and lighting\n"
    "neutral background"
)
_CONSTRAINTS_DIR = (
    Path(__file__).resolve().parents[3] / "worker" / "prompts" / "image" / "constraints"
)
_SCENE_CONSTRAINTS_PATH = _CONSTRAINTS_DIR / "scene_quality.txt"
_CHARACTER_CONSTRAINTS_PATH = _CONSTRAINTS_DIR / "character_quality.txt"


def _load_constraints(path: Path, fallback: str) -> str:
    try:
        return path.read_text(encoding="utf-8").strip() or fallback
    except OSError:
        logger.warning("Failed to read constraint prompt at %s; using fallback", path)
        return fallback


SCENE_QUALITY_CONSTRAINTS = _load_constraints(_SCENE_CONSTRAINTS_PATH, _DEFAULT_SCENE_QUALITY_CONSTRAINTS)
CHARACTER_QUALITY_CONSTRAINTS = _load_constraints(
    _CHARACTER_CONSTRAINTS_PATH, _DEFAULT_CHARACTER_QUALITY_CONSTRAINTS
)

STEP_PROGRESS = {
    "outline": 10,
    "art_style": 20,
    "characters": 30,
    "character_images": 45,
    "scenes": 60,
    "scene_images": 80,
    "storyboard": 90,
    "done": 100,
}


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


def _update_task(task_id: str, status: str | None = None, progress: int | None = None) -> None:
    task = GENERATION_TASKS.get(task_id)
    if not task:
        return
    if status:
        task["status"] = status
    if progress is not None:
        task["progress"] = progress
    task["updated_at"] = utc_now()


def _join_keywords(keywords: list[str]) -> str:
    return ", ".join([item for item in keywords if isinstance(item, str) and item.strip()])


def _build_style_prompt(art_style: dict) -> str:
    style_prompt = art_style.get("style_prompt") if isinstance(art_style, dict) else ""
    style_prompt = style_prompt.strip() if isinstance(style_prompt, str) else ""
    palette = art_style.get("palette") if isinstance(art_style.get("palette"), list) else []
    palette = [str(item).strip() for item in palette if str(item).strip()] if isinstance(palette, list) else []
    if palette:
        palette_line = f"Palette: {', '.join(palette)}"
        style_prompt = f"{style_prompt}\n{palette_line}".strip() if style_prompt else palette_line
    return style_prompt


def _compose_image_prompt(base_prompt: str, style_prompt: str, constraints: str) -> str:
    cleaned = (base_prompt or "").strip()
    sections = [cleaned] if cleaned else []
    lower = cleaned.lower()
    if style_prompt and "style:" not in lower and "风格" not in cleaned:
        sections.append(f"Style:\n{style_prompt}")
    if constraints and "constraints:" not in lower and "约束" not in cleaned:
        sections.append(f"Constraints:\n{constraints}")
    return "\n\n".join([section for section in sections if section]).strip()


def _build_scene_prompt_parts(scene: dict, blueprint: dict) -> dict:
    summary = blueprint.get("summary", {}) if isinstance(blueprint, dict) else {}
    art_style = blueprint.get("art_style", {}) if isinstance(blueprint, dict) else {}
    description = scene.get("description") or summary.get("synopsis") or ""
    mood = scene.get("mood") or "neutral"
    keywords = summary.get("keywords") if isinstance(summary.get("keywords"), list) else []
    content_lines = [f"Scene summary: {description}", f"Mood: {mood}"]
    keywords_text = _join_keywords(keywords)
    if keywords_text:
        content_lines.append(f"Keywords: {keywords_text}")

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
        "constraints": SCENE_QUALITY_CONSTRAINTS,
    }


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


def _simulate_generation(task_id: str) -> None:
    task = GENERATION_TASKS.get(task_id)
    if not task:
        return
    trace_id = GENERATION_TRACES.get(task_id)
    db = SessionLocal()
    try:
        try:
            project = project_repo.get_project(db, task["project_id"])
        except SQLAlchemyError:
            db.rollback()
            return
        if not project:
            return

        task["status"] = "running"
        task["progress"] = 10
        task["updated_at"] = utc_now()
        emit_event(
            "generation.progressed",
            {
                "project_id": task["project_id"],
                "task_id": task_id,
                "progress": task["progress"],
                "status": task["status"],
            },
            trace_id=trace_id,
        )
        time.sleep(1)

        task["progress"] = 60
        task["updated_at"] = utc_now()
        emit_event(
            "generation.progressed",
            {
                "project_id": task["project_id"],
                "task_id": task_id,
                "progress": task["progress"],
                "status": task["status"],
            },
            trace_id=trace_id,
        )
        time.sleep(1)

        task["status"] = "completed"
        task["progress"] = 100
        task["updated_at"] = utc_now()
        emit_event(
            "generation.completed",
            {
                "project_id": task["project_id"],
                "task_id": task_id,
                "progress": task["progress"],
                "status": task["status"],
            },
            trace_id=trace_id,
        )

        package_id = task.get("material_package_id")
        if package_id:
            try:
                package_repo.update_package(
                    db,
                    package_id,
                    {
                        "status": "completed",
                        "summary": "Mock material package generated",
                        "generated_at": db_utc_now(),
                    },
                )
            except SQLAlchemyError:
                db.rollback()
                return

        try:
            project_repo.update_project(
                db,
                task["project_id"],
                {"status": "editing", "stage": "editing", "progress": 50},
            )
        except SQLAlchemyError:
            db.rollback()
            return
    finally:
        db.close()


def _run_generation_task(
    project_id: str,
    llm_input: str,
    mode: str,
    documents: list,
    task_id: str,
    trace_id: str,
) -> None:
    db = SessionLocal()
    current_step = "outline"
    error_sent = False
    reset_generation_events(project_id)
    _update_task(task_id, status="running", progress=0)
    _emit_step(project_id, "outline", "started", "正在理解你的创作意图…")
    emit_event(
        "generation.progressed",
        {
            "project_id": project_id,
            "task_id": task_id,
            "progress": 0,
            "status": "running",
        },
        trace_id=trace_id,
    )
    try:
        started_at = time.perf_counter()
        llm_result = llm_service.generate_material_package(str(llm_input), mode, documents=documents)
        duration_ms = int((time.perf_counter() - started_at) * 1000)
        logger.info(
            "generation stage=llm project_id=%s mode=%s duration_ms=%s",
            project_id,
            mode,
            duration_ms,
        )

        llm_payload = llm_result if isinstance(llm_result, dict) else {}
        blueprint = build_blueprint(llm_payload, source_prompt=llm_input)

        _emit_step(project_id, "outline", "completed", "故事梗概已完成")
        current_step = "outline"
        _update_task(task_id, progress=STEP_PROGRESS["outline"])
        _emit_step(project_id, "art_style", "completed", "美术风格已确定")
        current_step = "art_style"
        _update_task(task_id, progress=STEP_PROGRESS["art_style"])
        image_size = settings.seedream_default_size or "960x1280"
        _emit_step(project_id, "characters", "completed", "角色设定已完成")
        current_step = "characters"
        _update_task(task_id, progress=STEP_PROGRESS["characters"])

        _emit_step(project_id, "character_images", "started", "正在生成角色三视图…")
        current_step = "character_images"
        images: list[dict] = []
        for subject in blueprint.get("subjects", []):
            subject_id = subject.get("id")
            subject_name = subject.get("name")
            base_prompt = subject.get("image_prompt") if isinstance(subject.get("image_prompt"), str) else ""
            if base_prompt.strip():
                sheet_prompt = _compose_image_prompt(
                    base_prompt,
                    _build_style_prompt(blueprint.get("art_style", {})),
                    CHARACTER_QUALITY_CONSTRAINTS,
                )
            else:
                sheet_prompt = _build_character_sheet_prompt(subject, blueprint) or blueprint["summary"]["logline"]
            image_result = None
            try:
                image_result = image_service.generate_image(sheet_prompt, size=image_size)
            except Exception:
                logger.exception(
                    "generation stage=character_sheet failed project_id=%s subject_id=%s",
                    project_id,
                    subject_id,
                )
            if not isinstance(image_result, dict) or not image_result.get("url"):
                raise ValueError("Character image generation failed")
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
        _update_task(task_id, progress=STEP_PROGRESS["character_images"])

        _emit_step(project_id, "scenes", "completed", "场景设定已完成")
        current_step = "scenes"
        _update_task(task_id, progress=STEP_PROGRESS["scenes"])

        _emit_step(project_id, "scene_images", "started", "正在生成场景空间图…")
        current_step = "scene_images"
        for scene in blueprint.get("scenes", []):
            scene_id = scene.get("id")
            base_prompt = scene.get("image_prompt") if isinstance(scene.get("image_prompt"), str) else ""
            if base_prompt.strip():
                scene_prompt = _compose_image_prompt(
                    base_prompt,
                    _build_style_prompt(blueprint.get("art_style", {})),
                    SCENE_QUALITY_CONSTRAINTS,
                )
            else:
                scene_prompt = scene.get("prompt_hint") or scene.get("description") or blueprint["summary"]["logline"]
            logger.info("generation stage=image_plan project_id=%s scene_id=%s", project_id, scene_id)
            image_result = None
            try:
                image_started_at = time.perf_counter()
                image_result = image_service.generate_image(scene_prompt, size=image_size)
                image_duration_ms = int((time.perf_counter() - image_started_at) * 1000)
                logger.info(
                    "generation stage=image_gen project_id=%s scene_id=%s duration_ms=%s request_id=%s",
                    project_id,
                    scene_id,
                    image_duration_ms,
                    (image_result or {}).get("request_id"),
                )
            except Exception:
                logger.exception(
                    "generation stage=image_gen failed project_id=%s scene_id=%s",
                    project_id,
                    scene_id,
                )
            if isinstance(image_result, dict) and image_result.get("url"):
                prompt_parts = _build_scene_prompt_parts(scene, blueprint)
                images.append(
                    {
                        "id": new_id(),
                        "type": "scene",
                        "scene_id": scene_id,
                        "url": image_result.get("url"),
                        "prompt": image_result.get("prompt") or scene_prompt,
                        "prompt_parts": prompt_parts,
                        "provider": image_result.get("provider"),
                        "model": image_result.get("model"),
                        "size": image_result.get("size"),
                    }
                )

        _emit_step(project_id, "scene_images", "completed", "场景空间图已生成")
        current_step = "scene_images"
        _update_task(task_id, progress=STEP_PROGRESS["scene_images"])

        _emit_step(project_id, "storyboard", "completed", "分镜剧本已完成")
        current_step = "storyboard"
        _update_task(task_id, progress=STEP_PROGRESS["storyboard"])

        packages = package_repo.list_packages_for_project(db, project_id)
        package_version = _next_package_version(packages)
        package_name = llm_service.generate_package_name(
            str(llm_input),
            blueprint["summary"]["logline"],
        )

        first_scene = blueprint["scenes"][0] if blueprint.get("scenes") else {}
        image_plan = {
            "prompt": first_scene.get("prompt_hint") or blueprint["summary"]["synopsis"],
            "style": None,
            "aspect_ratio": "3:4",
            "size": settings.seedream_default_size or "960x1280",
            "seed": None,
        }

        package = package_repo.create_package(
            db,
            project_id=project_id,
            package_name=package_name,
            status="completed",
            materials={
                "metadata": {
                    "summary": blueprint["summary"]["logline"],
                    "keywords": blueprint["summary"]["keywords"],
                    "blueprint_v1": blueprint,
                    "image_plan": image_plan,
                    "image_size": settings.seedream_default_size or "960x1280",
                    "images": images,
                    "video_plan": {"status": "pending", "items": []},
                    "package_version": package_version,
                    "package_name": package_name,
                    "parent_package_id": None,
                    "user_prompt": llm_input,
                    "user_feedback": None,
                    "generation_mode": mode,
                },
                "art_style": {
                    "style_name": blueprint.get("art_style", {}).get("style_name", ""),
                    "description": blueprint.get("art_style", {}).get("style_prompt", ""),
                },
                "characters": [],
                "scenes": [],
                "storyboards": [],
            },
        )

        project_repo.update_project(
            db,
            project_id,
            {
                "last_material_package_id": package["id"],
                "status": "generating",
                "stage": "generating",
                "progress": 5,
            },
        )
        task = GENERATION_TASKS.get(task_id)
        if task is not None:
            task["material_package_id"] = package["id"]
        _emit_step(project_id, "done", "completed", "素材包已生成")
        current_step = "done"
        _update_task(task_id, status="completed", progress=STEP_PROGRESS["done"])
        emit_event(
            "generation.completed",
            {
                "project_id": project_id,
                "task_id": task_id,
                "material_package_id": package["id"],
                "progress": STEP_PROGRESS["done"],
                "status": "completed",
            },
            trace_id=trace_id,
        )
    except Exception:
        logger.exception("generation failed project_id=%s", project_id)
        _update_task(task_id, status="failed", progress=0)
        if not error_sent:
            error_sent = True
            publish_generation_event(
                project_id,
                {"type": "generation.error", "step": current_step, "message": "生成失败"},
            )
        emit_event(
            "generation.completed",
            {
                "project_id": project_id,
                "task_id": task_id,
                "status": "failed",
            },
            trace_id=trace_id,
        )
    finally:
        db.close()


@router.get("/stream/{project_id}")
async def stream_generation(project_id: str) -> StreamingResponse:
    if not project_id.strip():
        raise HTTPException(status_code=400, detail="project_id required")
    queue, history = subscribe_generation_events(project_id)

    def event_stream():
        try:
            for payload in history:
                yield format_sse(payload)
            while True:
                try:
                    payload = queue.get(timeout=15)
                except Empty:
                    yield ": ping\n\n"
                    continue
                yield format_sse(payload)
                if payload.get("type") == "generation.error":
                    break
                if (
                    payload.get("type") == "generation.step"
                    and payload.get("step") == "done"
                    and payload.get("status") == "completed"
                ):
                    break
        finally:
            unsubscribe_generation_events(project_id, queue)

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )


@router.post("/start")
async def start_generation(
    background_tasks: BackgroundTasks,
    payload: Dict[str, Any] = Body(default_factory=dict),
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    project_id = payload.get("project_id")
    if not isinstance(project_id, str) or not project_id.strip():
        raise HTTPException(status_code=400, detail="project_id required")
    try:
        project = project_repo.get_project(db, project_id)
    except SQLAlchemyError:
        db.rollback()
        raise HTTPException(status_code=500, detail="Database error")
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    prompt = payload.get("prompt")
    if isinstance(prompt, str) and prompt.strip():
        llm_input = prompt.strip()
    else:
        llm_input = project.get("description") or project.get("name") or ""
    if not isinstance(llm_input, str) or not llm_input.strip():
        raise HTTPException(status_code=400, detail="prompt required")
    mode = payload.get("mode")
    mode = mode.strip().lower() if isinstance(mode, str) else "general"
    if mode not in {"general", "pro"}:
        mode = "general"
    documents = payload.get("documents")
    documents = documents if isinstance(documents, list) else []
    task_id = new_id()
    trace_id = new_trace_id()
    task = {
        "id": task_id,
        "project_id": project_id,
        "status": "pending",
        "progress": 0,
        "created_at": utc_now(),
        "updated_at": utc_now(),
    }
    GENERATION_TASKS[task_id] = task
    GENERATION_TRACES[task_id] = trace_id
    emit_event(
        "generation.started",
        {
            "project_id": project_id,
            "task_id": task_id,
            "material_package_id": None,
        },
        trace_id=trace_id,
    )
    reset_generation_events(project_id)
    background_tasks.add_task(
        _run_generation_task,
        project_id,
        llm_input,
        mode,
        documents,
        task_id,
        trace_id,
    )
    return ok(task)


@router.get("/progress/{project_id}")
async def get_generation_progress(
    project_id: str,
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
    tasks = [task for task in GENERATION_TASKS.values() if task["project_id"] == project_id]
    return ok({"list": tasks})


@router.post("/retry/{task_id}")
async def retry_generation(
    task_id: str,
    background_tasks: BackgroundTasks,
) -> Dict[str, Any]:
    if not task_id.strip():
        raise HTTPException(status_code=400, detail="task_id required")
    task = GENERATION_TASKS.get(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    task["status"] = "pending"
    task["progress"] = 0
    task["updated_at"] = utc_now()
    trace_id = GENERATION_TRACES.get(task_id)
    emit_event(
        "generation.started",
        {
            "project_id": task["project_id"],
            "task_id": task_id,
            "material_package_id": task.get("material_package_id"),
            "retry": True,
        },
        trace_id=trace_id,
    )
    background_tasks.add_task(_simulate_generation, task_id)
    return ok(task)


@router.post("/skip/{task_id}")
async def skip_generation(task_id: str) -> Dict[str, Any]:
    if not task_id.strip():
        raise HTTPException(status_code=400, detail="task_id required")
    task = GENERATION_TASKS.get(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    task["status"] = "failed"
    task["updated_at"] = utc_now()
    trace_id = GENERATION_TRACES.get(task_id)
    emit_event(
        "generation.completed",
        {
            "project_id": task["project_id"],
            "task_id": task_id,
            "status": task["status"],
            "skipped": True,
        },
        trace_id=trace_id,
    )
    return ok(task)
