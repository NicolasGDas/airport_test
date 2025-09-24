# from __future__ import annotations
from sqlalchemy.orm import Session, aliased
from sqlalchemy import select, func, case, cast, Float, text, and_
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

def top_routes_by_country(db: Session, country: str, start=None, end=None):
    ao = aliased(Airport)
    ad = aliased(Airport)
    R = Route
    q = (
        select(ao.iata, ad.iata, func.count().label("flights"))
        .join(ao, R.origin_id == ao.id)
        .join(ad, R.destination_id == ad.id)
        .where(ao.country == country, ad.country == country)
    )
    if start:
        q = q.where(R.flight_date >= start)
    if end:
        q = q.where(R.flight_date <= end)
    q = q.group_by(ao.iata, ad.iata).order_by(func.count().desc()).limit(5)
    return db.execute(q).all()



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