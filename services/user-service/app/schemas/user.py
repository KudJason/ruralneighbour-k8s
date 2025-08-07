from pydantic import BaseModel
from typing import Optional, Literal
from datetime import datetime
import uuid

UserMode = Literal["NIN", "LAH"]


class UserBase(BaseModel):
    email: str
    full_name: Optional[str] = None
    default_mode: UserMode = "NIN"


class UserResponse(UserBase):
    user_id: uuid.UUID
    is_active: bool = True
    is_verified: bool = False
    created_at: datetime
    updated_at: datetime
    last_login: Optional[datetime] = None

    class Config:
        from_attributes = True
