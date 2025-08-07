from pydantic import BaseModel, Field, validator
from typing import Optional, Literal
from decimal import Decimal
from datetime import datetime
import uuid

UserMode = Literal["NIN", "LAH"]


class UserProfileBase(BaseModel):
    bio: Optional[str] = None
    phone_number: Optional[str] = None
    profile_picture_url: Optional[str] = None


class UserProfileCreate(UserProfileBase):
    user_id: uuid.UUID


class UserProfileUpdate(UserProfileBase):
    default_mode: Optional[UserMode] = None


class UserProfileResponse(UserProfileBase):
    profile_id: uuid.UUID
    user_id: uuid.UUID
    average_rating: Decimal = Field(default=Decimal("0.00"))
    total_ratings: int = 0
    default_mode: UserMode = "NIN"
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ProviderProfileBase(BaseModel):
    service_radius_miles: Optional[Decimal] = Field(
        default=Decimal("2.0"), ge=0.1, le=50.0
    )
    vehicle_description: Optional[str] = None
    services_offered: Optional[str] = None  # JSON string
    hourly_rate: Optional[Decimal] = Field(default=None, ge=0)
    availability_schedule: Optional[str] = None  # JSON string
    is_available: Optional[str] = "true"


class ProviderProfileCreate(ProviderProfileBase):
    user_id: uuid.UUID


class ProviderProfileUpdate(ProviderProfileBase):
    pass


class ProviderProfileResponse(ProviderProfileBase):
    id: uuid.UUID
    user_id: uuid.UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ModeSwitch(BaseModel):
    default_mode: UserMode
