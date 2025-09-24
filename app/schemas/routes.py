from datetime import date
from typing import Optional
from decimal import Decimal, InvalidOperation
from pydantic import BaseModel, Field, field_validator, ConfigDict
import math

# Tokens que tratamos como nulos
NULL_TOKENS = {"", "nan", "NaN", "null", "none", "NULL", "None", "inf", "+inf", "-inf", "Infinity", "-Infinity"}


def _norm_float(v, *, allow_negative=True, ndigits: Optional[int] = None) -> Optional[float]:
    if v is None:
        return None
    s = str(v).strip().replace(",", ".")
    if s in NULL_TOKENS:
        return None
    try:
        f = float(s)
    except Exception:
        return None
    if not math.isfinite(f):
        return None
    if not allow_negative and f < 0:
        return None
    if ndigits is not None:
        f = round(f, ndigits)
    return f


def _norm_decimal(v, *, allow_negative=True, quant: Optional[str] = None) -> Optional[Decimal]:
    if v is None:
        return None
    s = str(v).strip().replace(",", ".")
    if s in NULL_TOKENS:
        return None
    try:
        d = Decimal(s)
    except (InvalidOperation, ValueError):
        return None
    if d.is_nan() or d == Decimal("Infinity") or d == Decimal("-Infinity"):
        return None
    if not allow_negative and d < 0:
        return None
    if quant is not None:
        d = d.quantize(Decimal(quant))  # ej: quant="0.01" para 2 decimales
    return d


class RouteIn(BaseModel):
    airline_id: int = Field(..., alias="IDAerolinea")
    origin_airport_id: int = Field(..., alias="AeropuertoOrigenID")
    destination_airport_id: int = Field(..., alias="AeropuertoDestinoID")

    operated_carrier: bool = Field(False, alias="OperadoCarrier")  # "" o "Y"
    stops: int = Field(0, alias="Stops")
    equipment: Optional[str] = Field(None, alias="Equipamiento")

    tickets_sold: Optional[int] = Field(None, alias="TicketsVendidos")
    capacity: Optional[int] = Field(None, alias="Lugares")
    price_ticket: Optional[Decimal] = Field(None, alias="PrecioTicket")
    total_kilometers: Optional[float] = Field(None, alias="KilometrosTotales")

    flight_date: Optional[date] = Field(None, alias="Fecha")

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    # --- Normalizaciones ---
    @field_validator("equipment", mode="before")
    @classmethod
    def _upper_or_none(cls, v):
        if v is None:
            return None
        s = str(v).strip()
        return s.upper() if s else None

    @field_validator("operated_carrier", mode="before")
    @classmethod
    def _bool_from_Y(cls, v):
        if v is None:
            return False
        return str(v).strip().upper() == "Y"

    @field_validator("price_ticket", mode="before")
    @classmethod
    def _price_decimal(cls, v):
        # sin negativos, con 2 decimales típicos de moneda
        return _norm_decimal(v, allow_negative=False, quant="0.01")

    @field_validator("total_kilometers", mode="before")
    @classmethod
    def _kms_float(cls, v):
        # sin negativos, sin redondeo automático
        return _norm_float(v, allow_negative=False)

    @field_validator(
        "stops",
        "tickets_sold",
        "capacity",
        "airline_id",
        "origin_airport_id",
        "destination_airport_id",
        mode="before",
    )
    @classmethod
    def _int_or_none(cls, v):
        if v is None:
            return None
        s = str(v).strip()
        if s == "" or s in NULL_TOKENS:
            return None
        try:
            # más estricto: si tiene decimales, no lo aceptamos como int
            if "." in s.replace(",", "."):
                return None
            return int(s.replace(",", ""))
        except Exception:
            return None

    @field_validator("flight_date", mode="before")
    @classmethod
    def _date_parse(cls, v):
        if v is None or str(v).strip() == "":
            return None
        import pandas as pd
        dt = pd.to_datetime(v, errors="coerce", dayfirst=False)
        return dt.date() if not pd.isna(dt) else None


class RouteOut(RouteIn):
    # Para devolver desde ORM / DTOs
    pass
