# from __future__ import annotations
from sqlalchemy.orm import Session
from sqlalchemy import select
from app.models import Airline

def get_by_codes(db: Session, *, iata: str | None, icao: str | None) -> Airline | None:
    if not iata and not icao:
        return None
    stmt = select(Airline)
    if iata:
        stmt = stmt.where(Airline.iata == iata.upper())
    if icao:
        stmt = stmt.where(Airline.icao == icao.upper())
    return db.execute(stmt).scalars().first()

def get_or_create(db: Session, *, iata: str | None, icao: str | None, defaults: dict | None = None) -> Airline | None:
    al = get_by_codes(db, iata=iata, icao=icao)
    if al:
        return al
    data = (defaults or {}).copy()
    if iata:
        data["iata"] = iata.upper()
    if icao:
        data["icao"] = icao.upper()
    al = Airline(**data)
    db.add(al)
    try:
        db.commit()
    except Exception:
        db.rollback()
        al = get_by_codes(db, iata=iata, icao=icao)
        if al:
            return al
        raise
    db.refresh(al)
    return al
