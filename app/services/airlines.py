# from __future__ import annotations
from sqlalchemy.orm import Session
from app.repositories import airlines as repo

def ensure_airline(db: Session, *, iata: str | None, icao: str | None, defaults: dict | None = None):
    return repo.get_or_create(db, iata=iata, icao=icao, defaults=defaults or {})

def get_airline_by_codes(db: Session, *, iata: str | None, icao: str | None):
    return repo.get_by_codes(db, iata=iata, icao=icao)

