from .news_articles import router as news_articles_router
from .videos import router as videos_router
from .system_settings import router as system_settings_router

__all__ = ["news_articles_router", "videos_router", "system_settings_router"]
