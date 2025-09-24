from typing import Any

def normalize_occupancy(value):
    try:
        v = float(value)
        if v > 1.0:
            v = v / 100.0
        if v < 0:
            v = 0.0
        if v > 1:
            v = 1.0
        return v
    except Exception:
        return None




def parse_int(x: Any) -> int | None:
        try:
            if x is None or (isinstance(x, float) and pd.isna(x)): return None
            s = str(x).strip()
            if s == "": return None
            return int(float(s.replace(",", ".")))
        except Exception:
            return None

def parse_float(x: Any) -> float | None:
    try:
        if x is None or (isinstance(x, float) and pd.isna(x)): return None
        s = str(x).strip().replace(",", ".")
        if s == "": return None
        return float(s)
    except Exception:
        return None

def parse_bool_Y(x: Any) -> bool:
    if x is None or (isinstance(x, float) and pd.isna(x)): 
        return False
    return str(x).strip().upper() == "Y"

def norm_occ(val: Any) -> float | None:
    # Usa tu normalize_occupancy si existe; si no, hace clip 0..1
    try:
        return normalize_occupancy(val)  # type: ignore[name-defined]
    except Exception:
        v = parse_float(val)
        if v is None: 
            return None
        if v < 0: v = 0.0
        if v > 1: v = 1.0
        return v