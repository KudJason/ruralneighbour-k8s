from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field
from uuid import UUID


class SavedLocationCreate(BaseModel):
    address: str = Field(..., min_length=1)
    latitude: float
    longitude: float
    name: Optional[str] = None  # default to address if not provided


class SavedLocationResponse(BaseModel):
    location_id: UUID
    user_id: UUID
    name: str
    address: str
    latitude: float
    longitude: float
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class SavedLocationListResponse(BaseModel):
    locations: List[SavedLocationResponse]
    total: int







