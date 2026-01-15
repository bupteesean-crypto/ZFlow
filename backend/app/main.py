from dotenv import load_dotenv

load_dotenv()
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from app.api.health import router as health_router
from app.api.v1.response import fail
from app.api.v1.router import router as v1_router
from app.core.config import settings
from app.core.logging import setup_logging

setup_logging()

app = FastAPI(title=settings.app_name)
app.mount(
    "/static/demo_material",
    StaticFiles(directory=Path(__file__).resolve().parent / "cut_demo_material"),
    name="demo-material",
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(health_router)
app.include_router(v1_router)


def _error_code_from_status(status_code: int) -> int:
    mapping = {
        400: 1001,
        401: 1002,
        403: 1003,
        404: 1004,
        409: 1005,
    }
    return mapping.get(status_code, 1000)


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    if request.url.path.startswith("/api/v1"):
        return JSONResponse(
            status_code=exc.status_code,
            content=fail(_error_code_from_status(exc.status_code), str(exc.detail)),
        )
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    if request.url.path.startswith("/api/v1"):
        return JSONResponse(status_code=500, content=fail(1000, "internal error"))
    return JSONResponse(status_code=500, content={"detail": "internal error"})
