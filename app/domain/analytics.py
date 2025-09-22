from pydantic import BaseModel

class AverageOccupancyItem(BaseModel):
    airline: str | None
    avg_occupancy: float | None

class DomesticAltitudePercentage(BaseModel):
    total_high_occupancy_domestic: int
    over_1000m_altitude_diff: int
    percentage: float
