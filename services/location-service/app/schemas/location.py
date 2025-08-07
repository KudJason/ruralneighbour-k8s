from typing import Optional
from pydantic import BaseModel, Field


class LocationValidationRequest(BaseModel):
    latitude: float = Field(..., ge=-90, le=90, description="Latitude coordinate")
    longitude: float = Field(..., ge=-180, le=180, description="Longitude coordinate")
    address: Optional[str] = Field(None, description="Optional address for context")


class LocationValidationResponse(BaseModel):
    is_valid: bool
    latitude: float
    longitude: float
    distance_to_restricted_area: Optional[float] = None
    nearest_restricted_city: Optional[str] = None
    population_of_nearest_city: Optional[int] = None
    message: str


class DistanceCalculationRequest(BaseModel):
    lat1: float = Field(..., ge=-90, le=90, description="Latitude of first point")
    lon1: float = Field(..., ge=-180, le=180, description="Longitude of first point")
    lat2: float = Field(..., ge=-90, le=90, description="Latitude of second point")
    lon2: float = Field(..., ge=-180, le=180, description="Longitude of second point")
    unit: str = Field(
        default="miles", description="Distance unit: miles, kilometers, meters"
    )


class DistanceCalculationResponse(BaseModel):
    distance: float
    unit: str
    lat1: float
    lon1: float
    lat2: float
    lon2: float
    calculation_method: str = "Haversine"


