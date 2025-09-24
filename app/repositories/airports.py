# from __future__ import annotations
from sqlalchemy.orm import Session
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from app.models import Airport


class AirportsRepo:
    @staticmethod
    def get(db: Session, id_: int) -> Airport | None:
        """
        Obtiene un aeropuerto por su clave primaria.

        Args:
            db (Session): Sesión de base de datos.
            id_ (int): Identificador del aeropuerto.

        Returns:
            Airport | None: Instancia del aeropuerto si existe, en caso contrario None.
        """
        return db.get(Airport, id_)

    @staticmethod
    def get_or_create(
        db: Session,
        *,
        iata: str | None,
        icao: str | None,
        defaults: dict | None = None
    ) -> Airport | None:
        """
        Devuelve un aeropuerto existente que matchee por IATA/ICAO (o por ID si viene en defaults),
        y si no existe lo crea con los datos provistos.

        Estrategia:
          1) Normaliza `iata`/`icao` a mayúsculas y arma el `data` de inserción (a partir de `defaults`).
          2) Busca primero por `(id)` si vino en `defaults`; si no, por `iata`/`icao`.
          3) Si no existe, intenta insertar. Si hay `IntegrityError` (conflicto de unicidad), hace
             rollback y reconsulta por códigos para retornar el existente.

        Args:
            db (Session): Sesión de base de datos.
            iata (str | None): Código IATA del aeropuerto (opcional).
            icao (str | None): Código ICAO del aeropuerto (opcional).
            defaults (dict | None): Datos para crear el aeropuerto si no existe (incluye
                eventualmente `id`, `name`, `city`, `country`, etc.).

        Returns:
            Airport | None: El aeropuerto correspondiente (existente o recién creado).
                Devuelve None solo si no hay datos suficientes para identificar/crear.
        """
        data = (defaults or {}).copy()
        if iata:
            data["iata"] = iata.upper()
        if icao:
            data["icao"] = icao.upper()

        ap = get_by_codes(
            db,
            iata=data.get("iata"),
            icao=data.get("icao"),
            id=defaults.get("id", None) if defaults else None,
        )
        if ap:
            return ap

        ap = Airport(**data)
        db.add(ap)
        try:
            db.commit()
        except IntegrityError:
            # En caso de colisión por constraints únicos, reconciliamos con una re-búsqueda.
            db.rollback()
            ap = get_by_codes(
                db,
                iata=iata,
                icao=icao,
                id=defaults.get("id", None) if defaults else None,
            )
            if ap:
                return ap
            raise
        db.refresh(ap)
        return ap


# Lo puedo mandar al utils porque se reutiliza muchas veces
def get_by_codes(
    db: Session,
    *,
    iata: str | None,
    icao: str | None,
    id: int | None = None
) -> Airport | None:
    """
    Busca un aeropuerto por `id` (si se provee) o por códigos `iata`/`icao`.

    Reglas de búsqueda:
      - Si viene `id`, se busca exclusivamente por `id`.
      - Si no viene `id` y no hay `iata` ni `icao`, devuelve None (no hay criterios).
      - Si vienen ambos `iata` e `icao`, se usa condición **OR** entre ambos códigos.
      - Si viene solo uno, se filtra por ese código.

    **Nota:** Esta función no fuerza mayúsculas; se asume que quien llama ya normalizó
    `iata`/`icao` si es necesario.

    Args:
        db (Session): Sesión de base de datos.
        iata (str | None): Código IATA (opcional).
        icao (str | None): Código ICAO (opcional).
        id (int | None): Identificador del aeropuerto (opcional).

    Returns:
        Airport | None: El aeropuerto encontrado o None si no hay coincidencias.
    """
    stmt = select(Airport)
    if id:
        stmt = stmt.where(Airport.id == id)
    elif not iata and not icao:
        return None
    elif iata and icao:
        # OR: matchea si coincide por IATA o por ICAO
        stmt = stmt.where((Airport.iata == iata) | (Airport.icao == icao))
    elif iata and not icao:
        stmt = stmt.where(Airport.iata == iata)
    else:
        stmt = stmt.where(Airport.icao == icao)

    return db.execute(stmt).scalars().first()
