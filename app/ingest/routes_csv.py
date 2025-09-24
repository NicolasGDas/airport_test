import pandas as pd
from app.schemas.routes import RouteIn
from typing import List
from pydantic import ValidationError

def parse_routes_csv(file) -> list[RouteIn]:
    def _read(sep=None):
        return pd.read_csv(file, sep=sep, engine="python", dtype=str)

    try:
        df = pd.read_csv(file, sep="|", engine="python", dtype=str)  # Asi esta este csv
    except Exception:
        file.seek(0)
        df = _read() # Por si no falla que lo haga generico


    df = df.loc[:, ~df.columns.str.match(r"^Unnamed")]
    df = df.applymap(lambda x: x.strip() if isinstance(x, str) else x)
    data = df.to_dict(orient="records")
    
    items: List[RouteIn] = []
    for rec in data:
        try:
            items.append(RouteIn.model_validate(rec))
        except ValidationError:
            print("Registro inválido, se ignora:", rec)
            continue
    return items