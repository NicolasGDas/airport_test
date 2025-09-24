# from __future__ import annotations
from typing import List, Optional
from app.schemas.analytics import AirlineOccupancyOut, TopRouteOut
from sqlalchemy.orm import Session, aliased
from sqlalchemy import select, func, case, cast, Float, text, and_, or_
from sqlalchemy.sql import exists
from datetime import date
from app.models import Route, Airport, Airline


def average_occupancy_by_airline(db: Session, start=None, end=None):
    """
    Calcula el promedio simple de ocupación por aerolínea.

    Usa `Route.occupancy` directamente (si ya está precalculado en el modelo).
    Para promedio ponderado por capacidad usá `find_airline_occupancy_orm`.

    Args:
        db (Session): Sesión de base de datos.
        start (date | None): Fecha inicial (inclusive) para filtrar rutas.
        end (date | None): Fecha final (inclusive) para filtrar rutas.

    Returns:
        list[Row]: Filas con `(airline_name, avg_occupancy)` ordenadas por aerolínea.
    """
    q = (
        select(Airline.name, func.avg(Route.occupancy))
        .join(Route, Route.airline_id == Airline.id, isouter=True)
    )
    if start:
        q = q.where(Route.flight_date >= start)
    if end:
        q = q.where(Route.flight_date <= end)
    q = q.group_by(Airline.name).order_by(Airline.name)
    return db.execute(q).all()


def domestic_altitude_percentage(db: Session, min_occupancy: float = 0.85):
    """
    Calcula el porcentaje de vuelos domésticos (mismo país) con alta ocupación
    cuya diferencia de altitud entre aeropuertos supere 1000 metros.

    Reglas:
      - Doméstico: `ao.country == ad.country` (y no nulos).
      - Alta ocupación: tickets_sold/capacity >= `min_occupancy`.
      - Altitud: se usa `altitude_ft` convertido a metros (ft * 0.3048).
      - Retorna `(total, over_1000, porcentaje)`.

    Args:
        db (Session): Sesión de base de datos.
        min_occupancy (float): Umbral de ocupación (0..1). Por defecto 0.85.

    Returns:
        tuple[int, int, float]: 
            - total de vuelos domésticos con datos válidos y alta ocupación,
            - cuántos superan 1000m de diferencia de altitud,
            - porcentaje correspondiente (0..100).
    """
    ao = aliased(Airport)  # origen
    ad = aliased(Airport)  # destino
    R = Route

    # Ocupación efectiva: tickets_sold / capacity (si ambos existen y capacity > 0)
    occ_effective = case(
        (
            (R.tickets_sold.is_not(None)) &
            (R.capacity.is_not(None)) &
            (R.capacity > 0),
            cast(R.tickets_sold, Float) / cast(R.capacity, Float)
        ),
        else_=None
    )

    # Diferencia de altitud en METROS (altitude_ft * 0.3048)
    altitude_diff_m = func.abs((ao.altitude_ft - ad.altitude_ft) * 0.3048)

    q = (
        select(
            func.count().label("total"),
            func.sum(
                case((altitude_diff_m > 1000, 1), else_=0)
            ).label("over_1000")
        )
        .select_from(R)
        .join(ao, ao.id == R.origin_airport_id)
        .join(ad, ad.id == R.destination_airport_id)
        .where(
            # Domésticos
            ao.country.is_not(None),
            ad.country.is_not(None),
            ao.country == ad.country,
            # Altitudes presentes (evitar NULL en la resta)
            ao.altitude_ft.is_not(None),
            ad.altitude_ft.is_not(None),
            # Alta ocupación
            occ_effective.is_not(None),
            occ_effective >= min_occupancy,
        )
    )

    row = db.execute(q).first()
    if row is None:
        total, over = 0, 0
    else:
        total, over = int(row.total or 0), int(row.over_1000 or 0)

    pct = (over / total * 100.0) if total else 0.0
    return total, over, pct


def consecutive_high_occupancy_routes(
    db: Session,
    min_occupancy: float = 0.85,
    start: date | None = None,
    end: date | None = None,
):
    """
    Identifica rutas con alta ocupación en días consecutivos.

    Considera la MISMA ruta `(airline_id, origin_airport_id, destination_airport_id)` con:
      - día `D` con ocupación >= `min_occupancy`, y
      - un vuelo idéntico el día `D+1` también con ocupación >= `min_occupancy`.

    Args:
        db (Session): Sesión de base de datos.
        min_occupancy (float): Umbral mínimo (0..1). Por defecto 0.85.
        start (date | None): Fecha inicial para filtrar `R.flight_date`.
        end (date | None): Fecha final para filtrar `R.flight_date`.

    Returns:
        list[Row]: Filas con
            `(airline, origin_iata, destination_iata, first_date, second_date)`,
        ordenadas por aerolínea, origen, destino y fecha.
    """
    R = Route
    R2 = aliased(Route)
    ao = aliased(Airport)   # origin
    ad = aliased(Airport)   # destination

    # ocupación efectiva R
    occ = case(
        (
            (R.tickets_sold.is_not(None)) &
            (R.capacity.is_not(None)) &
            (R.capacity > 0),
            cast(R.tickets_sold, Float) / cast(R.capacity, Float)
        ),
        else_=None
    )

    # ocupación efectiva R2
    occ2 = case(
        (
            (R2.tickets_sold.is_not(None)) &
            (R2.capacity.is_not(None)) &
            (R2.capacity > 0),
            cast(R2.tickets_sold, Float) / cast(R2.capacity, Float)
        ),
        else_=None
    )

    # EXISTS: hay un vuelo al día siguiente con la misma ruta y alta ocupación
    exists_next_day = exists(
        select(1)
        .where(
            and_(
                R2.airline_id == R.airline_id,
                R2.origin_airport_id == R.origin_airport_id,
                R2.destination_airport_id == R.destination_airport_id,
                R2.flight_date == R.flight_date + text("INTERVAL '1 day'"),
                occ2.is_not(None),
                occ2 >= min_occupancy,
            )
        )
    )

    q = (
        select(
            Airline.name.label("airline"),
            ao.iata.label("origin"),
            ad.iata.label("destination"),
            R.flight_date.label("first_date"),
            (R.flight_date + text("INTERVAL '1 day'")).label("second_date"),
        )
        .select_from(R)
        .join(Airline, Airline.id == R.airline_id, isouter=False)
        .join(ao, ao.id == R.origin_airport_id)
        .join(ad, ad.id == R.destination_airport_id)
        .where(
            occ.is_not(None),
            occ >= min_occupancy,
            exists_next_day,
        )
    )

    if start:
        q = q.where(R.flight_date >= start)
    if end:
        q = q.where(R.flight_date <= end)

    q = q.order_by(Airline.name, ao.iata, ad.iata, R.flight_date)

    return db.execute(q).all()


def find_top_routes_by_country_orm(
    db: Session,
    *,
    country: str,
    start: Optional["date"] = None,
    end: Optional["date"] = None,
    scope: str = "either",            # "origin" | "destination" | "either"
    limit: int = 5,
    only_operated: Optional[bool] = None,
) -> List[TopRouteOut]:
    """
    Devuelve las rutas más voladas asociadas a un país.

    Permite analizar el país en el origen, en el destino o en cualquiera de los dos
    (scope = "either"), acotando opcionalmente por fechas y por vuelos operados.

    Args:
        db (Session): Sesión de base de datos.
        country (str): Nombre exacto del país (según `airports.country`).
        start (date | None): Fecha inicial (inclusive).
        end (date | None): Fecha final (inclusive).
        scope (str): "origin", "destination" o "either" (por defecto).
        limit (int): Máximo de rutas a devolver. Default 5.
        only_operated (bool | None): Si es True, solo vuelos operados; si es False,
            solo no operados; si es None, no filtra.

    Returns:
        List[TopRouteOut]: Lista de rutas con IDs de aeropuertos, nombres legibles
        (preferencia IATA→ICAO→name) y cantidad de vuelos.
    """
    R = Route
    AO = aliased(Airport)  # origin
    AD = aliased(Airport)  # destination

    # Nombres legibles (IATA → ICAO → name). Usamos MAX() para poder agrupar solo por IDs.
    origin_name = func.max(func.coalesce(AO.iata, AO.icao, AO.name)).label("origin")
    dest_name   = func.max(func.coalesce(AD.iata, AD.icao, AD.name)).label("destination")

    # Filtro país según scope
    if scope == "origin":
        country_filter = (AO.country == country)
    elif scope == "destination":
        country_filter = (AD.country == country)
    else:
        country_filter = or_(AO.country == country, AD.country == country)

    filters = [country_filter]
    if only_operated is True:
        filters.append(R.operated_carrier.is_(True))
    elif only_operated is False:
        filters.append(R.operated_carrier.is_(False))
    if start is not None:
        filters.append(R.flight_date >= start)
    if end is not None:
        filters.append(R.flight_date <= end)

    q = (
        select(
            R.origin_airport_id,
            R.destination_airport_id,
            origin_name,
            dest_name,
            func.count().label("flights"),
        )
        .select_from(R)
        .join(AO, AO.id == R.origin_airport_id)
        .join(AD, AD.id == R.destination_airport_id)
        .where(and_(*filters))
        .group_by(R.origin_airport_id, R.destination_airport_id)
        .order_by(func.count().desc())
        .limit(limit)
    )

    rows = db.execute(q).mappings().all()

    # Mapear a Pydantic
    return [
        TopRouteOut(
            origin_airport_id=r["origin_airport_id"],
            destination_airport_id=r["destination_airport_id"],
            origin=r["origin"],
            destination=r["destination"],
            flights=int(r["flights"]),
        )
        for r in rows
    ]


def find_airline_occupancy_orm(
    db: Session,
    *,
    start: Optional["date"] = None,
    end: Optional["date"] = None,
    only_operated: Optional[bool] = None,
    min_flights: int = 1,
) -> List[AirlineOccupancyOut]:
    """
    Calcula ocupación promedio por aerolínea (ponderado por capacidad).

    Fórmula:
        occupancy = SUM(tickets_sold) / NULLIF(SUM(capacity), 0)

    Permite filtrar por rango de fechas y por si el vuelo fue operado por la aerolínea.
    Además, se puede exigir un mínimo de vuelos para incluir a la aerolínea.

    Args:
        db (Session): Sesión de base de datos.
        start (date | None): Fecha inicial (inclusive).
        end (date | None): Fecha final (inclusive).
        only_operated (bool | None): Si es True, solo vuelos operados; si es False,
            solo no operados; si es None, no filtra.
        min_flights (int): Mínimo de vuelos para incluir la aerolínea. Default 1.

    Returns:
        List[AirlineOccupancyOut]: Aerolínea con su cantidad de vuelos, tickets,
        capacidad total y ocupación (0..1).
    """
    R = Route
    A = Airline

    filters = []
    if start is not None:
        filters.append(R.flight_date >= start)
    if end is not None:
        filters.append(R.flight_date <= end)
    if only_operated is True:
        filters.append(R.operated_carrier.is_(True))
    elif only_operated is False:
        filters.append(R.operated_carrier.is_(False))

    sum_tickets   = func.coalesce(func.sum(R.tickets_sold), 0).label("tickets")
    sum_capacity  = func.coalesce(func.sum(R.capacity), 0).label("capacity")
    flights_count = func.count().label("flights")

    # occupancy = SUM(tickets) / NULLIF(SUM(capacity), 0)
    occupancy = cast(
        sum_tickets.cast(Float) / func.nullif(sum_capacity, 0),
        Float
    ).label("occupancy")

    base = (
        select(
            R.airline_id,
            func.max(A.name).label("airline"),  # determinista por airline_id
            flights_count,
            sum_tickets,
            sum_capacity,
            occupancy,
        )
        .select_from(R)
        .join(A, A.id == R.airline_id)
    )
    q = base.where(and_(*filters)) if filters else base
    q = q.group_by(R.airline_id)

    if min_flights > 1:
        q = q.having(func.count() >= min_flights)

    q = q.order_by(occupancy.desc().nulls_last(), flights_count.desc())

    rows = db.execute(q).mappings().all()

    # Mapear a Pydantic (evitar None en occupancy si cap=0)
    out: List[AirlineOccupancyOut] = []
    for r in rows:
        occ = r["occupancy"] if r["occupancy"] is not None else 0.0
        out.append(
            AirlineOccupancyOut(
                airline_id=r["airline_id"],
                airline=r["airline"],
                flights=int(r["flights"]),
                tickets=int(r["tickets"]),
                capacity=int(r["capacity"]),
                occupancy=float(occ),
            )
        )
    return out
