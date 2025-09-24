# from __future__ import annotations
from typing import List, Optional
from app.schemas.analytics import AirlineOccupancyOut, TopRouteOut
from sqlalchemy.orm import Session, aliased
from sqlalchemy import select, func, case, cast, Float, text, and_, or_
from sqlalchemy.sql import exists
from datetime import date
from app.models import Route, Airport, Airline

def average_occupancy_by_airline(db: Session, start=None, end=None):
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
        # 👇 Establecemos tabla base explícita para evitar la ambigüedad del JOIN
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
    Devuelve pares (airline_name, origin_iata, dest_iata, first_date, second_date)
    donde existe la MISMA ruta (airline, origin, destination) con alta ocupación
    (>= min_occupancy) en dos días consecutivos.
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

    # Podrías agrupar para evitar pares duplicados; aquí devolvemos cada par detectado
    q = q.order_by(Airline.name, ao.iata, ad.iata, R.flight_date)

    return db.execute(q).all()


def find_top_routes_by_country_orm(
    db: Session,
    *,
    country: str,
    start: Optional["date"] = None,   # importa date si preferís
    end: Optional["date"] = None,
    scope: str = "either",            # "origin" | "destination" | "either"
    limit: int = 5,
    only_operated: Optional[bool] = None,
) -> List[TopRouteOut]:
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
    start: Optional["date"] = None,  # from datetime import date si querés tipar
    end: Optional["date"] = None,
    only_operated: Optional[bool] = None,
    min_flights: int = 1,            # opcional: filtrar aerolíneas con al menos N vuelos
) -> List[AirlineOccupancyOut]:
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

    q = (
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
        .where(and_(*filters)) if filters else select(
            R.airline_id,
            func.max(A.name).label("airline"),
            flights_count,
            sum_tickets,
            sum_capacity,
            occupancy,
        ).select_from(R).join(A, A.id == R.airline_id)
    ).group_by(R.airline_id)

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