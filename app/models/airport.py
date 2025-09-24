from sqlalchemy import (
    String, Integer, Numeric, CheckConstraint, UniqueConstraint, Index, text
)
from sqlalchemy.dialects.postgresql import VARCHAR
from sqlalchemy.orm import Mapped, mapped_column
from app.db.session import Base


class Airport(Base):
    __tablename__ = "airports"

    # PK interno (autoincremental) distinto del IDAirport del dataset
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)


    # Campos principales
    name: Mapped[str] = mapped_column(String(200), nullable=False, index=True)
    city: Mapped[str | None] = mapped_column(String(120), nullable=True, index=True)
    country: Mapped[str] = mapped_column(String(100), nullable=False, index=True)

    # Códigos
    iata: Mapped[str | None] = mapped_column(String(3), nullable=True, index=True)
    icao: Mapped[str | None] = mapped_column(String(4), nullable=True, index=True)

    # Geográficos
    latitude: Mapped[float] = mapped_column(Numeric(9, 6), nullable=False)
    longitude: Mapped[float] = mapped_column(Numeric(9, 6), nullable=False)
    altitude_ft: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # Zona horaria / offset
    utc_offset: Mapped[float | None] = mapped_column(Numeric(4, 2), nullable=True)
    continent_code: Mapped[str | None] = mapped_column(String(2), nullable=True)  # en tu CSV venía 1 letra, dejamos 2 por flex
    timezone_olson: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)

    __table_args__ = (
        # Rango de lat/lon
        CheckConstraint("latitude >= -90 AND latitude <= 90", name="ck_airport_lat_range"),
        CheckConstraint("longitude >= -180 AND longitude <= 180", name="ck_airport_lon_range"),

        
        CheckConstraint(
            "(utc_offset IS NULL) OR (utc_offset BETWEEN -12 AND 14 AND mod(((utc_offset * 60)::int), 15) = 0)",
            name="ck_airport_utc_quarter_steps",
        ),


        # Unicidad parcial (PostgreSQL) — permite varios NULL y exige unicidad cuando hay valor
        # UniqueConstraint("iata", name="uq_airport_iata_not_null", deferrable=False, initially="IMMEDIATE"),
        # UniqueConstraint("icao", name="uq_airport_icao_not_null", deferrable=False, initially="IMMEDIATE"),


        # Índices compuestos útiles para queries
        Index("ix_airport_country_city", "country", "city"),
    )
