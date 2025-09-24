import pandas as pd
from app.schemas.airports import AirportIn


def parse_airports_csv(file) -> list[AirportIn]:
    """
    Parsea un archivo CSV de aeropuertos y devuelve registros validados.

    El archivo se intenta leer en UTF-8 con separador de coma. Si falla,
    se reintenta con el motor de Python. Cada fila se valida contra el 
    esquema Pydantic `AirportIn`.

    Args:
        file (IO): Objeto de archivo abierto (por ejemplo, `UploadFile.file`).

    Returns:
        list[AirportIn]: Lista de aeropuertos validados y convertidos a diccionarios
        mediante `model_dump()`.

    Ejemplo de estructura de salida:
        [
            {"id": 4206, "name": "Mactan-Cebu International", "city": "Cebu", "country": "Philippines", "iata": "CEB", "icao": "RPVM"},
            {"id": 1234, "name": "Aeropuerto Internacional Ezeiza", "city": "Buenos Aires", "country": "Argentina", "iata": "EZE", "icao": "SAEZ"}
        ]
    """
    try:
        df = pd.read_csv(file, sep=",", encoding="utf-8")
    except Exception:
        file.seek(0)
        df = pd.read_csv(file, sep=",", engine="python")

    return [
        AirportIn.model_validate(rec).model_dump()
        for rec in df.to_dict(orient="records")
    ]
