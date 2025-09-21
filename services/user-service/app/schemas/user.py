from pydantic import BaseModel, Field
from typing import Optional, Literal
from datetime import datetime
import uuid
import sys
import os

# 添加共享schema路径
sys.path.append(os.path.join(os.path.dirname(__file__), '../../../shared'))
try:
    from schemas.common import BaseUserFields, AutoConversionConfig
except ImportError:
    # 如果共享schema不可用，定义基础字段
    BaseUserFields = None
    AutoConversionConfig = None

UserMode = Literal["NIN", "LAH"]


class UserBase(BaseModel):
    email: str
    full_name: Optional[str] = None
    default_mode: UserMode = "NIN"


class UserResponse(UserBase):
    user_id: uuid.UUID = Field(alias="userId")
    is_active: bool = Field(alias="isActive", default=True)
    is_verified: bool = Field(alias="isVerified", default=False)
    created_at: datetime = Field(alias="createdAt")
    updated_at: datetime = Field(alias="updatedAt")
    last_login: Optional[datetime] = Field(alias="lastLogin", default=None)

    class Config:
        from_attributes = True
        by_alias = True  # 响应时使用别名


class UserUpdate(BaseModel):
    full_name: Optional[str] = Field(alias="fullName", default=None)
    phone_number: Optional[str] = Field(alias="phone", default=None)
    default_mode: Optional[UserMode] = Field(alias="defaultMode", default=None)
    is_active: Optional[bool] = Field(alias="isActive", default=None)

    class Config:
        populate_by_name = True  # 支持两种字段名
