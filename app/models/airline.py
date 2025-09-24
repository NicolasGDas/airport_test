# from __future__ import annotations
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import String, Integer, UniqueConstraint

from app.db.session import Base

class Airline(Base):
    __tablename__ = "airlines"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str | None] = mapped_column(String(200))
    iata: Mapped[str | None] = mapped_column(String(3), index=True)
    icao: Mapped[str | None] = mapped_column(String(4), index=True)
    country: Mapped[str | None] = mapped_column(String(100))
    callsign: Mapped[str | None] = mapped_column(String(100))
    active: Mapped[bool] = mapped_column(default=True)
    aliases: Mapped[str | None] = mapped_column(String(200))

    __table_args__ = (
        UniqueConstraint("iata", name="uq_airline_iata"),
        UniqueConstraint("icao", name="uq_airline_icao"),
    )
