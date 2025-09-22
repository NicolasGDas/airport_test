# from __future__ import annotations
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import String, Integer, Float, UniqueConstraint

from app.db.session import Base

class Airport(Base):
    __tablename__ = "airports"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str | None] = mapped_column(String(200))
    city: Mapped[str | None] = mapped_column(String(100))
    country: Mapped[str | None] = mapped_column(String(100), index=True)
    iata: Mapped[str | None] = mapped_column(String(3), index=True)
    icao: Mapped[str | None] = mapped_column(String(4), index=True)
    latitude: Mapped[float | None] = mapped_column(Float)
    longitude: Mapped[float | None] = mapped_column(Float)
    altitude_m: Mapped[float | None] = mapped_column(Float)

    __table_args__ = (
        UniqueConstraint("iata", name="uq_airport_iata"),
        UniqueConstraint("icao", name="uq_airport_icao"),
    )
