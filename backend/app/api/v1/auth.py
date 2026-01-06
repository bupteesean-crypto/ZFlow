from typing import Any, Dict

from fastapi import APIRouter, Body, HTTPException

from app.api.v1.response import ok
from app.store import SESSIONS, USERS_BY_PHONE, new_id, utc_now

router = APIRouter(prefix="/auth", tags=["auth"])


def _build_user(phone: str, user_type: str) -> Dict[str, Any]:
    user_id = new_id()
    return {
        "id": user_id,
        "uid": user_id[:8],
        "username": f"user_{phone[-4:]}",
        "phone": phone,
        "user_type": user_type,
        "avatar_url": None,
        "membership": "demo",
        "points": {"current": 0, "paid": 0, "bonus": 0},
        "quota_info": {"daily_limit": 10, "used": 0, "reset_at": utc_now(), "remaining": 10},
        "created_at": utc_now(),
        "updated_at": utc_now(),
    }


@router.post("/login")
async def login(payload: Dict[str, Any] = Body(default_factory=dict)) -> Dict[str, Any]:
    phone = payload.get("phone")
    code = payload.get("code")
    invite_code = payload.get("invite_code")

    if not phone or not code:
        raise HTTPException(status_code=400, detail="phone and code required")

    user_type = "team" if invite_code else "personal"
    user = USERS_BY_PHONE.get(phone)
    if not user:
        user = _build_user(phone, user_type)
        USERS_BY_PHONE[phone] = user
    else:
        user["user_type"] = user_type
        user["updated_at"] = utc_now()

    session_token = new_id()
    refresh_token = new_id()
    current_space = {
        "type": user_type,
        "space_id": None,
        "space_name": "Personal Space" if user_type == "personal" else "Team Space",
    }

    SESSIONS[session_token] = {
        "session_token": session_token,
        "refresh_token": refresh_token,
        "user_id": user["id"],
        "current_space": current_space,
        "created_at": utc_now(),
    }

    return ok(
        {
            "user": user,
            "session_token": session_token,
            "refresh_token": refresh_token,
            "current_space": current_space,
            "authenticated": True,
        }
    )
