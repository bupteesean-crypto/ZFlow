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
from app.services.generation_todo import TODO_LIST
from app.services.image_service import ImageService
from app.services.llm_service import LLMService
from app.services.model_registry import select_enabled_model
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
    Path(__file__).resolve().parents[4] / "worker" / "prompts" / "image" / "constraints"
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
    "summary": 20,
    "art_style": 40,
    "characters": 60,
    "scenes": 80,
    "storyboard": 90,
    "done": 100,
}


def _emit_assistant_message(project_id: str, content: str) -> None:
    publish_generation_event(
        project_id,
        {"type": "assistant_message", "content": content},
    )


def _emit_todo_list(project_id: str) -> None:
    publish_generation_event(
        project_id,
        {"type": "todo_list", "items": TODO_LIST},
    )


def _emit_todo_update(project_id: str, item_id: str, status: str) -> None:
    publish_generation_event(
        project_id,
        {"type": "todo_update", "id": item_id, "status": status},
    )


def _emit_content_update(project_id: str, section: str, data: object) -> None:
    publish_generation_event(
        project_id,
        {"type": "content_update", "section": section, "data": data},
    )


def _emit_done(project_id: str, package_id: str | None) -> None:
    publish_generation_event(
        project_id,
        {"type": "done", "package_id": package_id},
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


def _normalize_input_config(value: object) -> dict:
    if isinstance(value, dict):
        return value
    return {}


def _normalize_documents(value: object) -> list[dict]:
    if not isinstance(value, list):
        return []
    items = []
    for item in value:
        if isinstance(item, dict):
            items.append(item)
    return items


def _resolve_image_size(input_config: dict) -> str:
    raw_size = input_config.get("image_size") if isinstance(input_config.get("image_size"), str) else ""
    if raw_size.strip():
        return raw_size.strip()
    ratio = input_config.get("aspect_ratio") if isinstance(input_config.get("aspect_ratio"), str) else ""
    ratio = ratio.strip()
    size_map = {
        "16:9": "1280x720",
        "4:3": "1024x768",
        "2.35:1": "1280x544",
        "19:16": "1140x960",
        "3:4": "960x1280",
    }
    if ratio in size_map:
        return size_map[ratio]
    return settings.seedream_default_size or "960x1280"


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
        "生成同一个角色的三视图角色设定图（turnaround / model sheet）。",
        "",
        f"角色：{name}",
        f"描述：{description}",
    ]
    if traits_text:
        lines.append(f"特征：{traits_text}")
    if style_prompt:
        lines.append(f"风格：{style_prompt}")
    lines.extend(
        [
            "",
            "要求：",
            "- 画面必须同时包含【正面视图 / 侧面视图 / 背面视图】，三个视图横向并排展示",
            "- 角色一致性要求：五官一致、发型一致、服装款式一致、颜色一致、身材比例一致",
            "- 姿态：标准站立中立姿态（neutral pose），双脚自然站立，身体直立，无动作、无夸张姿势",
            "- 视角：正交视图（orthographic view），不允许透视，不允许镜头角度变化，仅正面/侧面/背面三种视角",
            "- 光照：均匀棚拍光照，无强阴影，无戏剧化光影",
            "- 背景：纯白色或浅灰色背景，无场景、无道具、无装饰",
            "- 绘制：高细节，线条清晰，轮廓明确，适合作为角色参考设定图使用",
            "- 强约束：禁止改变服装，禁止改变颜色，禁止增加动作，禁止透视，禁止生成多个人物",
            "- 禁止文字、水印、Logo、字幕",
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
    input_config: dict,
    task_id: str,
    trace_id: str,
    image_model_id: str | None,
    image_model: str | None,
) -> None:
    db = SessionLocal()
    current_step = "summary"
    error_sent = False
    reset_generation_events(project_id)
    _update_task(task_id, status="running", progress=0)
    _emit_assistant_message(project_id, "我将按以下步骤为你生成素材包，请稍等")
    _emit_todo_list(project_id)
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
        summary, keywords = llm_service.generate_summary(
            llm_input,
            mode,
            documents=documents,
            input_config=input_config,
        )
        _emit_todo_update(project_id, "summary", "done")
        _emit_content_update(project_id, "summary", summary)
        _update_task(task_id, progress=STEP_PROGRESS["summary"])

        current_step = "art_style"
        art_style = llm_service.generate_art_style(
            summary,
            llm_input,
            mode,
            documents=documents,
            input_config=input_config,
        )
        _emit_todo_update(project_id, "art_style", "done")
        _emit_content_update(project_id, "art_style", art_style)
        _update_task(task_id, progress=STEP_PROGRESS["art_style"])

        current_step = "package_name"
        package_name = llm_service.generate_package_name(summary, art_style)
        _emit_content_update(project_id, "package_name", package_name)

        current_step = "characters"
        subjects = llm_service.generate_characters(
            summary,
            art_style,
            llm_input,
            mode,
            documents=documents,
            input_config=input_config,
        )
        _emit_todo_update(project_id, "characters", "done")
        _emit_content_update(project_id, "characters", subjects)
        _update_task(task_id, progress=STEP_PROGRESS["characters"])

        current_step = "scenes"
        scenes = llm_service.generate_scenes(
            summary,
            art_style,
            subjects,
            llm_input,
            mode,
            documents=documents,
            input_config=input_config,
        )
        _emit_todo_update(project_id, "scenes", "done")
        _emit_content_update(project_id, "scenes", scenes)
        _update_task(task_id, progress=STEP_PROGRESS["scenes"])

        current_step = "storyboard"
        storyboard = llm_service.generate_storyboard(
            summary,
            art_style,
            subjects,
            scenes,
            llm_input,
            mode,
            documents=documents,
            input_config=input_config,
        )
        _emit_todo_update(project_id, "storyboard", "done")
        _emit_content_update(project_id, "storyboard", storyboard)
        _update_task(task_id, progress=STEP_PROGRESS["storyboard"])

        llm_payload = {
            "summary": summary,
            "keywords": keywords,
            "art_style": art_style,
            "subjects": subjects,
            "scenes": scenes,
            "storyboard": storyboard,
        }
        blueprint = build_blueprint(llm_payload, source_prompt=llm_input)

        image_size = _resolve_image_size(input_config)
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
                image_result = image_service.generate_image(sheet_prompt, size=image_size, model=image_model)
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
                    "model_id": image_model_id,
                    "size": image_result.get("size"),
                }
            )

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
                image_result = image_service.generate_image(scene_prompt, size=image_size, model=image_model)
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
                        "model_id": image_model_id,
                        "size": image_result.get("size"),
                    }
                )

        packages = package_repo.list_packages_for_project(db, project_id)
        package_version = _next_package_version(packages)

        first_scene = blueprint["scenes"][0] if blueprint.get("scenes") else {}
        image_plan = {
            "prompt": first_scene.get("prompt_hint") or blueprint["summary"]["synopsis"],
            "style": None,
            "aspect_ratio": (
                input_config.get("aspect_ratio") if isinstance(input_config, dict) else None
            )
            or "3:4",
            "size": image_size,
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
                    "image_size": image_size,
                    "images": images,
                    "video_plan": {"status": "pending", "items": []},
                    "package_version": package_version,
                    "package_name": package_name,
                    "parent_package_id": None,
                    "user_prompt": llm_input,
                    "user_feedback": None,
                    "generation_mode": mode,
                    "image_model_id": image_model_id,
                    "input_config": input_config,
                    "input_documents": documents,
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
        _emit_done(project_id, package["id"])
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
                if payload.get("type") == "done":
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
    documents = _normalize_documents(payload.get("documents"))
    input_config = _normalize_input_config(payload.get("input_config"))
    if mode == "pro" and not documents:
        metadata = project.get("metadata") if isinstance(project.get("metadata"), dict) else {}
        attachments = metadata.get("attachments") if isinstance(metadata.get("attachments"), list) else []
        documents = _normalize_documents(attachments)
    image_model_id = payload.get("image_model_id")
    if image_model_id is not None and not isinstance(image_model_id, str):
        raise HTTPException(status_code=400, detail="image_model_id must be a string")
    image_model_id = image_model_id.strip() if isinstance(image_model_id, str) and image_model_id.strip() else None
    if not image_model_id and isinstance(input_config.get("image_model_id"), str):
        image_model_id = input_config.get("image_model_id").strip() or None
    image_model = None
    if image_model_id:
        try:
            model_spec = select_enabled_model(image_model_id, "image")
        except ValueError:
            raise HTTPException(status_code=400, detail="image_model_id not available")
        image_model = model_spec.model if model_spec else None
    if input_config:
        try:
            project_repo.update_project(db, project_id, {"input_config": input_config})
        except SQLAlchemyError:
            db.rollback()
            raise HTTPException(status_code=500, detail="Database error")
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
        input_config,
        task_id,
        trace_id,
        image_model_id,
        image_model,
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
