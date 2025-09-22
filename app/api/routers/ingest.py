# from __future__ import annotations
from fastapi import APIRouter, UploadFile, File, Depends
from sqlalchemy.orm import Session
from app.api.deps import get_session
from app.ingest.airlines_csv import parse_airlines_csv
from app.ingest.routes_csv import parse_routes_csv
from app.services.airlines import ensure_airline
from app.services.airports import ensure_airport
from app.services.routes import insert_routes

router = APIRouter(prefix="/ingest", tags=["ingest"])

@router.post("/airlines")
async def ingest_airlines(file: UploadFile = File(...), db: Session = Depends(get_session)):
    items = parse_airlines_csv(file.file)
    inserted = 0
    for it in items:
        al = ensure_airline(db, iata=it.get("iata"), icao=it.get("icao"), defaults={"name": it.get("name"), "country": it.get("country")})
        if al: inserted += 1
    return {"inserted_or_existing": inserted}

@router.post("/routes")
async def ingest_routes(file: UploadFile = File(...), db: Session = Depends(get_session)):
    rows = parse_routes_csv(file.file)
    data = []
    for r in rows:
        ao = ensure_airport(db, iata=r.get("origin_iata"), icao=None)
        ad = ensure_airport(db, iata=r.get("destination_iata"), icao=None)
        if not ao or not ad:
            continue
        al = None
        if r.get("airline_iata"):
            from app.services.airlines import ensure_airline as ensure_al
            al = ensure_al(db, iata=r.get("airline_iata"), icao=None)
        data.append({
            "airline_id": (al.id if al else None),
            "origin_id": ao.id,
            "destination_id": ad.id,
            "capacity": r.get("capacity"),
            "occupancy": r.get("occupancy"),
            "flight_date": r.get("flight_date"),
        })
    count = insert_routes(db, data)
    return {"inserted": count}
