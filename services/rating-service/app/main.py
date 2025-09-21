from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .api.v1.endpoints import ratings
from .core.config import settings

app = FastAPI(
    title="Rating Service",
    version="1.0.0",
    description="评分服务微服务，支持用户对服务提供者进行评分和评论"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 在生产环境中应该限制具体域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(ratings.router, prefix="/api/v1/ratings", tags=["ratings"])


@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "rating-service"}


@app.get("/")
async def root():
    return {"message": "Rating Service is running"}


@app.get("/info")
async def info():
    return {
        "service": "Rating Service",
        "version": "1.0.0",
        "features": [
            "Rating CRUD operations",
            "Rating summary statistics",
            "Rating permission validation",
            "Frontend field mapping compatibility"
        ],
        "configuration": {
            "database_url": settings.database_url,
            "user_service_url": settings.user_service_url,
            "request_service_url": settings.request_service_url
        },
    }






