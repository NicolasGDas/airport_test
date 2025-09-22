# from __future__ import annotations
from sqlalchemy.orm import Session
from sqlalchemy import select
from app.models import Airport

def get_by_codes(db: Session, *, iata: str | None, icao: str | None) -> Airport | None:
    if not iata and not icao:
        return None
    stmt = select(Airport)
    if iata:
        stmt = stmt.where(Airport.iata == iata.upper())
    if icao:
        stmt = stmt.where(Airport.icao == icao.upper())
    return db.execute(stmt).scalars().first()

def get_or_create(db: Session, *, iata: str | None, icao: str | None, defaults: dict | None = None) -> Airport | None:
    ap = get_by_codes(db, iata=iata, icao=icao)
    if ap:
        return ap
    data = (defaults or {}).copy()
    if iata:
        data["iata"] = iata.upper()
    if icao:
        data["icao"] = icao.upper()
    ap = Airport(**data)
    db.add(ap)
    try:
        db.commit()
    except Exception:
        db.rollback()
        ap = get_by_codes(db, iata=iata, icao=icao)
        if ap:
            return ap
        raise
    db.refresh(ap)
    return ap
