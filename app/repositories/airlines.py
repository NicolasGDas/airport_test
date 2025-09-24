# from __future__ import annotations
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from sqlalchemy import select
from app.models import Airline
from app.ingest.fk_resolver import AirlineMaps


class AirlinesRepo:
    @staticmethod
    def preload_maps(db: Session) -> AirlineMaps:
        iata2id, icao2id, ext2id = {}, {}, {}
        # si Airline no tiene ext_id, quitá la columna y dejá ext2id={}
        for row in db.execute(select(Airline.id, Airline.iata, Airline.icao, getattr(Airline, "ext_id", None))):
            id_, iata, icao, ext = row
            if iata: iata2id[iata.upper()] = id_
            if icao: icao2id[icao.upper()]  = id_
            if ext is not None:
                try: ext2id[int(ext)] = id_
                except: pass
        return AirlineMaps(iata2id, icao2id, ext2id)

# Aca las deje aparte pero podrian ir adentro de la clase del repo, no hay problema.
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
