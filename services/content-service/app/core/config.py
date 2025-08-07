import os
from typing import Optional

# Database configuration
DATABASE_URL = os.getenv(
    "DATABASE_URL", "postgresql://devuser:devpass@postgres:5432/contentdb"
)

# Content retention policy (1 year in days)
CONTENT_RETENTION_DAYS = int(os.getenv("CONTENT_RETENTION_DAYS", "365"))

# JWT configuration
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-change-in-production")
ALGORITHM = os.getenv("ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))

# API configuration
API_V1_STR = "/api/v1"
PROJECT_NAME = "Content Service"

# Other service URLs
AUTH_SERVICE_URL = os.getenv("AUTH_SERVICE_URL", "http://localhost:8001")
USER_SERVICE_URL = os.getenv("USER_SERVICE_URL", "http://localhost:8002")


class Settings:
    DATABASE_URL: str = DATABASE_URL
    API_V1_STR: str = API_V1_STR
    PROJECT_NAME: str = PROJECT_NAME
    SECRET_KEY: str = SECRET_KEY
    ALGORITHM: str = ALGORITHM
    ACCESS_TOKEN_EXPIRE_MINUTES: int = ACCESS_TOKEN_EXPIRE_MINUTES
    AUTH_SERVICE_URL: str = AUTH_SERVICE_URL
    USER_SERVICE_URL: str = USER_SERVICE_URL
    CONTENT_RETENTION_DAYS: int = CONTENT_RETENTION_DAYS


settings = Settings()
