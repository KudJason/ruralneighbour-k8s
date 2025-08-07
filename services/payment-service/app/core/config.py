from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Database
    database_url: str = (
        "postgresql://user:password@localhost/dbname"  # TODO: Set via environment
    )

    # Redis for event streaming
    redis_url: str = "redis://localhost:6379/0"

    # Payment Provider Settings
    stripe_secret_key: str = "sk_test_..."  # TODO: Set via environment
    stripe_publishable_key: str = "pk_test_..."  # TODO: Set via environment

    # PayPal Settings
    paypal_client_id: str = "your-paypal-client-id"  # TODO: Set via environment
    paypal_client_secret: str = "your-paypal-client-secret"  # TODO: Set via environment
    paypal_mode: str = "sandbox"  # or "live" for production

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
