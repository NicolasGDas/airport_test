import re
import pandas as pd

#Compiled regex patterns for IATA and ICAO codes
IATA_RE = re.compile(r"^[A-Z]{3}$")
ICAO_RE = re.compile(r"^[A-Z]{4}$")

def parse_airlines_csv(file) -> list[dict]:
    df = pd.read_csv(file)
    cols = [c.lower() for c in df.columns]
    
    def col(name):
        return df.columns[cols.index(name)] if name in cols else None
    
    name_c = col("nombreaerolinea")
    iata_c = col("iata")
    icao_c = col("icao")
    country_c = col("country") or col("pais")
    alias_c = col("alias")
    calsign_c = col("callsign")
    active_c = col("active")
    
    out = []
    
    for _, row in df.iterrows():
        
        iata_val = str(row[iata_c]).strip().upper() if iata_c and pd.notna(row[iata_c]) else None   
        icao_val = str(row[icao_c]).strip() if icao_c and pd.notna(row[icao_c]) else None
        
        if iata_val and not IATA_RE.match(iata_val):
            iata_val = None
        
        if icao_val and not ICAO_RE.match(icao_val):
            icao_val = None
        
        out.append({
            "name": row[name_c] if name_c else None,
            "iata": iata_val,
            "icao": icao_val,
            "country": row[country_c] if country_c else None,
            "callsign": row[calsign_c] if calsign_c else None,
            "active": (str(row[active_c]).strip().upper() == "Y" if active_c and pd.notna(row[active_c]) else True),
            "aliases": row[alias_c] if alias_c else None,
        })
    return out
