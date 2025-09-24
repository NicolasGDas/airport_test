# app/services/routes_service.py
from typing import Dict, List
from sqlalchemy.orm import Session

from app.ingest.routes_csv import parse_routes_csv
from app.repositories.routes import RoutesRepo
from app.models import Route


def ingest_routes_service(db: Session, fileobj) -> Dict:
    """
    Procesa un archivo CSV de rutas y realiza la inserción en la base de datos.

    El flujo es:
      1. Parsear el archivo usando `parse_routes_csv`, que devuelve una lista de objetos
         `RouteIn` válidos y una lista de errores de parseo.
      2. Convertir los objetos válidos a instancias del modelo SQLAlchemy `Route`.
      3. Insertar las filas en la base de datos utilizando `RoutesRepo.bulk_insert`.
      4. Devolver un resumen con las métricas de la operación.

    Args:
        db (Session): Sesión de base de datos inyectada.
        fileobj (IO): Archivo CSV abierto en modo lectura (generalmente `UploadFile.file`).

    Returns:
        dict: Resumen del proceso de ingesta:
            - "inserted": cantidad de rutas insertadas correctamente.
            - "skipped": cantidad de filas descartadas por errores de parseo.
            - "skipped_preview": vista previa de hasta 10 errores detectados, 
              para ayudar a depuración.
    """
    items, parse_errors = parse_routes_csv(fileobj)
    rows: List[Route] = []

    for it in items:
        d = it.model_dump(by_alias=False, exclude_none=True)
        rows.append(Route(**d))

    if rows:
        RoutesRepo.bulk_insert(db, rows)

    return {
        "inserted": len(rows),
        "skipped": len(parse_errors),
        "skipped_preview": parse_errors[:10],  # para depurar por qué faltan IDs
    }
