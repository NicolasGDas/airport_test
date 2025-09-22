# from __future__ import annotations
from sqlalchemy.orm import Session
from datetime import date
from app.repositories import analytics as repo

def average_occupancy(db: Session, start: date | None, end: date | None):
    rows = repo.average_occupancy_by_airline(db, start=start, end=end)
    return [{ "airline": r[0], "avg_occupancy": float(r[1]) if r[1] is not None else None } for r in rows]

def domestic_altitude_percentage(db: Session, min_occupancy: float):
    total, over, pct = repo.domestic_altitude_percentage(db, min_occupancy=min_occupancy)
    return { "total_high_occupancy_domestic": total, "over_1000m_altitude_diff": over, "percentage": pct }

def top_routes_by_country(db: Session, country: str, start: date | None, end: date | None):
    rows = repo.top_routes_by_country(db, country=country, start=start, end=end)
    return [{ "origin": r[0], "destination": r[1], "flights": int(r[2]) } for r in rows]
