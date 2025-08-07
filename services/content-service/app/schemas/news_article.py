from datetime import date, datetime
from typing import Optional
from pydantic import BaseModel, UUID4, ConfigDict


class NewsArticleBase(BaseModel):
    title: str
    content: str
    author_id: Optional[UUID4] = None
    image_url: Optional[str] = None
    is_featured: bool = False
    is_active: bool = True
    publish_date: Optional[date] = None
    expiry_date: Optional[date] = None


class NewsArticleCreate(NewsArticleBase):
    pass


class NewsArticleUpdate(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None
    author_id: Optional[UUID4] = None
    image_url: Optional[str] = None
    is_featured: Optional[bool] = None
    is_active: Optional[bool] = None
    publish_date: Optional[date] = None
    expiry_date: Optional[date] = None


class NewsArticleResponse(NewsArticleBase):
    article_id: UUID4
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
