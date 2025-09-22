from pydantic import BaseModel

class AirportIn(BaseModel):
    name: str | None = None
    city: str | None = None
    country: str | None = None
    iata: str | None = None
    icao: str | None = None
    latitude: float | None = None
    longitude: float | None = None
    altitude_m: float | None = None

class AirportOut(AirportIn):
    id: int
    class Config:
        from_attributes = True
