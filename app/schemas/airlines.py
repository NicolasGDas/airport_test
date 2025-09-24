import re
from pydantic import BaseModel, Field, field_validator
from typing import Optional

IATA_RE = re.compile(r"^[A-Z]{3}$")
ICAO_RE = re.compile(r"^[A-Z]{4}$")
NULL_TOKENS = {
    "", "N", "NA", "N/A", "NONE", "NULL", "\\N", "-", "--",
    "NAN", "NAN()", "NULL()", "?", "UNKNOWN"
}
class AirlineIn(BaseModel):
    id: int  = Field(None, alias="IDAerolinea")
    name: Optional[str] = Field(None, alias="NombreAerolinea")
    iata: Optional[str] = Field(None, alias="IATA")
    icao: Optional[str] = Field(None, alias="ICAO")
    country: Optional[str] = Field(None, alias="Pais")
    callsign: Optional[str] = Field(None, alias="Callsign")
    active: Optional[bool] = Field(None, alias="Activa")  # "Y" o "N"
    aliases: Optional[str] = Field(None, alias="Alias")




    @field_validator("iata", mode="before")
    @classmethod
    def _norm_iata(cls, v):
        if v is None:
            return None
        s = str(v).strip().upper()
        if s in NULL_TOKENS:
            return None
        return s if IATA_RE.fullmatch(s) else None

    @field_validator("icao", mode="before")
    @classmethod
    def _norm_icao(cls, v):
        if v is None:
            return None
        s = str(v).strip().upper()
        if s in NULL_TOKENS:
            return None
        return s if ICAO_RE.fullmatch(s) else None

    @field_validator("active", mode="before")
    @classmethod
    def _bool_from_Y(cls, v):
        if v is None: return False
        return str(v).strip().upper() == "Y"


    @field_validator("name", "country", "callsign", "aliases", mode="before")
    def _norm_empty(cls, v):
        if v is None:
            return None
        s = str(v).strip()
        return s if s and s.upper() not in NULL_TOKENS else None



class AirlineOut(AirlineIn):
    id: int
    class Config:
        from_attributes = True
