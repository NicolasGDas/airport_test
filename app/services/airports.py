# from __future__ import annotations
from sqlalchemy.orm import Session
from app.repositories.airports import AirportsRepo as repo

def ensure_airport(db: Session, *, iata: str | None, icao: str | None, defaults: dict | None = None):
    return repo.get_or_create(db, iata=iata, icao=icao, defaults=defaults or {})
