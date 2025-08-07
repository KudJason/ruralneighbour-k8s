from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, Field, validator
from uuid import UUID


class AddressCreate(BaseModel):
    user_id: UUID
    street_address: str = Field(..., min_length=1, max_length=255)
    city: str = Field(..., min_length=1, max_length=100)
    state: str = Field(..., min_length=2, max_length=50)
    postal_code: str = Field(..., min_length=5, max_length=20)
    country: str = Field(default="USA", max_length=100)
    latitude: float = Field(..., ge=-90, le=90)
    longitude: float = Field(..., ge=-180, le=180)
    is_primary: bool = Field(default=False)
    address_type: str = Field(default="residential", max_length=50)


class AddressUpdate(BaseModel):
    street_address: Optional[str] = Field(None, min_length=1, max_length=255)
    city: Optional[str] = Field(None, min_length=1, max_length=100)
    state: Optional[str] = Field(None, min_length=2, max_length=50)
    postal_code: Optional[str] = Field(None, min_length=5, max_length=20)
    country: Optional[str] = Field(None, max_length=100)
    latitude: Optional[float] = Field(None, ge=-90, le=90)
    longitude: Optional[float] = Field(None, ge=-180, le=180)
    is_primary: Optional[bool] = None
    address_type: Optional[str] = Field(None, max_length=50)


class AddressResponse(BaseModel):
    address_id: UUID
    user_id: UUID
    street_address: str
    city: str
    state: str
    postal_code: str
    country: str
    latitude: float
    longitude: float
    is_within_service_area: bool
    is_primary: bool
    address_type: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class AddressListResponse(BaseModel):
    addresses: List[AddressResponse]
    total: int
    page: int
    size: int


