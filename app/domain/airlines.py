from pydantic import BaseModel

class AirlineIn(BaseModel):
    name: str | None = None
    iata: str | None = None
    icao: str | None = None
    country: str | None = None

class AirlineOut(AirlineIn):
    id: int
    class Config:
        from_attributes = True
