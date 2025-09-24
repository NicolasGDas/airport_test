from pydantic import BaseModel
from datetime import date
class AverageOccupancyItem(BaseModel):
    airline: str | None
    avg_occupancy: float | None

class DomesticAltitudePercentage(BaseModel):
    total_high_occupancy_domestic: int
    over_1000m_altitude_diff: int
    percentage: float
    
class ConsecutiveHighOccRoute(BaseModel):
    airline: str
    origin: str
    destination: str
    first_date: date
    second_date: date
    
    
    