from fastapi import APIRouter

from app.api.v1 import auth, generation, material_packages, projects

router = APIRouter(prefix="/api/v1")
router.include_router(auth.router)
router.include_router(projects.router)
router.include_router(material_packages.router)
router.include_router(generation.router)
