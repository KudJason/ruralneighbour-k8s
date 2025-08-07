from typing import List, Dict, Any
from sqlalchemy.orm import Session
from datetime import date, datetime, timedelta
from app.crud.news_article import news_article_crud
from app.crud.video import video_crud
from app.core.config import settings


class RetentionService:
    """Service for handling content retention policy"""

    @staticmethod
    def get_expired_content(db: Session) -> Dict[str, List]:
        """Get all expired content for retention policy"""
        expired_articles = news_article_crud.get_expired_articles(db)
        expired_videos = video_crud.get_expired_videos(db)

        return {"expired_articles": expired_articles, "expired_videos": expired_videos}

    @staticmethod
    def mark_expired_content_inactive(db: Session) -> Dict[str, int]:
        """Mark expired content as inactive instead of deleting"""
        expired_content = RetentionService.get_expired_content(db)

        articles_marked = 0
        videos_marked = 0

        # Mark expired articles as inactive
        for article in expired_content["expired_articles"]:
            if news_article_crud.mark_as_inactive(db, str(article.article_id)):
                articles_marked += 1

        # Mark expired videos as inactive
        for video in expired_content["expired_videos"]:
            if video_crud.mark_as_inactive(db, str(video.video_id)):
                videos_marked += 1

        return {
            "articles_marked_inactive": articles_marked,
            "videos_marked_inactive": videos_marked,
            "total_content_processed": articles_marked + videos_marked,
        }

    @staticmethod
    def set_expiry_dates_for_new_content(
        db: Session, content_type: str, content_id: str
    ) -> bool:
        """Set expiry date for new content based on retention policy"""
        retention_days = settings.CONTENT_RETENTION_DAYS
        expiry_date = date.today() + timedelta(days=retention_days)

        if content_type == "article":
            article = news_article_crud.get(db, content_id)
            if article:
                article.expiry_date = expiry_date
                db.commit()
                return True
        elif content_type == "video":
            video = video_crud.get(db, content_id)
            if video:
                video.expiry_date = expiry_date
                db.commit()
                return True

        return False

    @staticmethod
    def get_retention_statistics(db: Session) -> Dict[str, Any]:
        """Get statistics about content retention"""
        expired_content = RetentionService.get_expired_content(db)

        return {
            "retention_policy_days": settings.CONTENT_RETENTION_DAYS,
            "expired_articles_count": len(expired_content["expired_articles"]),
            "expired_videos_count": len(expired_content["expired_videos"]),
            "total_expired_content": len(expired_content["expired_articles"])
            + len(expired_content["expired_videos"]),
            "last_check": datetime.utcnow().isoformat(),
        }
