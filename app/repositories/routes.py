# from __future__ import annotations
from sqlalchemy.orm import Session
from app.models import Route

def add_route(db: Session, data: dict) -> Route:
    r = Route(**data)
    db.add(r)
    return r

def bulk_commit(db: Session):
    db.commit()
