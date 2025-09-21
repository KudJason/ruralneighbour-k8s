from pydantic import BaseModel, Field, validator
from typing import Optional, Literal, List, Dict, Any
from decimal import Decimal
from datetime import datetime
import uuid
import sys
import os
import json

# 添加共享schema路径
sys.path.append(os.path.join(os.path.dirname(__file__), '../../../shared'))
try:
    from schemas.common import BaseProfileFields, BaseProviderFields
except ImportError:
    # 如果共享schema不可用，定义基础字段
    BaseProfileFields = None
    BaseProviderFields = None

UserMode = Literal["NIN", "LAH"]


class UserProfileBase(BaseModel):
    bio: Optional[str] = None
    phone_number: Optional[str] = Field(alias="phone", default=None)
    profile_picture_url: Optional[str] = Field(alias="avatarUrl", default=None)

    class Config:
        populate_by_name = True  # 支持两种字段名


class UserProfileCreate(UserProfileBase):
    user_id: uuid.UUID = Field(alias="userId")


class UserProfileUpdate(UserProfileBase):
    default_mode: Optional[UserMode] = Field(alias="defaultMode", default=None)

    class Config:
        populate_by_name = True


class UserProfileResponse(UserProfileBase):
    profile_id: uuid.UUID = Field(alias="profileId")
    user_id: uuid.UUID = Field(alias="userId")
    average_rating: Decimal = Field(alias="averageRating", default=Decimal("0.00"))
    total_ratings: int = Field(alias="totalRatings", default=0)
    default_mode: UserMode = Field(alias="defaultMode", default="NIN")
    created_at: datetime = Field(alias="createdAt")
    updated_at: datetime = Field(alias="updatedAt")

    class Config:
        from_attributes = True
        by_alias = True  # 响应时使用别名


class ProviderProfileBase(BaseModel):
    service_radius_miles: Optional[Decimal] = Field(
        alias="serviceRadiusMiles", default=Decimal("2.0"), ge=0.1, le=50.0
    )
    vehicle_description: Optional[str] = Field(alias="description", default=None)
    services_offered: Optional[str] = Field(alias="services", default=None)  # JSON string
    hourly_rate: Optional[Decimal] = Field(alias="hourlyRate", default=None, ge=0)
    availability_schedule: Optional[str] = Field(alias="availability", default=None)  # JSON string
    is_available: Optional[str] = Field(alias="isAvailable", default="true")

    class Config:
        populate_by_name = True  # 支持两种字段名


class ProviderProfileCreate(ProviderProfileBase):
    user_id: uuid.UUID = Field(alias="userId")

    class Config:
        populate_by_name = True


class ProviderProfileUpdate(ProviderProfileBase):
    def __init__(self, **data):
        # 处理JSON序列化
        if 'services' in data and isinstance(data['services'], (list, dict)):
            data['services_offered'] = json.dumps(data['services'], ensure_ascii=False)
            del data['services']
        
        if 'availability' in data and isinstance(data['availability'], dict):
            data['availability_schedule'] = json.dumps(data['availability'], ensure_ascii=False)
            del data['availability']
        
        super().__init__(**data)


class ProviderProfileResponse(ProviderProfileBase):
    id: uuid.UUID = Field(alias="providerId")
    user_id: uuid.UUID = Field(alias="userId")
    created_at: datetime = Field(alias="createdAt")
    updated_at: datetime = Field(alias="updatedAt")

    class Config:
        from_attributes = True
        by_alias = True  # 响应时使用别名


class ModeSwitch(BaseModel):
    default_mode: UserMode = Field(alias="defaultMode")

    class Config:
        populate_by_name = True
