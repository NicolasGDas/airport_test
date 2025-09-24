# from __future__ import annotations
from sqlalchemy.orm import Session
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from app.models import Airport
from app.ingest.fk_resolver import AirportMaps

class AirportsRepo:
    @staticmethod
    def preload_maps(db: Session) -> AirportMaps:
        iata2id, icao2id, ext2id = {}, {}, {}
        for id_, iata, icao, ext in db.execute(
            select(Airport.id, Airport.iata, Airport.icao, Airport.ext_id)
        ):
            if iata: iata2id[iata.upper()] = id_
            if icao: icao2id[icao.upper()]  = id_
            if ext is not None:
                try: ext2id[int(ext)] = id_
                except: pass
        return AirportMaps(iata2id, icao2id, ext2id)


 # Aca las deje aparte pero podrian ir adentro de la clase del repo, no hay problema.
def get_by_codes(db: Session, *, iata: str | None, icao: str | None) -> Airport | None:
    if not iata and not icao:
        return None
    stmt = select(Airport)
    if iata and icao:
        stmt = stmt.where((Airport.iata == iata.upper()) | (Airport.icao == icao.upper()))
    elif iata and not icao:
        stmt = stmt.where(Airport.iata == iata.upper())
    else:
        stmt = stmt.where(Airport.icao == icao.upper())
    return db.execute(stmt).scalars().first()

def get_or_create(db: Session, *, iata: str | None, icao: str | None, defaults: dict | None = None) -> Airport | None:
    ap = get_by_codes(db, iata=iata, icao=icao)
    if ap:
        return ap
    data = (defaults or {}).copy()
    if iata:
        data["iata"] = iata.upper()
    if icao:
        data["icao"] = icao.upper()
    ap = Airport(**data)
    db.add(ap)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        ap = get_by_codes(db, iata=iata, icao=icao)
        if ap:
            return ap
        raise
    db.refresh(ap)
    return ap


