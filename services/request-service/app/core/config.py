import os

# Database configuration
DATABASE_URL = os.getenv(
    "DATABASE_URL", "postgresql://devuser:devpass@postgres:5432/devdb"
)

# Redis stream configuration
REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379/0")

# Service configuration constants
MAX_REQUESTS_PER_USER = int(os.getenv("MAX_REQUESTS_PER_USER", "5"))
SERVICE_RADIUS_MILES = float(os.getenv("SERVICE_RADIUS_MILES", "2.0"))
REQUEST_EXPIRY_HOURS = int(os.getenv("REQUEST_EXPIRY_HOURS", "24"))

# JWT configuration
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-change-in-production")
ALGORITHM = os.getenv("ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))

# API configuration
API_V1_STR = "/api/v1"
PROJECT_NAME = "Request Service"

# Other service URLs
AUTH_SERVICE_URL = os.getenv("AUTH_SERVICE_URL", "http://localhost:8001")
USER_SERVICE_URL = os.getenv("USER_SERVICE_URL", "http://localhost:8002")
PAYMENT_SERVICE_URL = os.getenv("PAYMENT_SERVICE_URL", "http://localhost:8005")


class Settings:
    DATABASE_URL: str = DATABASE_URL
    REDIS_URL: str = REDIS_URL
    API_V1_STR: str = API_V1_STR
    PROJECT_NAME: str = PROJECT_NAME
    SECRET_KEY: str = SECRET_KEY
    ALGORITHM: str = ALGORITHM
    ACCESS_TOKEN_EXPIRE_MINUTES: int = ACCESS_TOKEN_EXPIRE_MINUTES
    AUTH_SERVICE_URL: str = AUTH_SERVICE_URL
    USER_SERVICE_URL: str = USER_SERVICE_URL
    PAYMENT_SERVICE_URL: str = PAYMENT_SERVICE_URL
    MAX_REQUESTS_PER_USER: int = MAX_REQUESTS_PER_USER
    SERVICE_RADIUS_MILES: float = SERVICE_RADIUS_MILES
    REQUEST_EXPIRY_HOURS: int = REQUEST_EXPIRY_HOURS


settings = Settings()

# For backward compatibility - some tests expect engine to be importable
try:
    from app.db.base import engine
except ImportError:
    engine = None
