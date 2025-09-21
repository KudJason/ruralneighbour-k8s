"""
统一字段命名Schema库

提供标准化的字段命名和转换功能，支持前端camelCase和后端snake_case的自动转换。
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime


class BaseUserFields(BaseModel):
    """用户基础字段 - 支持字段别名"""
    full_name: str = Field(alias="fullName")
    phone_number: str = Field(alias="phone")
    
    class Config:
        populate_by_name = True  # 支持两种字段名


class BaseProfileFields(BaseModel):
    """资料基础字段 - 支持字段别名"""
    avatar_url: str = Field(alias="avatarUrl")
    bio: Optional[str] = None
    phone_number: str = Field(alias="phone")
    
    class Config:
        populate_by_name = True


class BaseProviderFields(BaseModel):
    """服务商基础字段 - 支持字段别名"""
    services: List[str] = Field(alias="services")
    availability: Dict[str, Any] = Field(alias="availability")
    description: str = Field(alias="description")
    
    class Config:
        populate_by_name = True


class BaseAddressFields(BaseModel):
    """地址基础字段 - 支持字段别名"""
    is_primary: bool = Field(alias="isDefault")
    label: Optional[str] = None
    extra: Optional[Dict[str, Any]] = None
    
    class Config:
        populate_by_name = True


class BaseRatingFields(BaseModel):
    """评分基础字段 - 支持字段别名"""
    rating_score: int = Field(alias="rating")
    category: str = Field(alias="category")
    
    class Config:
        populate_by_name = True


# 请求Schema - 使用camelCase别名
class UserUpdateRequest(BaseUserFields):
    """用户更新请求Schema"""
    pass


class ProfileUpdateRequest(BaseProfileFields):
    """资料更新请求Schema"""
    pass


class ProviderUpdateRequest(BaseProviderFields):
    """服务商更新请求Schema"""
    pass


class AddressUpdateRequest(BaseAddressFields):
    """地址更新请求Schema"""
    pass


class RatingCreateRequest(BaseRatingFields):
    """评分创建请求Schema"""
    pass


# 响应Schema - 使用camelCase别名
class UserResponse(BaseUserFields):
    """用户响应Schema"""
    user_id: str = Field(alias="userId")
    email: str
    created_at: datetime = Field(alias="createdAt")
    updated_at: datetime = Field(alias="updatedAt")
    
    class Config:
        by_alias = True  # 响应时使用别名


class ProfileResponse(BaseProfileFields):
    """资料响应Schema"""
    profile_id: str = Field(alias="profileId")
    user_id: str = Field(alias="userId")
    created_at: datetime = Field(alias="createdAt")
    updated_at: datetime = Field(alias="updatedAt")
    
    class Config:
        by_alias = True


class ProviderResponse(BaseProviderFields):
    """服务商响应Schema"""
    provider_id: str = Field(alias="providerId")
    user_id: str = Field(alias="userId")
    service_radius_miles: float = Field(alias="serviceRadiusMiles")
    hourly_rate: float = Field(alias="hourlyRate")
    is_available: bool = Field(alias="isAvailable")
    created_at: datetime = Field(alias="createdAt")
    updated_at: datetime = Field(alias="updatedAt")
    
    class Config:
        by_alias = True


class AddressResponse(BaseAddressFields):
    """地址响应Schema"""
    address_id: str = Field(alias="id")
    user_id: str = Field(alias="userId")
    street: str
    city: str
    state: str
    postal_code: str = Field(alias="postalCode")
    country: str
    latitude: float
    longitude: float
    created_at: datetime = Field(alias="createdAt")
    updated_at: datetime = Field(alias="updatedAt")
    
    class Config:
        by_alias = True


class RatingResponse(BaseRatingFields):
    """评分响应Schema"""
    rating_id: str = Field(alias="ratingId")
    rater_id: str = Field(alias="raterId")
    ratee_id: str = Field(alias="rateeId")
    comment: Optional[str] = None
    created_at: datetime = Field(alias="createdAt")
    updated_at: datetime = Field(alias="updatedAt")
    
    class Config:
        by_alias = True


# 字段转换工具函数
def to_camel_case(snake_str: str) -> str:
    """将snake_case转换为camelCase"""
    components = snake_str.split('_')
    return components[0] + ''.join(x.capitalize() for x in components[1:])


def to_snake_case(camel_str: str) -> str:
    """将camelCase转换为snake_case"""
    import re
    s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', camel_str)
    return re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1).lower()


# 自动字段转换配置
class AutoConversionConfig:
    """自动字段转换配置"""
    
    @staticmethod
    def get_request_model(model_class):
        """获取请求模型，自动添加camelCase别名"""
        class AutoRequestModel(model_class):
            class Config:
                alias_generator = to_camel_case
                populate_by_name = True
        
        return AutoRequestModel
    
    @staticmethod
    def get_response_model(model_class):
        """获取响应模型，自动添加camelCase别名"""
        class AutoResponseModel(model_class):
            class Config:
                alias_generator = to_camel_case
                by_alias = True
        
        return AutoResponseModel


# 字段映射配置
FIELD_MAPPINGS = {
    # 用户相关
    "fullName": "full_name",
    "phone": "phone_number",
    "avatarUrl": "profile_picture_url",
    "profilePhotoUrl": "profile_picture_url",
    "profilePictureUrl": "profile_picture_url",
    
    # 服务商相关
    "services": "services_offered",
    "availability": "availability_schedule",
    "description": "vehicle_description",
    "serviceRadiusMiles": "service_radius_miles",
    "hourlyRate": "hourly_rate",
    "isAvailable": "is_available",
    
    # 地址相关
    "isDefault": "is_primary",
    "postalCode": "postal_code",
    
    # 评分相关
    "rating": "rating_score",
    "ratingId": "rating_id",
    "raterId": "rater_id",
    "rateeId": "ratee_id",
    
    # 通用
    "userId": "user_id",
    "createdAt": "created_at",
    "updatedAt": "updated_at",
    "profileId": "profile_id",
    "providerId": "provider_id",
    "addressId": "address_id"
}


def map_fields_to_backend(data: Dict[str, Any]) -> Dict[str, Any]:
    """将前端字段映射到后端字段"""
    mapped = {}
    for key, value in data.items():
        backend_key = FIELD_MAPPINGS.get(key, key)
        mapped[backend_key] = value
    return mapped


def map_fields_to_frontend(data: Dict[str, Any]) -> Dict[str, Any]:
    """将后端字段映射到前端字段"""
    mapped = {}
    reverse_mapping = {v: k for k, v in FIELD_MAPPINGS.items()}
    for key, value in data.items():
        frontend_key = reverse_mapping.get(key, key)
        mapped[frontend_key] = value
    return mapped
