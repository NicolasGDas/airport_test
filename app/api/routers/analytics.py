from __future__ import  annotations
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from datetime import date
from typing import Optional, List
from app.api.deps import get_session
from app.services import analytics as svc
from app.schemas.analytics import DomesticAltitudePercentage, ConsecutiveHighOccRoute


router = APIRouter(prefix="/analytics", tags=["analytics"])

@router.get("/average-occupancy")
def average_occupancy(start: Optional[date] = None, end: Optional[date] = None, db: Session = Depends(get_session)):
    return svc.average_occupancy(db, start=start, end=end)

@router.get(
    "/domestic-altitude-percentage",
    response_model=DomesticAltitudePercentage, 
)
def domestic_altitude_percentage(min_occupancy: float = Query(0.85, ge=0, le=1), db: Session = Depends(get_session)):
     return svc.domestic_altitude_percentage(db, min_occupancy=min_occupancy)

@router.get("/top-routes-by-country")
def top_routes_by_country(country: str, start: Optional[date] = None, end: Optional[date] = None, db: Session = Depends(get_session)):
    return svc.top_routes_by_country(db, country=country, start=start, end=end)


@router.get(
    "/consecutive-high-occupancy-routes",
    response_model=List[ConsecutiveHighOccRoute],
)
def consecutive_high_occupancy_routes(
    min_occupancy: float = Query(0.85, ge=0, le=1),
    start: Optional[date] = None,
    end: Optional[date] = None,
    db: Session = Depends(get_session),
):
    return svc.consecutive_high_occupancy_routes(
        db,
        min_occupancy=min_occupancy,
        start=start,
        end=end,
    )