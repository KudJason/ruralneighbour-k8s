from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Header
from sqlalchemy.orm import Session
from app.api.deps import get_db_session, require_admin_auth
from app.services.content_service import ContentService
from app.schemas.news_article import (
    NewsArticleCreate,
    NewsArticleUpdate,
    NewsArticleResponse,
)

router = APIRouter()


@router.post("/news/articles", response_model=NewsArticleResponse, tags=["admin"])
async def create_news_article(
    article_data: NewsArticleCreate,
    db: Session = Depends(get_db_session),
    authorization: Optional[str] = Header(None),
):
    """Create a new news article (Admin only)"""
    # Verify admin authentication
    require_admin_auth(authorization)

    article = ContentService.create_news_article(db, article_data)
    return article


@router.get("/news/articles", response_model=List[NewsArticleResponse], tags=["public"])
async def get_news_articles(
    skip: int = 0, limit: int = 100, db: Session = Depends(get_db_session)
):
    """Get all active news articles (Public endpoint)"""
    articles = ContentService.get_active_news_articles(db, skip, limit)
    return articles


@router.get(
    "/news/articles/featured", response_model=List[NewsArticleResponse], tags=["public"]
)
async def get_featured_news_articles(
    skip: int = 0, limit: int = 10, db: Session = Depends(get_db_session)
):
    """Get featured news articles (Public endpoint)"""
    articles = ContentService.get_featured_news_articles(db, skip, limit)
    return articles


@router.get(
    "/news/articles/{article_id}", response_model=NewsArticleResponse, tags=["public"]
)
async def get_news_article(article_id: str, db: Session = Depends(get_db_session)):
    """Get a specific news article by ID (Public endpoint)"""
    article = ContentService.get_news_article(db, article_id)
    if not article:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="News article not found"
        )
    return article


@router.put(
    "/news/articles/{article_id}", response_model=NewsArticleResponse, tags=["admin"]
)
async def update_news_article(
    article_id: str,
    article_data: NewsArticleUpdate,
    db: Session = Depends(get_db_session),
    authorization: Optional[str] = Header(None),
):
    """Update a news article (Admin only)"""
    # Verify admin authentication
    require_admin_auth(authorization)

    article = ContentService.update_news_article(db, article_id, article_data)
    if not article:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="News article not found"
        )
    return article


@router.delete("/news/articles/{article_id}", tags=["admin"])
async def delete_news_article(
    article_id: str,
    db: Session = Depends(get_db_session),
    authorization: Optional[str] = Header(None),
):
    """Delete a news article (Admin only)"""
    # Verify admin authentication
    require_admin_auth(authorization)

    success = ContentService.delete_news_article(db, article_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="News article not found"
        )
    return {"message": "News article deleted successfully"}
