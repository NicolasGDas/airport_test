import pandas as pd
from app.schemas.airlines import AirlineIn


def parse_airlines_csv(file) -> list[AirlineIn]:
    """
    Parsea un archivo CSV de aerolíneas y devuelve registros validados.

    El archivo se intenta leer en UTF-8 con separador de coma. Si falla, 
    se reintenta con el motor de Python. Cada fila se valida contra el 
    esquema Pydantic `AirlineIn`.

    Args:
        file (IO): Objeto de archivo abierto (por ejemplo, `UploadFile.file`).

    Returns:
        list[AirlineIn]: Lista de aerolíneas validadas y convertidas a 
        diccionarios mediante `model_dump()`.

    Ejemplo de estructura de salida:
        [
            {"id": 1, "name": "American Airlines", "iata": "AA", "icao": "AAL", "country": "United States"},
            {"id": 2, "name": "Aerolíneas Argentinas", "iata": "AR", "icao": "ARG", "country": "Argentina"}
        ]
    """
    try:
        df = pd.read_csv(file, sep=",", encoding="utf-8")
    except Exception:
        file.seek(0)
        df = pd.read_csv(file, sep=",", engine="python")
    return [
        AirlineIn.model_validate(rec).model_dump()
        for rec in df.to_dict(orient="records")
    ]
