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


@router.get("/news/", response_model=List[NewsArticleResponse], tags=["public"])
async def list_news(
    skip: int = 0,
    limit: int = 100,
    is_featured: Optional[bool] = None,
    db: Session = Depends(get_db_session),
):
    articles = ContentService.get_active_news_articles_with_filter(
        db, skip, limit, is_featured
    )
    return articles


@router.get("/news/{article_id}", response_model=NewsArticleResponse, tags=["public"])
async def get_news(article_id: str, db: Session = Depends(get_db_session)):
    article = ContentService.get_news_article(db, article_id)
    if not article:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="News article not found"
        )
    return article


@router.post("/news/", response_model=NewsArticleResponse, tags=["admin"])
async def create_news(
    article_data: NewsArticleCreate,
    db: Session = Depends(get_db_session),
    authorization: Optional[str] = Header(None),
):
    require_admin_auth(authorization)
    article = ContentService.create_news_article(db, article_data)
    return article


@router.put("/news/{article_id}", response_model=NewsArticleResponse, tags=["admin"])
async def put_news(
    article_id: str,
    article_data: NewsArticleUpdate,
    db: Session = Depends(get_db_session),
    authorization: Optional[str] = Header(None),
):
    require_admin_auth(authorization)
    article = ContentService.update_news_article(db, article_id, article_data)
    if not article:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="News article not found"
        )
    return article


@router.patch("/news/{article_id}", response_model=NewsArticleResponse, tags=["admin"])
async def patch_news(
    article_id: str,
    article_data: NewsArticleUpdate,
    db: Session = Depends(get_db_session),
    authorization: Optional[str] = Header(None),
):
    require_admin_auth(authorization)
    article = ContentService.update_news_article(db, article_id, article_data)
    if not article:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="News article not found"
        )
    return article


@router.delete("/news/{article_id}", tags=["admin"])
async def delete_news(
    article_id: str,
    db: Session = Depends(get_db_session),
    authorization: Optional[str] = Header(None),
):
    require_admin_auth(authorization)
    success = ContentService.delete_news_article(db, article_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="News article not found"
        )
    return {"message": "News article deleted successfully"}


