from typing import Optional, Any, Dict
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from datetime import datetime, timedelta
from pydantic import BaseModel, Field, field_validator, model_validator, ConfigDict
import re

# zoneinfo está en stdlib (py>=3.9)
try:
    from zoneinfo import ZoneInfo
except Exception:
    ZoneInfo = None  # fallback si no estuviera disponible

# --- Normalización de tokens "vacíos" en strings ---
IATA_RE = re.compile(r"^[A-Z]{3}$")
ICAO_RE = re.compile(r"^[A-Z]{4}$")
NULL_TOKENS = {
    "", "N", "NA", "N/A", "NONE", "NULL", "\\N", "-", "--",
    "NAN", "NAN()", "NULL()", "?", "UNKNOWN"
}


class AirportIn(BaseModel):
    ext_id: int                   = Field(..., alias="IDAirport")  # ID externo del dataset
    name: str                     = Field(..., alias="NombreAeropuerto")
    city: Optional[str]           = Field(None, alias="Ciudad")
    country: str                  = Field(..., alias="Pais")
    iata: Optional[str]           = Field(None, alias="CodigoAeropuerto")
    icao: Optional[str]           = Field(None, alias="icao")
    latitude: float               = Field(..., alias="Latitud")
    longitude: float              = Field(..., alias="Longitud")
    altitude_ft: Optional[int]    = Field(None, alias="Altitud")
    utc_offset: Optional[float]   = Field(None, alias="DifUTC")
    continent_code: Optional[str] = Field(None, alias="CodigoContinente")
    timezone_olson: Optional[str] = Field(None, alias="TimezoneOlson")

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    # --------- Normalizaciones básicas ---------
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

    @field_validator("continent_code", mode="before")
    @classmethod
    def _norm_continent(cls, v):
        if v is None:
            return None
        s = str(v).strip().upper()
        if s in NULL_TOKENS:
            return None
        # si querés forzar 1 letra, usá s[:1]
        return s[:2] or None

    @field_validator("timezone_olson", "city", "name", "country", mode="before")
    @classmethod
    def _strip_empty(cls, v):
        if v is None:
            return None
        s = str(v).strip()
        return s or None

    @field_validator("altitude_ft", mode="before")
    @classmethod
    def _int_or_none(cls, v):
        if v is None:
            return None
        s = str(v).strip().replace(",", ".")
        try:
            return int(float(s))
        except Exception:
            return None

    # --------- Coordenadas: reparar formatos y validar rango ---------
    @field_validator("latitude", "longitude", mode="before")
    @classmethod
    def _fix_coords(cls, v, info):
        """
        Repara coordenadas con puntos de miles/decimales corridos.
        - Si parsea y es plausible: devuelve.
        - Si parsea y es implausible: corre el decimal a la izquierda hasta entrar en rango.
        - Si no parsea: reconstruye desde dígitos (A: últimos 6 decimales; B: long con 3 enteros).
        """
        if v is None or str(v).strip() == "":
            return None

        s = str(v).strip().replace(",", ".")
        limit = 90 if info.field_name == "latitude" else 180

        def plausible(x: float) -> bool:
            return -limit <= x <= limit

        def reparse_from_digits(raw: str) -> Optional[float]:
            sign = -1 if raw.startswith("-") else 1
            digits = "".join(ch for ch in raw if ch.isdigit())
            if not digits:
                return None
            # Candidato A: últimos 6 como fracción (común en datasets)
            if len(digits) > 6:
                cand_a = sign * float(f"{digits[:-6]}.{digits[-6:]}")
            else:
                cand_a = sign * float(digits)
            # Candidato B (solo longitudes): 3 dígitos enteros + resto fracción
            cand_b = None
            if info.field_name == "longitude" and len(digits) >= 4:
                cand_b = sign * float(f"{digits[:3]}.{digits[3:] or '0'}")
            # Elegir el más plausible (si A < 10 y B >= 10 y plausible, preferir B)
            if cand_b is not None and plausible(cand_b) and (abs(cand_a) < 10 <= abs(cand_b)):
                return cand_b
            return cand_a if plausible(cand_a) else (cand_b if (cand_b is not None and plausible(cand_b)) else None)

        # 1) Intento directo
        try:
            x = float(s)
            if plausible(x):
                return x
            # 2) Si no es plausible, correr el decimal hacia la izquierda
            y = x
            while abs(y) > limit and abs(y) >= 1:
                y /= 10.0
            if plausible(y):
                return y
            # 3) Fallback: reparsear desde dígitos
            alt = reparse_from_digits(s)
            return alt if alt is not None else x
        except Exception:
            # 4) No parseó: usar estrategia por dígitos
            alt = reparse_from_digits(s)
            return alt

    @field_validator("latitude")
    @classmethod
    def _lat_range(cls, v: float):
        if v is None:
            return None
        if not (-90.0 <= float(v) <= 90.0):
            raise ValueError("Latitud fuera de rango (-90..90)")
        return float(v)

    @field_validator("longitude")
    @classmethod
    def _lon_range(cls, v: float):
        if v is None:
            return None
        if not (-180.0 <= float(v) <= 180.0):
            raise ValueError("Longitud fuera de rango (-180..180)")
        return float(v)

    # --------- UTC offset: acepta H:MM, decimales, minutos y fallback desde TZ ---------
    @staticmethod
    def _is_valid_quarter(d: Decimal) -> bool:
        return Decimal("-12") <= d <= Decimal("14") and (d * 4) == (d * 4).to_integral_value()

    @staticmethod
    def _snap_quarter(d: Decimal) -> Decimal:
        # redondea al cuarto de hora más cercano: .00, .25, .50, .75
        return (d * 4).to_integral_value(rounding=ROUND_HALF_UP) / Decimal(4)

    @classmethod
    def _parse_utc_any(cls, raw: Any) -> Optional[Decimal]:
        """
        Acepta:
          - "5.75", "-3.5", "12,75"  (horas decimales)
          - "5:45", "-3:30", "+9:00" (H:MM)
          - "160", "230"             (minutos → horas; se snapea a 15')
        Devuelve Decimal en múltiplos de 0.25 dentro de [-12, 14], o None si no se pudo.
        """
        if raw is None or str(raw).strip() == "":
            return None
        s = str(raw).strip().replace(",", ".")

        # (1) H:MM
        if ":" in s:
            try:
                sign = -1 if s.startswith("-") else 1
                hh, mm = s.replace("+", "").replace("-", "").split(":")
                h = int(hh)
                m = int(mm)
                d = Decimal(sign) * (Decimal(h) + Decimal(m) / Decimal(60))
                d = cls._snap_quarter(d)
                return d if cls._is_valid_quarter(d) else None
            except Exception:
                pass

        # (2) Horas decimales
        try:
            d = Decimal(s)
            if cls._is_valid_quarter(d):
                return d
            if Decimal("-12") <= d <= Decimal("14"):
                d2 = cls._snap_quarter(d)
                return d2 if cls._is_valid_quarter(d2) else None
        except InvalidOperation:
            pass

        # (3) ¿minutos? (valor absoluto mayor a 14 horas → probablemente minutos)
        try:
            x = Decimal(s)
            if abs(x) > Decimal("14") and abs(x) <= Decimal("840"):  # 14h = 840m
                d = x / Decimal(60)
                d = cls._snap_quarter(d)
                return d if cls._is_valid_quarter(d) else None
        except InvalidOperation:
            pass

        return None

    @field_validator("utc_offset", mode="before")
    @classmethod
    def _coerce_utc_offset(cls, v):
        """
        Normaliza DifUTC a float en múltiplos de 15'.
        No consulta otros campos; si no se puede parsear, retorna None y el model_validator intentará tz.
        """
        d = cls._parse_utc_any(v)
        return float(d) if d is not None else None

    @model_validator(mode="before")
    @classmethod
    def _fill_utc_from_tz(cls, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Si DifUTC vino vacío o inválido, intenta derivarlo desde TimezoneOlson (zona IANA).
        """
        dif = data.get("DifUTC")
        tz  = data.get("TimezoneOlson") or data.get("timezone_olson")

        # ¿ya hay algo parseable?
        parsed = cls._parse_utc_any(dif)
        if parsed is not None:
            data["DifUTC"] = float(parsed)
            return data

        # Fallback desde TZ
        if tz and ZoneInfo is not None:
            try:
                # Fecha fija para evitar líos de DST
                dt = datetime(2025, 1, 1, 12, 0, 0, tzinfo=ZoneInfo(tz))
                delta = dt.utcoffset()
                if delta is not None:
                    hours = Decimal(delta / timedelta(hours=1))
                    hours = cls._snap_quarter(hours)
                    if cls._is_valid_quarter(hours):
                        data["DifUTC"] = float(hours)
                        return data
            except Exception:
                pass

        data["DifUTC"] = None
        return data
