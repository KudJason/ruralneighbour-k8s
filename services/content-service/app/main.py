from fastapi import FastAPI
from app.api.v1.endpoints import news_articles, videos, system_settings
from app.core.config import settings
from app.db.base import engine, Base
import os

# Import models after creating Base to avoid circular imports
import app.db.init_db

# Create tables only if not in testing environment
if os.getenv("TESTING") != "true":
    Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Content Service",
    description="Service for managing content including news articles, videos, and system settings",
    version="1.0.0",
)

# Include routers
app.include_router(news_articles.router, prefix="/api/v1", tags=["news_articles"])
app.include_router(videos.router, prefix="/api/v1", tags=["videos"])
app.include_router(system_settings.router, prefix="/api/v1", tags=["system_settings"])


@app.get("/")
async def root():
    return {"message": "Content Service is running"}


@app.get("/health")
async def health():
    return {"status": "healthy"}


@app.get("/info")
async def info():
    """Get service information and configuration"""
    return {
        "service": "Content Service",
        "version": "1.0.0",
        "features": [
            "News Articles Management (CRUD)",
            "Video Content Management (CRUD)",
            "System Settings Management",
            "Content Retention Policy (1 year)",
            "Public Content Delivery",
            "Admin-only Content Management",
        ],
        "configuration": {
            "content_retention_days": settings.CONTENT_RETENTION_DAYS,
        },
    }
