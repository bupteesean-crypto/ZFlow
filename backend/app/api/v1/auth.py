import hashlib
import secrets
from typing import Any, Dict

from fastapi import APIRouter, Body, Depends, HTTPException
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.api.v1.deps import require_platform_admin
from app.api.v1.response import ok
from app.db.models import to_user_account_dict
from app.db.session import get_db
from app.repositories import companies as company_repo
from app.repositories import users as user_repo
from app.store import SESSIONS, new_id, utc_now

router = APIRouter(prefix="/auth", tags=["auth"])

def _hash_password(password: str, salt: str) -> str:
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt.encode("utf-8"), 120000)
    return digest.hex()


def _generate_invite_code() -> str:
    return secrets.token_hex(6)


def _build_user_response(user: dict) -> Dict[str, Any]:
    return {
        "id": user.get("id"),
        "uid": user.get("uid"),
        "username": user.get("username"),
        "display_name": user.get("display_name"),
        "avatar_url": user.get("avatar_url"),
        "account_type": user.get("account_type") or "personal",
        "roles": user.get("roles") or [],
        "company_id": user.get("company_id"),
        "is_platform_admin": bool(user.get("is_platform_admin")),
        "membership": "demo",
        "points": {"current": 0, "paid": 0, "bonus": 0},
        "quota_info": {"daily_limit": 10, "used": 0, "reset_at": utc_now(), "remaining": 10},
        "created_at": user.get("created_at") or utc_now(),
        "updated_at": user.get("updated_at") or utc_now(),
    }


@router.post("/login")
async def login(
    payload: Dict[str, Any] = Body(default_factory=dict),
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    username = payload.get("username")
    password = payload.get("password")

    if not isinstance(username, str) or not username.strip():
        raise HTTPException(status_code=400, detail="username required")
    if not isinstance(password, str) or not password:
        raise HTTPException(status_code=400, detail="password required")

    username = username.strip()
    try:
        user = user_repo.get_user_by_username(db, username)
        if not user:
            if user_repo.count_users(db) == 0:
                salt = secrets.token_hex(16)
                password_hash = _hash_password(password, salt)
                user_repo.create_user(
                    db,
                    username,
                    password_hash,
                    salt,
                    account_type="personal",
                    roles=["admin", "creator"],
                    company_id=None,
                    is_platform_admin=True,
                    display_name=username,
                )
                user = user_repo.get_user_by_username(db, username)
            else:
                raise HTTPException(status_code=401, detail="invalid credentials")
        if not user:
            raise HTTPException(status_code=401, detail="invalid credentials")
    except SQLAlchemyError:
        db.rollback()
        raise HTTPException(status_code=500, detail="Database error")

    if _hash_password(password, user.password_salt) != user.password_hash:
        raise HTTPException(status_code=401, detail="invalid credentials")

    session_token = new_id()
    refresh_token = new_id()
    space_name = "Personal Space"
    space_id = None
    if user.company_id:
        company = company_repo.get_company(db, user.company_id)
        if company:
            space_id = company.id
            space_name = company.name
    current_space = {
        "type": user.account_type or "personal",
        "space_id": space_id,
        "space_name": space_name,
    }

    SESSIONS[session_token] = {
        "session_token": session_token,
        "refresh_token": refresh_token,
        "user_id": user.id,
        "current_space": current_space,
        "created_at": utc_now(),
    }

    user_payload = _build_user_response(to_user_account_dict(user))
    user_payload["llm_api_base"] = user.llm_api_base or ""
    user_payload["llm_configured"] = bool(user.llm_api_key_encrypted)
    return ok(
        {
            "user": user_payload,
            "session_token": session_token,
            "refresh_token": refresh_token,
            "current_space": current_space,
            "authenticated": True,
        }
    )


@router.get("/users")
async def list_users(
    db: Session = Depends(get_db),
    current_user: object = Depends(require_platform_admin),
) -> Dict[str, Any]:
    try:
        users = user_repo.list_users(db)
    except SQLAlchemyError:
        db.rollback()
        raise HTTPException(status_code=500, detail="Database error")
    return ok({"list": users, "total": len(users)})


@router.post("/users")
async def create_user(
    payload: Dict[str, Any] = Body(default_factory=dict),
    db: Session = Depends(get_db),
    current_user: object = Depends(require_platform_admin),
) -> Dict[str, Any]:
    username = payload.get("username")
    password = payload.get("password")
    account_type = payload.get("account_type") or "personal"
    roles = payload.get("roles") if isinstance(payload.get("roles"), list) else []
    roles = [str(item).strip() for item in roles if str(item).strip()]
    roles = [item for item in roles if item in {"admin", "creator"}]
    create_company_name = payload.get("create_company_name")
    company_invite_code = payload.get("company_invite_code")
    if not isinstance(username, str) or not username.strip():
        raise HTTPException(status_code=400, detail="username required")
    if not isinstance(password, str) or not password:
        raise HTTPException(status_code=400, detail="password required")
    if account_type not in {"personal", "company"}:
        raise HTTPException(status_code=400, detail="account_type invalid")
    username = username.strip()
    try:
        existing = user_repo.get_user_by_username(db, username)
        if existing:
            raise HTTPException(status_code=409, detail="username already exists")
        company_id = None
        if isinstance(create_company_name, str) and create_company_name.strip():
            if account_type != "company":
                raise HTTPException(status_code=400, detail="create_company_name requires company account")
            invite_code = _generate_invite_code()
            company = company_repo.create_company(db, create_company_name.strip(), invite_code)
            company_id = company["id"]
            if "admin" not in roles:
                roles = [*roles, "admin"]
        elif isinstance(company_invite_code, str) and company_invite_code.strip():
            company = company_repo.get_company_by_invite(db, company_invite_code.strip())
            if not company:
                raise HTTPException(status_code=404, detail="invalid invite code")
            company_id = company.id
        elif account_type == "company":
            raise HTTPException(status_code=400, detail="company account requires invite or create_company_name")

        if not roles:
            roles = ["creator"]
        salt = secrets.token_hex(16)
        password_hash = _hash_password(password, salt)
        user = user_repo.create_user(
            db,
            username,
            password_hash,
            salt,
            account_type=account_type,
            roles=roles,
            company_id=company_id,
            is_platform_admin=False,
            display_name=username,
        )
    except HTTPException:
        raise
    except SQLAlchemyError:
        db.rollback()
        raise HTTPException(status_code=500, detail="Database error")
    return ok(_build_user_response(user))


@router.put("/users/{user_id}/password")
async def update_user_password(
    user_id: str,
    payload: Dict[str, Any] = Body(default_factory=dict),
    db: Session = Depends(get_db),
    current_user: object = Depends(require_platform_admin),
) -> Dict[str, Any]:
    password = payload.get("password")
    if not isinstance(password, str) or not password:
        raise HTTPException(status_code=400, detail="password required")
    try:
        user = user_repo.get_user(db, user_id)
        if not user:
            raise HTTPException(status_code=404, detail="user not found")
        salt = secrets.token_hex(16)
        password_hash = _hash_password(password, salt)
        updated = user_repo.update_user_password(db, user, password_hash, salt)
    except HTTPException:
        raise
    except SQLAlchemyError:
        db.rollback()
        raise HTTPException(status_code=500, detail="Database error")
    return ok(_build_user_response(updated))


@router.get("/companies")
async def list_companies(
    db: Session = Depends(get_db),
    current_user: object = Depends(require_platform_admin),
) -> Dict[str, Any]:
    try:
        companies = company_repo.list_companies(db)
    except SQLAlchemyError:
        db.rollback()
        raise HTTPException(status_code=500, detail="Database error")
    return ok({"list": companies, "total": len(companies)})


@router.post("/companies")
async def create_company(
    payload: Dict[str, Any] = Body(default_factory=dict),
    db: Session = Depends(get_db),
    current_user: object = Depends(require_platform_admin),
) -> Dict[str, Any]:
    name = payload.get("name")
    if not isinstance(name, str) or not name.strip():
        raise HTTPException(status_code=400, detail="name required")
    invite_code = _generate_invite_code()
    try:
        company = company_repo.create_company(db, name.strip(), invite_code)
    except SQLAlchemyError:
        db.rollback()
        raise HTTPException(status_code=500, detail="Database error")
    return ok(company)


@router.put("/companies/{company_id}/invite")
async def reset_company_invite(
    company_id: str,
    db: Session = Depends(get_db),
    current_user: object = Depends(require_platform_admin),
) -> Dict[str, Any]:
    if not company_id.strip():
        raise HTTPException(status_code=400, detail="company_id required")
    try:
        company = company_repo.get_company(db, company_id)
        if not company:
            raise HTTPException(status_code=404, detail="company not found")
        invite_code = _generate_invite_code()
        updated = company_repo.update_invite_code(db, company, invite_code)
    except HTTPException:
        raise
    except SQLAlchemyError:
        db.rollback()
        raise HTTPException(status_code=500, detail="Database error")
    return ok(updated)
