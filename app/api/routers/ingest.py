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
    """
    Ingresa aerolíneas desde un archivo CSV.

    El CSV se parsea y por cada fila se intenta crear o actualizar la aerolínea
    en la base de datos. Si la aerolínea ya existe (por IATA o ICAO), no se inserta nuevamente.

    Args:
        file (UploadFile): Archivo CSV con los datos de aerolíneas.
        db (Session): Sesión de base de datos inyectada por dependencia.

    Returns:
        dict: Cantidad de registros insertados o ya existentes, en la forma:
            {"inserted_or_existing": N}

    Mejoras futuras:
        - Insert en batch para optimizar rendimiento.
        - Informar en logs los registros que no pudieron insertarse.
        - Insert asíncrono con colas de background tasks.
    """
    airlines = parse_airlines_csv(file.file)
    inserted = 0
    for it in airlines:
        al_inserted = ensure_airline(db, iata=it.get("iata"), icao=it.get("icao"), defaults=it)
        if al_inserted:
            inserted += 1
    return {"inserted_or_existing": inserted}


@router.post("/routes")
async def ingest_routes(file: UploadFile = File(...), db: Session = Depends(get_session)):
    """
    Ingresa rutas (vuelos) desde un archivo CSV.

    Se delega la lógica de parseo e inserción al servicio `ingest_routes_service`.
    Este servicio maneja la validación de datos y la inserción en la base.

    Args:
        file (UploadFile): Archivo CSV con los datos de rutas/vuelos.
        db (Session): Sesión de base de datos inyectada por dependencia.

    Returns:
        dict: Resumen del proceso de ingesta (cantidad de rutas insertadas,
        rechazadas, etc. según defina el servicio).
    """
    return ingest_routes_service(db, file.file)


@router.post("/airports")
async def ingest_airports(file: UploadFile = File(...), db: Session = Depends(get_session)):
    """
    Ingresa aeropuertos desde un archivo CSV.

    El CSV se parsea y por cada fila se intenta crear o actualizar el aeropuerto
    en la base de datos. Si el aeropuerto ya existe (por IATA o ICAO), no se inserta nuevamente.

    Args:
        file (UploadFile): Archivo CSV con los datos de aeropuertos.
        db (Session): Sesión de base de datos inyectada por dependencia.

    Returns:
        dict: Cantidad de registros insertados o ya existentes, en la forma:
            {"inserted_or_existing": N}
    """
    airports = parse_airports_csv(file.file)
    inserted = 0
    for ap in airports:
        ap_inserted = ensure_airport(db, iata=ap.get("iata"), icao=ap.get("icao"), defaults=ap)
        if ap_inserted:
            inserted += 1
    return {"inserted_or_existing": inserted}
