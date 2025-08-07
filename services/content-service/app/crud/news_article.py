from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from datetime import date, datetime
from app.models.news_article import NewsArticle
from app.schemas.news_article import NewsArticleCreate, NewsArticleUpdate


class NewsArticleCRUD:
    def create(self, db: Session, obj_in: NewsArticleCreate) -> NewsArticle:
        """Create a new news article"""
        db_obj = NewsArticle(**obj_in.model_dump())
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def get(self, db: Session, article_id: str) -> Optional[NewsArticle]:
        """Get a news article by ID"""
        return (
            db.query(NewsArticle).filter(NewsArticle.article_id == article_id).first()
        )

    def get_active_articles(
        self, db: Session, skip: int = 0, limit: int = 100
    ) -> List[NewsArticle]:
        """Get all active news articles"""
        return (
            db.query(NewsArticle)
            .filter(NewsArticle.is_active == True)
            .offset(skip)
            .limit(limit)
            .all()
        )

    def get_featured_articles(
        self, db: Session, skip: int = 0, limit: int = 10
    ) -> List[NewsArticle]:
        """Get featured active news articles"""
        return (
            db.query(NewsArticle)
            .filter(
                and_(NewsArticle.is_active == True, NewsArticle.is_featured == True)
            )
            .offset(skip)
            .limit(limit)
            .all()
        )

    def update(
        self, db: Session, article_id: str, obj_in: NewsArticleUpdate
    ) -> Optional[NewsArticle]:
        """Update a news article"""
        db_obj = self.get(db, article_id)
        if not db_obj:
            return None

        update_data = obj_in.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_obj, field, value)

        db.commit()
        db.refresh(db_obj)
        return db_obj

    def delete(self, db: Session, article_id: str) -> bool:
        """Delete a news article"""
        db_obj = self.get(db, article_id)
        if not db_obj:
            return False

        db.delete(db_obj)
        db.commit()
        return True

    def get_expired_articles(self, db: Session) -> List[NewsArticle]:
        """Get articles that have expired (for retention policy)"""
        today = date.today()
        return (
            db.query(NewsArticle)
            .filter(
                and_(
                    NewsArticle.expiry_date.isnot(None), NewsArticle.expiry_date < today
                )
            )
            .all()
        )

    def mark_as_inactive(self, db: Session, article_id: str) -> bool:
        """Mark an article as inactive instead of deleting"""
        db_obj = self.get(db, article_id)
        if not db_obj:
            return False

        db_obj.is_active = False
        db.commit()
        return True


news_article_crud = NewsArticleCRUD()
