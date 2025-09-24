
import pandas as pd
from app.schemas.airlines import AirlineIn

def parse_airlines_csv(file) -> list[AirlineIn]:
    try:
        df = pd.read_csv(file, sep=",", encoding="utf-8")
    except Exception:
        file.seek(0)
        df = pd.read_csv(file, sep=",", engine="python")
    return [
        AirlineIn.model_validate(rec).model_dump()
        for rec in df.to_dict(orient="records")
    ]
