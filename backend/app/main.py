from fastapi import FastAPI

from app.api.health import router as health_router
from app.api.tasks import router as tasks_router
from app.core.config import settings
from app.core.logging import setup_logging

setup_logging()

app = FastAPI(title=settings.app_name)
app.include_router(health_router)
app.include_router(tasks_router)
