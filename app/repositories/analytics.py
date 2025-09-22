# from __future__ import annotations
from sqlalchemy.orm import Session, aliased
from sqlalchemy import select, func, case
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

def domestic_altitude_percentage(db: Session, min_occupancy: float):
    ao = aliased(Airport)
    ad = aliased(Airport)
    R = Route
    q = (
        select(
            func.count().label("total"),
            func.sum(case((func.abs(ao.altitude_m - ad.altitude_m) > 1000, 1), else_=0)).label("over_1000")
        )
        .join(ao, R.origin_id == ao.id)
        .join(ad, R.destination_id == ad.id)
        .where(R.occupancy >= min_occupancy)
        .where(ao.country == ad.country)
    )
    total, over = db.execute(q).first() or (0, 0)
    pct = float(over) / float(total) if total else 0.0
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
