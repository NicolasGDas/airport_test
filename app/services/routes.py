# app/services/routes_service.py
from typing import Dict, List
from sqlalchemy.orm import Session

from app.ingest.routes_csv import parse_routes_csv
from app.repositories.routes import RoutesRepo
from app.schemas.routes import RouteIn
from app.models import Route

def ingest_routes_service(db: Session, fileobj) -> Dict:
    items, parse_errors = parse_routes_csv(fileobj)
    rows: List[Route] = []

    for it in items:
        d = it.model_dump(by_alias=False, exclude_none=True)
        rows.append(Route(**d))

    if rows:
        RoutesRepo.bulk_insert(db, rows)

    return {
        "inserted": len(rows),
        "skipped": len(parse_errors),
        "skipped_preview": parse_errors[:10],  # para depurar por qué faltan IDs
    }
