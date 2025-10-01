import os

from pydantic_settings import BaseSettings


def get_database_url():
    """構建數據庫 URL 從環境變量"""
    # 优先使用 DATABASE_URL 环境变量
    database_url = os.getenv("DATABASE_URL")
    if database_url:
        return database_url
    
    # 如果没有 DATABASE_URL，则从分离的环境变量构建
    db_user = os.getenv("POSTGRES_USER", "user")
    db_password = os.getenv("POSTGRES_PASSWORD", "password")
    db_host = os.getenv("POSTGRES_HOST", "localhost")
    db_port = os.getenv("POSTGRES_PORT", "5432")
    db_name = os.getenv("POSTGRES_DB", "dbname")

    return f"postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"


class Settings(BaseSettings):
    # Database
    database_url: str = get_database_url()

    # Redis for event streaming
    redis_url: str = "redis://localhost:6379/0"

    # Payment Provider Settings
    stripe_secret_key: str = os.getenv("STRIPE_SECRET_KEY", "sk_test_...")
    stripe_publishable_key: str = os.getenv("STRIPE_PUBLISHABLE_KEY", "pk_test_...")

    # PayPal Settings
    paypal_client_id: str = os.getenv("PAYPAL_CLIENT_ID", "your-paypal-client-id")
    paypal_client_secret: str = os.getenv(
        "PAYPAL_CLIENT_SECRET", "your-paypal-client-secret"
    )
    paypal_mode: str = os.getenv("PAYPAL_MODE", "live")  # or "sandbox" for testing

    # Base URL for callbacks
    base_url: str = "http://localhost:8000"  # TODO: Set via environment

    # Payment Settings
    currency: str = "USD"
    payment_timeout_minutes: int = 30

    # Security
    secret_key: str = (
        "your-secret-key-change-in-production"  # TODO: Set via environment
    )
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30

    class Config:
        env_file = ".env"


settings = Settings()
