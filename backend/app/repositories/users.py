from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db.models import UserAccount, to_user_account_dict
from app.store import new_id, utc_now


def list_users(db: Session) -> list[dict]:
    items = db.execute(select(UserAccount).order_by(UserAccount.created_at.desc())).scalars().all()
    return [to_user_account_dict(item) for item in items]


def count_users(db: Session) -> int:
    return db.execute(select(func.count()).select_from(UserAccount)).scalar_one()


def get_user(db: Session, user_id: str) -> UserAccount | None:
    return db.execute(select(UserAccount).where(UserAccount.id == user_id)).scalar_one_or_none()


def get_user_by_username(db: Session, username: str) -> UserAccount | None:
    return (
        db.execute(select(UserAccount).where(UserAccount.username == username))
        .scalar_one_or_none()
    )


def create_user(
    db: Session,
    username: str,
    password_hash: str,
    password_salt: str,
    account_type: str = "personal",
    roles: list[str] | None = None,
    company_id: str | None = None,
    is_platform_admin: bool = False,
    display_name: str | None = None,
    avatar_url: str | None = None,
) -> dict:
    now = utc_now()
    user = UserAccount(
        id=new_id(),
        username=username,
        display_name=display_name or username,
        avatar_url=avatar_url,
        password_hash=password_hash,
        password_salt=password_salt,
        account_type=account_type or "personal",
        roles=roles or [],
        company_id=company_id,
        is_platform_admin=is_platform_admin,
        created_at=now,
        updated_at=now,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return to_user_account_dict(user)


def update_user_password(db: Session, user: UserAccount, password_hash: str, password_salt: str) -> dict:
    user.password_hash = password_hash
    user.password_salt = password_salt
    user.updated_at = utc_now()
    db.commit()
    db.refresh(user)
    return to_user_account_dict(user)


def update_user_username(db: Session, user: UserAccount, username: str) -> dict:
    user.username = username
    user.updated_at = utc_now()
    db.commit()
    db.refresh(user)
    return to_user_account_dict(user)


def update_user_llm_settings(
    db: Session,
    user: UserAccount,
    api_base: str | None,
    api_key_encrypted: str | None,
) -> dict:
    if api_base is not None:
        user.llm_api_base = api_base
    if api_key_encrypted is not None:
        user.llm_api_key_encrypted = api_key_encrypted
    user.updated_at = utc_now()
    db.commit()
    db.refresh(user)
    return to_user_account_dict(user)


def update_user_profile(
    db: Session,
    user: UserAccount,
    display_name: str | None = None,
    avatar_url: str | None = None,
) -> dict:
    if display_name is not None:
        user.display_name = display_name
    if avatar_url is not None:
        user.avatar_url = avatar_url
    user.updated_at = utc_now()
    db.commit()
    db.refresh(user)
    return to_user_account_dict(user)
