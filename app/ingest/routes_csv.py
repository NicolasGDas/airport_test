import pandas as pd
from typing import List, Dict, Any, Tuple
from pydantic import ValidationError
from app.schemas.routes import RouteIn

def parse_routes_csv(file) -> Tuple[List[RouteIn], List[Dict[str, Any]]]:
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
            errors.append({"row": idx, "reason": "validation_error", "errors": ve.errors(), "rec": safe_rec})
    return items, errors
