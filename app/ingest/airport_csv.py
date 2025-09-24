import pandas as pd
from app.schemas.airports import AirportIn



def parse_airports_csv(file) -> list[AirportIn]:
    try:
        df = pd.read_csv(file, sep=",", encoding="utf-8")
    except Exception:
        file.seek(0)
        df = pd.read_csv(file, sep=",", engine="python")
        
    return [
        AirportIn.model_validate(rec).model_dump()
        for rec in df.to_dict(orient="records")
    ]