# from __future__ import annotations
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from sqlalchemy import select
from app.models import Airline

class AirlinesRepo:
    @staticmethod
    def get(db: Session, id_: int):
        return db.get(Airline, id_)
    
# Aca las deje aparte pero podrian ir adentro de la clase del repo como staticmethods.
def get_by_codes(db: Session, *, iata: str | None, icao: str | None) -> Airline | None:
    if not iata and not icao:
        return None
    stmt = select(Airline)
    if iata:
        stmt = stmt.where(Airline.iata == iata.upper())
    if icao:
        stmt = stmt.where(Airline.icao == icao.upper())
    return db.execute(stmt).scalars().first()

def get_or_create(db: Session, *, iata: str | None, icao: str | None, defaults: dict | None = None) -> Airline | None:
    al = get_by_codes(db, iata=iata, icao=icao)
    if al:
        return al
    data = (defaults or {}).copy()
    if iata:
        data["iata"] = iata.upper()
    if icao:
        data["icao"] = icao.upper()
    
    al = Airline(**data)
    db.add(al)
    try:
        db.commit()          
        db.refresh(al)
        return al,None
    except IntegrityError:
        db.rollback()
        return None, get_by_codes(db, iata=iata, icao=icao)
