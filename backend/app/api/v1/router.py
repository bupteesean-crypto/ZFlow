from fastapi import APIRouter

from app.api.v1 import (
    attachments,
    auth,
    exports,
    generation,
    images,
    material_packages,
    models,
    music,
    projects,
    text,
    tts,
    voice_roles,
)

router = APIRouter(prefix="/api/v1")
router.include_router(auth.router)
router.include_router(projects.router)
router.include_router(attachments.router)
router.include_router(material_packages.router)
router.include_router(generation.router)
router.include_router(images.router)
router.include_router(models.router)
router.include_router(exports.router)
router.include_router(text.router)
router.include_router(voice_roles.router)
router.include_router(tts.router)
router.include_router(music.router)
