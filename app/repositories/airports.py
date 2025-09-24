# from __future__ import annotations
from sqlalchemy.orm import Session
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from app.models import Airport

class AirportsRepo:
    @staticmethod
    def get(db: Session, id_: int):
        return db.get(Airport, id_)

    
    @staticmethod
    def get_or_create(db: Session, *, iata: str | None, icao: str | None, defaults: dict | None = None) -> Airport | None:
        data = (defaults or {}).copy()
        if iata:
            data["iata"] = iata.upper()
        if icao:
            data["icao"] = icao.upper()
        ap = get_by_codes(db, iata=data.get("iata"), icao=data.get("icao"), id=defaults.get("id", None))
        if ap:
            return ap
        ap = Airport(**data)
        db.add(ap)
        try:
            db.commit()
        except IntegrityError:
            db.rollback()
            ap = get_by_codes(db, iata=iata, icao=icao,id=defaults.get("id", None))
            if ap:
                return ap
            raise
        db.refresh(ap)
        return ap

 # Lo puedo mandar al utils porque se reutiliza muchas veces
def get_by_codes(db: Session, *, iata: str | None, icao: str | None, id: int | None = None) -> Airport | None:
    stmt = select(Airport)
    if id:
        stmt = stmt.where(Airport.id == id)
    elif not iata and not icao:
        return None
    elif iata and icao:
        stmt = stmt.where((Airport.iata == iata) | (Airport.icao == icao))
    elif iata and not icao:
        stmt = stmt.where(Airport.iata == iata)
    else:
        stmt = stmt.where(Airport.icao == icao)
    return db.execute(stmt).scalars().first()

