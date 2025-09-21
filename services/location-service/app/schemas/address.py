from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, Field, validator
from uuid import UUID


class AddressCreate(BaseModel):
    user_id: UUID
    # Frontend may send `street`; map to `street_address`
    street: Optional[str] = Field(None, min_length=1, max_length=255)
    street_address: str = Field(..., min_length=1, max_length=255)
    city: str = Field(..., min_length=1, max_length=100)
    state: str = Field(..., min_length=2, max_length=50)
    postal_code: str = Field(..., min_length=5, max_length=20)
    country: str = Field(default="USA", max_length=100)
    latitude: float = Field(..., ge=-90, le=90)
    longitude: float = Field(..., ge=-180, le=180)
    # Alias support: is_default -> is_primary (define before is_primary)
    is_default: Optional[bool] = Field(None, description="Alias for is_primary")
    is_primary: bool = Field(default=False)
    address_type: str = Field(default="residential", max_length=50)

    @validator("is_primary", pre=True, always=True)
    def map_is_default_to_is_primary(cls, v, values):
        # If is_default is provided, use it to set is_primary
        if values.get("is_default") is not None:
            return bool(values["is_default"])
        return v

    @validator("street_address", pre=True, always=True)
    def map_street_to_street_address(cls, v, values):
        if v is None and values.get("street"):
            return values["street"]
        return v


class AddressUpdate(BaseModel):
    street: Optional[str] = Field(None, min_length=1, max_length=255)
    street_address: Optional[str] = Field(None, min_length=1, max_length=255)
    city: Optional[str] = Field(None, min_length=1, max_length=100)
    state: Optional[str] = Field(None, min_length=2, max_length=50)
    postal_code: Optional[str] = Field(None, min_length=5, max_length=20)
    country: Optional[str] = Field(None, max_length=100)
    latitude: Optional[float] = Field(None, ge=-90, le=90)
    longitude: Optional[float] = Field(None, ge=-180, le=180)
    # Alias first so validator sees it
    is_default: Optional[bool] = Field(None, description="Alias for is_primary")
    is_primary: Optional[bool] = None
    address_type: Optional[str] = Field(None, max_length=50)

    @validator("is_primary", pre=True, always=True)
    def map_update_is_default_to_is_primary(cls, v, values):
        if values.get("is_default") is not None:
            return bool(values["is_default"])
        return v

    @validator("street_address", pre=True, always=True)
    def map_update_street_to_street_address(cls, v, values):
        if v is None and values.get("street"):
            return values["street"]
        return v


class AddressResponse(BaseModel):
    address_id: UUID
    # Convenience id for frontend
    id: UUID = Field(..., description="Alias of address_id for frontend convenience")
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
    # Optional fields reserved for UI/extension
    label: Optional[str] = None
    extra: Optional[dict] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

    @validator("id", pre=True, always=True)
    def populate_id_from_address_id(cls, v, values):
        # When constructing from ORM, ensure id mirrors address_id
        if v is None and "address_id" in values:
            return values["address_id"]
        return v


class AddressListResponse(BaseModel):
    addresses: List[AddressResponse]
    total: int
    page: int
    size: int


