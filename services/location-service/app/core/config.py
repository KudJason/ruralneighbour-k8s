import os
from typing import Optional

# Database configuration
def get_database_url():
    """構建數據庫 URL 從環境變量"""
    db_user = os.getenv("POSTGRES_USER", "devuser")
    db_password = os.getenv("POSTGRES_PASSWORD", "devpass")
    db_host = os.getenv("POSTGRES_HOST", "postgres")
    db_port = os.getenv("POSTGRES_PORT", "5432")
    db_name = os.getenv("POSTGRES_DB", "locationdb")
    
    return f"postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"

DATABASE_URL = get_database_url()

# Service configuration constants
RESTRICTED_CITY_POPULATION_THRESHOLD = int(
    os.getenv("RESTRICTED_CITY_POPULATION_THRESHOLD", "50000")
)
RESTRICTED_AREA_RADIUS_MILES = float(os.getenv("RESTRICTED_AREA_RADIUS_MILES", "2.0"))
MAX_QUERY_TIME_MS = int(os.getenv("MAX_QUERY_TIME_MS", "200"))

# JWT configuration
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-change-in-production")
ALGORITHM = os.getenv("ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))

# API configuration
API_V1_STR = "/api/v1"
PROJECT_NAME = "Location Service"

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
    RESTRICTED_CITY_POPULATION_THRESHOLD: int = RESTRICTED_CITY_POPULATION_THRESHOLD
    RESTRICTED_AREA_RADIUS_MILES: float = RESTRICTED_AREA_RADIUS_MILES
    MAX_QUERY_TIME_MS: int = MAX_QUERY_TIME_MS


settings = Settings()
