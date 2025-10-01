from pydantic_settings import BaseSettings
import os


class Settings(BaseSettings):
    # Database
    database_url: str = os.getenv("DATABASE_URL", "postgresql://user:password@localhost/dbname")

    # JWT
    secret_key: str = os.getenv("SECRET_KEY", "your-secret-key-change-in-production")
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30

    # Security
    bcrypt_rounds: int = 12

    # Email Service Configuration
    # SendGrid (Primary)
    sendgrid_api_key: str = ""
    from_email: str = "noreply@ruralneighbor.com"
    frontend_url: str = "https://ruralneighbor.com"

    # SMTP (Fallback)
    smtp_server: str = "smtp.gmail.com"
    smtp_port: int = 587
    smtp_username: str = ""
    smtp_password: str = ""

    class Config:
        env_file = ".env"


settings = Settings()
