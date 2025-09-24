from pydantic import BaseModel
from datetime import date
from typing import Optional
class AverageOccupancyItem(BaseModel):
    airline: str | None
    avg_occupancy: float | None

class DomesticAltitudePercentage(BaseModel):
    total_high_occupancy_domestic: int
    over_1000m_altitude_diff: int
    percentage: float
    
class ConsecutiveHighOccRoute(BaseModel):
    first_date: date
    second_date: date
    airline: str | None
    destination: str | None = None
    origin: str | None = None
    
class TopRouteOut(BaseModel):
    origin_airport_id: int
    destination_airport_id: int
    origin: Optional[str] = None      
    destination: Optional[str] = None
    flights: int
    
class AirlineOccupancyOut(BaseModel):
    airline_id: int
    airline: Optional[str] = None
    flights: int
    tickets: int
    capacity: int
    occupancy: float 