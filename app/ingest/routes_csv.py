import pandas as pd
from typing import List, Dict, Any, Tuple
from pydantic import ValidationError
from app.schemas.routes import RouteIn


def parse_routes_csv(file) -> Tuple[List[RouteIn], List[Dict[str, Any]]]:
    """
    Parsea un archivo CSV de rutas y devuelve objetos validados junto con los errores.

    El archivo puede venir con separador `|` o `,`. Si falla la lectura con `|`, 
    se reintenta con coma como separador. Cada fila se valida contra el esquema 
    Pydantic `RouteIn`.

    Args:
        file (IO): Objeto de archivo abierto (por ejemplo, `UploadFile.file`).

    Returns:
        Tuple[List[RouteIn], List[Dict[str, Any]]]:
            - Lista de instancias `RouteIn` validadas correctamente.
            - Lista de errores, donde cada error es un diccionario con:
                * "row": índice de la fila en el DataFrame.
                * "reason": motivo (ej. `"validation_error"`).
                * "errors": detalles de validación provistos por Pydantic.
                * "rec": representación segura de la fila original (sin NaN, todo string).

    Ejemplo de retorno de error:
        {
            "row": 5,
            "reason": "validation_error",
            "errors": [{"loc": ["capacity"], "msg": "value is not a valid integer"}],
            "rec": {"airline_id": "1", "capacity": "abc", ...}
        }
    """
    try:
        df = pd.read_csv(file, sep="|", engine="python", dtype=str)
    except Exception:
        file.seek(0)
        df = pd.read_csv(file, engine="python", dtype=str)

    items: List[RouteIn] = []
    errors: List[Dict[str, Any]] = []

    for idx, rec in enumerate(df.to_dict(orient="records")):
        try:
            items.append(RouteIn.model_validate(rec))
        except ValidationError as ve:
            safe_rec = {k: ("" if pd.isna(v) else str(v)) for k, v in rec.items()}
            errors.append(
                {
                    "row": idx,
                    "reason": "validation_error",
                    "errors": ve.errors(),
                    "rec": safe_rec,
                }
            )
    return items, errors
