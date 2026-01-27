from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import Company, to_company_dict, utc_now
from app.store import new_id


def list_companies(db: Session) -> list[dict]:
    items = db.execute(select(Company).order_by(Company.created_at.desc())).scalars().all()
    return [to_company_dict(item) for item in items]


def get_company(db: Session, company_id: str) -> Company | None:
    return db.execute(select(Company).where(Company.id == company_id)).scalar_one_or_none()


def get_company_by_invite(db: Session, invite_code: str) -> Company | None:
    return (
        db.execute(select(Company).where(Company.invite_code == invite_code))
        .scalar_one_or_none()
    )


def create_company(db: Session, name: str, invite_code: str) -> dict:
    now = utc_now()
    company = Company(
        id=new_id(),
        name=name,
        invite_code=invite_code,
        created_at=now,
        updated_at=now,
    )
    db.add(company)
    db.commit()
    db.refresh(company)
    return to_company_dict(company)


def update_invite_code(db: Session, company: Company, invite_code: str) -> dict:
    company.invite_code = invite_code
    company.updated_at = utc_now()
    db.commit()
    db.refresh(company)
    return to_company_dict(company)
