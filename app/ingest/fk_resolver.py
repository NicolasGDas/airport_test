
from dataclasses import dataclass
from typing import Dict, Optional

@dataclass
class AirportMaps:
    iata2id: Dict[str,int]
    icao2id: Dict[str,int]
    ext2id:  Dict[int,int]

@dataclass
class AirlineMaps:
    iata2id: Dict[str,int]
    icao2id: Dict[str,int]
    ext2id:  Dict[int,int]

@dataclass
class RouteFKs:
    origin_id: Optional[int]
    dest_id:   Optional[int]
    airline_id: Optional[int]

def _resolve_airport(d: dict, code_key: str, ext_key: str, ap: AirportMaps) -> Optional[int]:
    ext = d.get(ext_key)
    if ext not in (None, ""):
        try:
            ext_i = int(ext)
            if ext_i in ap.ext2id:
                return ap.ext2id[ext_i]
        except: pass
    code = d.get(code_key)
    if code:
        c = code.strip().upper()
        if len(c) == 4 and c in ap.icao2id: return ap.icao2id[c]
        if len(c) == 3 and c in ap.iata2id: return ap.iata2id[c]
    return None

def _resolve_airline(d: dict, al: AirlineMaps) -> Optional[int]:
    ext = d.get("airline_id")
    if ext not in (None, ""):
        try:
            ext_i = int(ext)
            if ext_i in al.ext2id:
                return al.ext2id[ext_i]
        except: pass
    code = d.get("airline_code")
    if code:
        c = code.strip().upper()
        if len(c) == 3 and c in al.icao2id: return al.icao2id[c]
        if len(c) <= 2 and c in al.iata2id: return al.iata2id[c]
    return None

def resolve_route_fks(d: dict, ap_maps: AirportMaps, al_maps: AirlineMaps) -> RouteFKs:
    return RouteFKs(
        origin_id=_resolve_airport(d, "origin_code", "origin_id", ap_maps),
        dest_id=_resolve_airport(d, "destination_code", "destination_id", ap_maps),
        airline_id=_resolve_airline(d, al_maps),
    )
