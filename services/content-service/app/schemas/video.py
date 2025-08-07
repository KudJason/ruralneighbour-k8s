from datetime import date, datetime
from typing import Optional
from pydantic import BaseModel, UUID4, ConfigDict
from enum import Enum


class VideoType(str, Enum):
    INFORMATIONAL = "informational"
    TUTORIAL = "tutorial"
    PROMOTIONAL = "promotional"
    COMMUNITY = "community"


class VideoBase(BaseModel):
    title: str
    description: Optional[str] = None
    video_url: str
    thumbnail_url: Optional[str] = None
    video_type: Optional[VideoType] = None
    is_featured: bool = False
    is_active: bool = True
    publish_date: Optional[date] = None
    expiry_date: Optional[date] = None


class VideoCreate(VideoBase):
    pass


class VideoUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    video_url: Optional[str] = None
    thumbnail_url: Optional[str] = None
    video_type: Optional[VideoType] = None
    is_featured: Optional[bool] = None
    is_active: Optional[bool] = None
    publish_date: Optional[date] = None
    expiry_date: Optional[date] = None


class VideoResponse(VideoBase):
    video_id: UUID4
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
