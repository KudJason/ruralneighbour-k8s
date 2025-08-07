from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    # Database
    database_url: str = "postgresql://devuser:devpass@postgres:5432/notificationdb"

    # JWT Settings
    secret_key: str = "your-secret-key-here"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30

    # API Settings
    api_v1_str: str = "/api/v1"
    project_name: str = "Notification Service"

    # External Service URLs
    auth_service_url: str = "http://auth-service:8000"
    user_service_url: str = "http://user-service:8000"
    service_request_service_url: str = "http://service-request-service:8000"
    payment_service_url: str = "http://payment-service:8000"
    safety_service_url: str = "http://safety-service:8000"

    # Email Settings (SendGrid)
    sendgrid_api_key: Optional[str] = None
    sendgrid_from_email: str = "noreply@yourplatform.com"

    # Push Notification Settings (Firebase)
    firebase_credentials_path: Optional[str] = None

    # Redis Settings (for Celery)
    redis_url: str = "redis://redis:6379/0"

    # Celery Settings
    celery_broker_url: str = "redis://redis:6379/0"
    celery_result_backend: str = "redis://redis:6379/0"

    # Notification Settings
    max_retry_attempts: int = 3
    notification_retention_days: int = 90  # Keep notifications for 90 days

    class Config:
        env_file = ".env"


settings = Settings()
