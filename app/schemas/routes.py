from datetime import date
from typing import Optional
from decimal import Decimal
from pydantic import BaseModel, Field, field_validator, ConfigDict

class RouteIn(BaseModel):
    
    airline_code: Optional[str] = Field(None, alias="CodAerolinea")
    airline_id: Optional[int]   = Field(None, alias="IDAerolinea")

    origin_code: Optional[str]  = Field(None, alias="AeropuertoOrigen")
    origin_id: Optional[int]    = Field(None, alias="AeropuertoOrigenID")

    destination_code: Optional[str] = Field(None, alias="AeropuertoDestino")
    destination_id: Optional[int]   = Field(None, alias="AeropuertoDestinoID")


    operated_carrier: bool = Field(False, alias="OperadoCarrier")   # "" o "Y"
    stops: int = Field(0, alias="Stops")
    equipment: Optional[str] = Field(None, alias="Equipamiento")

    tickets_sold: Optional[int]      = Field(None, alias="TicketsVendidos")
    capacity: Optional[int]          = Field(None, alias="Lugares")
    price_ticket: Optional[Decimal]  = Field(None, alias="PrecioTicket")
    total_kilometers: Optional[float]= Field(None, alias="KilometrosTotales")

    flight_date: Optional[date] = Field(None, alias="Fecha")


    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    # Normalizaciones
    @field_validator("airline_code", "origin_code", "destination_code", "equipment", mode="before")
    @classmethod
    def _upper_or_none(cls, v):
        if v is None: return None
        s = str(v).strip()
        return s.upper() if s else None

    @field_validator("operated_carrier", mode="before")
    @classmethod
    def _bool_from_Y(cls, v):
        if v is None: return False
        return str(v).strip().upper() == "Y"

    @field_validator("price_ticket", mode="before")
    @classmethod
    def _decimal_comma(cls, v):
        if v is None: return None
        s = str(v).strip().replace(",", ".")
        return s if s else None  # Decimal lo parsea luego

    @field_validator("total_kilometers", mode="before")
    @classmethod
    def _float_comma(cls, v):
        if v is None: return None
        s = str(v).strip().replace(",", ".")
        return float(s) if s else None

    @field_validator("stops", "tickets_sold", "capacity", "airline_id", "origin_id", "destination_id", mode="before")
    @classmethod
    def _int_or_none(cls, v):
        if v is None: return None
        s = str(v).strip()
        if s == "": return None
        try:
            return int(float(s.replace(",", ".")))
        except Exception:
            return None

    @field_validator("flight_date", mode="before")
    @classmethod
    def _date_parse(cls, v):
        # Acepta "YYYY-MM-DD" del CSV; si usás otro formato, ajustá acá
        from datetime import date
        import pandas as pd
        if v is None or str(v).strip() == "": return None
        dt = pd.to_datetime(v, errors="coerce", dayfirst=False)
        return dt.date() if not pd.isna(dt) else None


class RouteOut(RouteIn):
    # Para devolver desde ORM / DTOs
    pass
