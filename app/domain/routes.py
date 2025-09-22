from pydantic import BaseModel
from datetime import date

class RouteIn(BaseModel):
    airline_iata: str | None = None
    origin_iata: str
    destination_iata: str
    capacity: int | None = None
    occupancy: float | None = None  # 0..1 or 0..100 -> normalized in services
    flight_date: date

class RouteOut(BaseModel):
    id: int
    airline_id: int | None = None
    origin_id: int
    destination_id: int
    capacity: int | None = None
    occupancy: float | None = None
    flight_date: date
    class Config:
        from_attributes = True
