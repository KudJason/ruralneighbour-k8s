from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from datetime import date, datetime
from app.crud.news_article import news_article_crud
from app.crud.video import video_crud
from app.crud.system_setting import system_setting_crud
from app.schemas.news_article import (
    NewsArticleCreate,
    NewsArticleUpdate,
    NewsArticleResponse,
)
from app.schemas.video import VideoCreate, VideoUpdate, VideoResponse
from app.schemas.system_setting import (
    SystemSettingCreate,
    SystemSettingUpdate,
    SystemSettingResponse,
)
from app.core.config import settings


class ContentService:
    """Service for content management and delivery"""

    @staticmethod
    def create_news_article(
        db: Session, article_data: NewsArticleCreate
    ) -> NewsArticleResponse:
        """Create a new news article"""
        article = news_article_crud.create(db, article_data)
        return NewsArticleResponse.model_validate(article)

    @staticmethod
    def get_news_article(db: Session, article_id: str) -> Optional[NewsArticleResponse]:
        """Get a news article by ID"""
        article = news_article_crud.get(db, article_id)
        return NewsArticleResponse.model_validate(article) if article else None

    @staticmethod
    def get_active_news_articles(
        db: Session, skip: int = 0, limit: int = 100
    ) -> List[NewsArticleResponse]:
        """Get all active news articles for public consumption"""
        articles = news_article_crud.get_active_articles(db, skip, limit)
        return [NewsArticleResponse.model_validate(article) for article in articles]

    @staticmethod
    def get_active_news_articles_with_filter(
        db: Session, skip: int = 0, limit: int = 100, is_featured: Optional[bool] = None
    ) -> List[NewsArticleResponse]:
        """Get active news articles with optional is_featured filter"""
        articles = news_article_crud.get_active_articles_with_filter(
            db, skip, limit, is_featured
        )
        return [NewsArticleResponse.model_validate(article) for article in articles]

    @staticmethod
    def get_featured_news_articles(
        db: Session, skip: int = 0, limit: int = 10
    ) -> List[NewsArticleResponse]:
        """Get featured news articles for public consumption"""
        articles = news_article_crud.get_featured_articles(db, skip, limit)
        return [NewsArticleResponse.model_validate(article) for article in articles]

    @staticmethod
    def update_news_article(
        db: Session, article_id: str, article_data: NewsArticleUpdate
    ) -> Optional[NewsArticleResponse]:
        """Update a news article"""
        article = news_article_crud.update(db, article_id, article_data)
        return NewsArticleResponse.model_validate(article) if article else None

    @staticmethod
    def delete_news_article(db: Session, article_id: str) -> bool:
        """Delete a news article"""
        return news_article_crud.delete(db, article_id)

    @staticmethod
    def create_video(db: Session, video_data: VideoCreate) -> VideoResponse:
        """Create a new video"""
        video = video_crud.create(db, video_data)
        return VideoResponse.model_validate(video)

    @staticmethod
    def get_video(db: Session, video_id: str) -> Optional[VideoResponse]:
        """Get a video by ID"""
        video = video_crud.get(db, video_id)
        return VideoResponse.model_validate(video) if video else None

    @staticmethod
    def get_active_videos(
        db: Session, skip: int = 0, limit: int = 100
    ) -> List[VideoResponse]:
        """Get all active videos for public consumption"""
        videos = video_crud.get_active_videos(db, skip, limit)
        return [VideoResponse.model_validate(video) for video in videos]

    @staticmethod
    def get_featured_videos(
        db: Session, skip: int = 0, limit: int = 10
    ) -> List[VideoResponse]:
        """Get featured videos for public consumption"""
        videos = video_crud.get_featured_videos(db, skip, limit)
        return [VideoResponse.model_validate(video) for video in videos]

    @staticmethod
    def get_videos_by_type(
        db: Session, video_type: str, skip: int = 0, limit: int = 50
    ) -> List[VideoResponse]:
        """Get videos by type for public consumption"""
        videos = video_crud.get_videos_by_type(db, video_type, skip, limit)
        return [VideoResponse.model_validate(video) for video in videos]

    @staticmethod
    def update_video(
        db: Session, video_id: str, video_data: VideoUpdate
    ) -> Optional[VideoResponse]:
        """Update a video"""
        video = video_crud.update(db, video_id, video_data)
        return VideoResponse.model_validate(video) if video else None

    @staticmethod
    def delete_video(db: Session, video_id: str) -> bool:
        """Delete a video"""
        return video_crud.delete(db, video_id)

    @staticmethod
    def create_system_setting(
        db: Session, setting_data: SystemSettingCreate
    ) -> SystemSettingResponse:
        """Create a new system setting"""
        setting = system_setting_crud.create(db, setting_data)
        return SystemSettingResponse.model_validate(setting)

    @staticmethod
    def get_system_setting(
        db: Session, setting_id: str
    ) -> Optional[SystemSettingResponse]:
        """Get a system setting by ID"""
        setting = system_setting_crud.get(db, setting_id)
        return SystemSettingResponse.model_validate(setting) if setting else None

    @staticmethod
    def get_system_setting_by_key(
        db: Session, setting_key: str
    ) -> Optional[SystemSettingResponse]:
        """Get a system setting by key"""
        setting = system_setting_crud.get_by_key(db, setting_key)
        return SystemSettingResponse.model_validate(setting) if setting else None

    @staticmethod
    def get_all_system_settings(
        db: Session, skip: int = 0, limit: int = 100
    ) -> List[SystemSettingResponse]:
        """Get all system settings"""
        settings = system_setting_crud.get_all(db, skip, limit)
        return [SystemSettingResponse.model_validate(setting) for setting in settings]

    @staticmethod
    def update_system_setting(
        db: Session, setting_id: str, setting_data: SystemSettingUpdate
    ) -> Optional[SystemSettingResponse]:
        """Update a system setting"""
        setting = system_setting_crud.update(db, setting_id, setting_data)
        return SystemSettingResponse.model_validate(setting) if setting else None

    @staticmethod
    def update_system_setting_by_key(
        db: Session, setting_key: str, setting_data: SystemSettingUpdate
    ) -> Optional[SystemSettingResponse]:
        """Update a system setting by key"""
        setting = system_setting_crud.update_by_key(db, setting_key, setting_data)
        return SystemSettingResponse.model_validate(setting) if setting else None

    @staticmethod
    def delete_system_setting(db: Session, setting_id: str) -> bool:
        """Delete a system setting"""
        return system_setting_crud.delete(db, setting_id)

    @staticmethod
    def get_setting_value(db: Session, setting_key: str) -> Optional[str]:
        """Get setting value by key"""
        return system_setting_crud.get_setting_value(db, setting_key)
