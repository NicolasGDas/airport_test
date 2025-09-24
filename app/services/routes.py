# app/services/routes_service.py
from typing import Dict, List
from sqlalchemy.orm import Session
from app.ingest.routes_csv import parse_routes_csv
from app.repositories.airports import AirportsRepo
from app.repositories.airlines import AirlinesRepo
from app.repositories.routes import RoutesRepo
from app.ingest.fk_resolver import resolve_route_fks
from app.schemas.routes import RouteIn
from app.models import Route

def ingest_routes_service(db: Session, fileobj) -> Dict:
    # 1) Parse + validar
    items: List[RouteIn] = parse_routes_csv(fileobj)

    # 2) Preload caches (1 query por tabla) para no tener que consultar por cada fila
    ap_maps = AirportsRepo.preload_maps(db)   # iata→id, icao→id, ext→id
    al_maps = AirlinesRepo.preload_maps(db)   # iata→id, icao→id, ext→id (si existe)

    # 3) Resolver FKs + construir modelos
    rows: List[Route] = []
    skipped = []

    for it in items:
        d = it.model_dump(by_alias=False)
        fk = resolve_route_fks(d, ap_maps, al_maps)

        if fk.origin_id is None or fk.dest_id is None:
            skipped.append({"reason": "airport_fk_missing", "rec": d})
            continue
        if d["flight_date"] is None:  # tu columna es NOT NULL
            skipped.append({"reason": "flight_date_null", "rec": d})
            continue

        rows.append(Route(
            airline_id=fk.airline_id,  # puede ser None (nullable)
            origin_airport_id=fk.origin_id,
            destination_airport_id=fk.dest_id,
            capacity=d.get("capacity"),
            flight_date=d["flight_date"],
            operated_carrier=d.get("operated_carrier", False),
            stops=d.get("stops", 0),
            equipment=d.get("equipment"),
            tickets_sold=d.get("tickets_sold"),
            price_ticket=float(d["price_ticket"]) if d.get("price_ticket") is not None else None,
            total_kilometers=d.get("total_kilometers"),
        ))

    # 4) Persistir
    if rows:
        RoutesRepo.bulk_insert(db, rows)

    return {"inserted": len(rows), "skipped": len(skipped), "skipped_preview": skipped[:10]}
