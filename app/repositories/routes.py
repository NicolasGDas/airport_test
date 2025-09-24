# from __future__ import annotations
from typing import List
from sqlalchemy.orm import Session
from app.models import Route

class RoutesRepo:
    @staticmethod
    def bulk_insert(db: Session, rows: List[Route]) -> None:
        db.bulk_save_objects(rows)
        db.commit()



def add_route(db: Session, data: dict) -> Route:
    r = Route(**data)
    db.add(r)
    return r

def bulk_commit(db: Session):
    db.commit()
