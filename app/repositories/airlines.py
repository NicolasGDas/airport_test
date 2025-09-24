# from __future__ import annotations
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from sqlalchemy import select
from app.models import Airline

class AirlinesRepo:
    @staticmethod
    def get(db: Session, id_: int):
        """
        Obtiene una aerolínea por clave primaria.

        Args:
            db (Session): Sesión de base de datos.
            id_ (int): ID de la aerolínea.

        Returns:
            Airline | None: Instancia si existe, de lo contrario None.
        """
        return db.get(Airline, id_)
    
# Aca las deje aparte pero podrian ir adentro de la clase del repo como metodos estaticos
def get_by_codes(db: Session, *, iata: str | None, icao: str | None) -> Airline | None:
    """
    Busca una aerolínea por sus códigos IATA/ICAO (case-insensitive → se normaliza a upper()).

    Args:
        db (Session): Sesión de base de datos.
        iata (str | None): Código IATA (2 letras).
        icao (str | None): Código ICAO (3 letras).

    Returns:
        Airline | None: La aerolínea encontrada o None si no hay match.
    """
    if not iata and not icao:
        return None
    stmt = select(Airline)
    if iata:
        stmt = stmt.where(Airline.iata == iata.upper())
    if icao:
        stmt = stmt.where(Airline.icao == icao.upper())
    return db.execute(stmt).scalars().first()

def get_or_create(db: Session, *, iata: str | None, icao: str | None, defaults: dict | None = None) -> Airline | None:
    """
    Devuelve la aerolínea que matchee por IATA/ICAO o la crea si no existe ("último gana").

    - Normaliza IATA/ICAO a mayúsculas.
    - Intenta insertar con los valores provistos en `defaults`.
    - Si hay conflicto de unicidad, hace rollback y reconsulta por los códigos.

    Args:
        db (Session): Sesión de base de datos.
        iata (str | None): Código IATA (opcional).
        icao (str | None): Código ICAO (opcional).
        defaults (dict | None): Datos adicionales para crear la aerolínea (name, country, etc.).

    Returns:
        Airline | None: La aerolínea existente o recién creada; None si no hay códigos válidos.
    """
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

