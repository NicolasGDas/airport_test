import pandas as pd

def parse_airlines_csv(file) -> list[dict]:
    df = pd.read_csv(file)
    cols = [c.lower() for c in df.columns]
    def col(name):
        return df.columns[cols.index(name)] if name in cols else None
    name_c = col("name") or col("nombreaerolinea")
    iata_c = col("iata")
    icao_c = col("icao")
    country_c = col("country") or col("pais")
    out = []
    for _, row in df.iterrows():
        out.append({
            "name": row[name_c] if name_c else None,
            "iata": (str(row[iata_c]).strip() if iata_c and pd.notna(row[iata_c]) else None),
            "icao": (str(row[icao_c]).strip() if icao_c and pd.notna(row[icao_c]) else None),
            "country": row[country_c] if country_c else None,
        })
    return out
