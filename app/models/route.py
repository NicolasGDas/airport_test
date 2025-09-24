# from __future__ import annotations
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import Integer, Float, Date, ForeignKey, Index, Boolean, Text

from app.db.session import Base

class Route(Base):
    __tablename__ = "routes"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    airline_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("airlines.id"))
    origin_airport_id: Mapped[int] = mapped_column(Integer, ForeignKey("airports.id"))
    destination_airport_id: Mapped[int] = mapped_column(Integer, ForeignKey("airports.id"))
    capacity: Mapped[int | None] = mapped_column(Integer)
    flight_date: Mapped["Date"] = mapped_column(Date, index=True)
    operated_carrier: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    stops: Mapped[int] = mapped_column(Integer, default=0)
    equipment: Mapped[str | None] = mapped_column(Text)
    tickets_sold: Mapped[int | None] = mapped_column(Integer)
    price_ticket: Mapped[float | None] = mapped_column(Float)
    total_kilometers: Mapped[float | None] = mapped_column(Float)
    
    
    airline = relationship("Airline")
    origin = relationship("Airport", foreign_keys=[origin_airport_id])
    destination = relationship("Airport", foreign_keys=[destination_airport_id])

    __table_args__ = (
        Index("ix_routes_od", "origin_airport_id", "destination_airport_id"),
        Index("ix_routes_airline_od", "airline_id", "origin_airport_id", "destination_airport_id"),
    )
