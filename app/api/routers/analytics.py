from __future__ import annotations
from app.repositories.analytics import find_airline_occupancy_orm, find_top_routes_by_country_orm
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from datetime import date
from typing import Optional, List
from app.api.deps import get_session
from app.services import analytics as svc
from app.schemas.analytics import (
    AirlineOccupancyOut,
    DomesticAltitudePercentage,
    ConsecutiveHighOccRoute,
    TopRouteOut,
)

router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.get("/airline-occupancy", response_model=List[AirlineOccupancyOut])
def airline_occupancy(
    start: Optional[date] = Query(None, description="YYYY-MM-DD"),
    end: Optional[date] = Query(None, description="YYYY-MM-DD"),
    only_operated: Optional[bool] = Query(None, description="Filtra operated_carrier"),
    min_flights: int = Query(1, ge=1, le=1000),
    db: Session = Depends(get_session),
):
    """
    Calcula el promedio de ocupación por aerolínea.

    El promedio se calcula de manera ponderada, sumando todos los tickets vendidos y
    dividiéndolos por la suma de la capacidad disponible.

    Args:
        start (date, optional): Fecha inicial del rango a analizar (inclusive).
        end (date, optional): Fecha final del rango a analizar (inclusive).
        only_operated (bool, optional): Si se especifica, filtra por vuelos operados por la aerolínea.
        min_flights (int): Mínimo de vuelos requeridos para incluir la aerolínea en el resultado.
        db (Session): Sesión de base de datos inyectada por dependencia.

    Returns:
        List[AirlineOccupancyOut]: Lista de aerolíneas con su ocupación promedio y estadísticas.
    """
    return find_airline_occupancy_orm(
        db,
        start=start,
        end=end,
        only_operated=only_operated,
        min_flights=min_flights,
    )


@router.get(
    "/domestic-altitude-percentage",
    response_model=DomesticAltitudePercentage,
)
def domestic_altitude_percentage(
    min_occupancy: float = Query(0.85, ge=0, le=1),
    db: Session = Depends(get_session),
):
    """
    Calcula el porcentaje de rutas domésticas con alta ocupación.

    Una ruta se considera "con alta ocupación" si supera el umbral definido.

    Args:
        min_occupancy (float): Umbral de ocupación mínimo (entre 0 y 1).
            Por defecto es 0.85 (85%).
        db (Session): Sesión de base de datos inyectada por dependencia.

    Returns:
        DomesticAltitudePercentage: Porcentaje de rutas domésticas con ocupación ≥ umbral.
    """
    return svc.domestic_altitude_percentage(db, min_occupancy=min_occupancy)


@router.get("/top-routes-by-country", response_model=List[TopRouteOut])
def top_routes_by_country(
    country: str = Query(..., description="Nombre exacto en airports.country"),
    start: Optional[date] = Query(None),
    end: Optional[date] = Query(None),
    scope: str = Query("either", pattern="^(origin|destination|either)$"),
    limit: int = Query(5, ge=1, le=50),
    only_operated: Optional[bool] = Query(None),
    db: Session = Depends(get_session),
):
    """
    Devuelve las rutas más utilizadas asociadas a un país.

    El país puede analizarse como origen, destino o ambos (scope = either).
    Se pueden limitar los resultados y acotar el rango de fechas.

    Args:
        country (str): Nombre exacto del país según la columna `airports.country`.
        start (date, optional): Fecha inicial para filtrar vuelos.
        end (date, optional): Fecha final para filtrar vuelos.
        scope (str): Ámbito a considerar: "origin", "destination" o "either".
            Por defecto "either".
        limit (int): Número máximo de rutas a devolver.
            Por defecto 5.
        only_operated (bool, optional): Si se especifica, filtra solo vuelos operados por la aerolínea.
        db (Session): Sesión de base de datos inyectada por dependencia.

    Returns:
        List[TopRouteOut]: Lista de rutas con conteo de vuelos y métricas agregadas.
    """
    return find_top_routes_by_country_orm(
        db,
        country=country,
        start=start,
        end=end,
        scope=scope,
        limit=limit,
        only_operated=only_operated,
    )


@router.get(
    "/consecutive-high-occupancy-routes",
    response_model=List[ConsecutiveHighOccRoute],
)
def consecutive_high_occupancy_routes(
    min_occupancy: float = Query(0.85, ge=0, le=1),
    start: Optional[date] = None,
    end: Optional[date] = None,
    db: Session = Depends(get_session),
):
    """
    Identifica rutas con alta ocupación en días consecutivos.

    Args:
        min_occupancy (float): Umbral mínimo de ocupación (entre 0 y 1) para considerar un vuelo como "alto".
            Por defecto 0.85 (85%).
        start (date, optional): Fecha inicial del rango a evaluar.
        end (date, optional): Fecha final del rango a evaluar.
        db (Session): Sesión de base de datos inyectada por dependencia.

    Returns:
        List[ConsecutiveHighOccRoute]: Lista de rutas con pares de fechas consecutivas
        donde la ocupación supera el umbral.
    """
    return svc.consecutive_high_occupancy_routes(
        db,
        min_occupancy=min_occupancy,
        start=start,
        end=end,
    )
