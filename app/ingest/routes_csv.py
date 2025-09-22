import pandas as pd
from app.core.utils import normalize_occupancy

def parse_routes_csv(file) -> list[dict]:
    try:
        df = pd.read_csv(file)
    except Exception:
        file.seek(0)
        df = pd.read_csv(file, sep='|', engine='python')
    cols = {c.lower(): c for c in df.columns}
    def pick(*names):
        for n in names:
            c = cols.get(n.lower())
            if c: return c
        return None

    airline_iata_c = pick("airline_iata", "codaerolinea", "iata")
    origin_c = pick("origin_iata", "aeropuertoorigen", "origen")
    dest_c = pick("destination_iata", "aeropuertodestino", "destino")
    capacity_c = pick("capacity", "lugares", "asientos")
    occ_c = pick("occupancy", "load_factor", "ticketsvendidos")
    date_c = pick("flight_date", "date", "fecha")

    out = []
    for _, row in df.iterrows():
        try:
            occ = None
            if occ_c:
                if occ_c.lower() == "ticketsvendidos" and capacity_c:
                    occ = normalize_occupancy(float(row[occ_c]) / float(row[capacity_c]) if pd.notna(row[occ_c]) and pd.notna(row[capacity_c]) else None)
                else:
                    occ = normalize_occupancy(row[occ_c])
            rec = {
                "airline_iata": str(row[airline_iata_c]).strip() if airline_iata_c else None,
                "origin_iata": str(row[origin_c]).strip() if origin_c else None,
                "destination_iata": str(row[dest_c]).strip() if dest_c else None,
                "capacity": int(row[capacity_c]) if capacity_c and pd.notna(row[capacity_c]) else None,
                "occupancy": occ,
                "flight_date": pd.to_datetime(row[date_c], errors="coerce").date() if date_c else None,
            }
            out.append(rec)
        except Exception:
            continue
    return out
