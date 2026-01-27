from fastapi import Depends, Header, HTTPException, Query
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.repositories import users as user_repo
from app.store import SESSIONS


def _extract_token(authorization: str | None, session_token: str | None) -> str | None:
    if authorization and authorization.lower().startswith("bearer "):
        return authorization.split(" ", 1)[1].strip()
    if session_token:
        return session_token.strip()
    return None


def get_current_user(
    db: Session = Depends(get_db),
    authorization: str | None = Header(default=None),
    session_token: str | None = Header(default=None, alias="X-Session-Token"),
    session_token_query: str | None = Query(default=None, alias="session_token"),
) -> object:
    token = _extract_token(authorization, session_token) or session_token_query
    if not token:
        raise HTTPException(status_code=401, detail="unauthorized")
    session = SESSIONS.get(token)
    if not session:
        raise HTTPException(status_code=401, detail="invalid session")
    user = user_repo.get_user(db, session.get("user_id"))
    if not user:
        raise HTTPException(status_code=401, detail="invalid user")
    return user


def require_platform_admin(current_user: object = Depends(get_current_user)) -> object:
    if not getattr(current_user, "is_platform_admin", False):
        raise HTTPException(status_code=403, detail="forbidden")
    return current_user
