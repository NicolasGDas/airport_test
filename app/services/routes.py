# from __future__ import annotations
from sqlalchemy.orm import Session
from app.repositories import routes as repo

def insert_routes(db: Session, routes_data: list[dict]) -> int:
    count = 0
    for data in routes_data:
        repo.add_route(db, data)
        count += 1
    repo.bulk_commit(db)
    return count
