# from __future__ import annotations
from fastapi import APIRouter, UploadFile, File, Depends, Query
from sqlalchemy.orm import Session
from app.api.deps import get_session
from app.ingest.airlines_csv import parse_airlines_csv
from app.ingest.airport_csv import parse_airports_csv 
from app.services.airlines import ensure_airline
from app.services.airports import ensure_airport
from app.services.routes import ingest_routes_service


router = APIRouter(prefix="/ingest", tags=["ingest"])


@router.post("/airlines")
async def ingest_airlines(file: UploadFile = File(...), db: Session = Depends(get_session)):
    airlines = parse_airlines_csv(file.file)
    inserted = 0
    
    """
        Mejoras:
        - Batch insert
        - Devolver los que no se pudieron insertar y por que. Capaz no devolver pero si informar en logs.
        - Async insert con una cola de background tasks.
    """
    for it in airlines:
        al_inserted = ensure_airline(db, iata=it.get("iata"), icao=it.get("icao"), defaults={"name": it.get("name"), "country": it.get("country")})
        if al_inserted: inserted += 1
    return {"inserted_or_existing": inserted}

@router.post("/routes")
async def ingest_routes(file: UploadFile = File(...), db: Session = Depends(get_session)):
    return ingest_routes_service(db, file.file)

@router.post("/airports")
async def ingest_airports(file: UploadFile = File(...), db: Session = Depends(get_session)):
    airports = parse_airports_csv(file.file)
    inserted = 0
    for ap in airports:
        ap_inserted = ensure_airport(db, iata=ap.get("iata"), icao=ap.get("icao"), defaults={
            "ext_id": ap.get("ext_id"),
            "name": ap.get("name"),
            "city": ap.get("city"),
            "country": ap.get("country"),
            "latitude": ap.get("latitude"),
            "longitude": ap.get("longitude"),
            "altitude_ft": ap.get("altitude_ft"),
            "utc_offset": ap.get("utc_offset"),
            "continent_code": ap.get("continent_code"),
            "timezone_olson": ap.get("timezone_olson"),
        })
        if ap_inserted: inserted += 1
    return {"inserted_or_existing": inserted}