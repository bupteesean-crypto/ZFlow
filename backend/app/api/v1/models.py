from fastapi import APIRouter, HTTPException, Query

from app.api.v1.response import ok
from app.services.model_registry import list_models

router = APIRouter(prefix="/models", tags=["models"])


@router.get("")
async def list_models(model_type: str | None = Query(default=None, alias="type")):
    if model_type is not None and model_type not in {"image", "video"}:
        raise HTTPException(status_code=400, detail="type must be image or video")
    items = list_models(model_type)
    return ok({"list": items})
