from fastapi import APIRouter

from app.api.v1 import auth, exports, generation, images, material_packages, models, projects, text

router = APIRouter(prefix="/api/v1")
router.include_router(auth.router)
router.include_router(projects.router)
router.include_router(material_packages.router)
router.include_router(generation.router)
router.include_router(images.router)
router.include_router(models.router)
router.include_router(exports.router)
router.include_router(text.router)
