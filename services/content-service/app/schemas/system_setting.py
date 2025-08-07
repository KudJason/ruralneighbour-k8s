from datetime import datetime
from typing import Optional
from pydantic import BaseModel, UUID4, ConfigDict


class SystemSettingBase(BaseModel):
    setting_key: str
    setting_value: Optional[str] = None
    setting_type: Optional[str] = None
    description: Optional[str] = None


class SystemSettingCreate(SystemSettingBase):
    pass


class SystemSettingUpdate(BaseModel):
    setting_value: Optional[str] = None
    setting_type: Optional[str] = None
    description: Optional[str] = None


class SystemSettingResponse(SystemSettingBase):
    setting_id: UUID4
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
