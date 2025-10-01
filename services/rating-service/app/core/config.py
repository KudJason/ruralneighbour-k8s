import os
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    # Database - 优先使用环境变量
    database_url: str = os.getenv("DATABASE_URL", "postgresql://user:password@localhost:5432/rating_service")
    
    # Redis
    redis_url: str = "redis://localhost:6379"
    
    # Service URLs
    user_service_url: str = "http://user-service:8000"
    request_service_url: str = "http://request-service:8000"
    
    # Security
    secret_key: str = "your-secret-key-here"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    
    class Config:
        env_file = ".env"


settings = Settings()






