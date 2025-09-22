# from __future__ import annotations
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import Integer, Float, Date, ForeignKey, Index

from app.db.session import Base

class Route(Base):
    __tablename__ = "routes"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    airline_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("airlines.id"))
    origin_id: Mapped[int] = mapped_column(Integer, ForeignKey("airports.id"))
    destination_id: Mapped[int] = mapped_column(Integer, ForeignKey("airports.id"))
    capacity: Mapped[int | None] = mapped_column(Integer)
    occupancy: Mapped[float | None] = mapped_column(Float)  # 0..1
    flight_date: Mapped["Date"] = mapped_column(Date, index=True)

    airline = relationship("Airline")
    origin = relationship("Airport", foreign_keys=[origin_id])
    destination = relationship("Airport", foreign_keys=[destination_id])

    __table_args__ = (
        Index("ix_routes_od", "origin_id", "destination_id"),
        Index("ix_routes_airline_od", "airline_id", "origin_id", "destination_id"),
    )
