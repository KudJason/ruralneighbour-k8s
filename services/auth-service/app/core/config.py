from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Database
    database_url: str = (
        "postgresql://user:password@localhost/dbname"  # TODO: Set via environment
    )

    # JWT
    secret_key: str = (
        "your-secret-key-change-in-production"  # TODO: Set via environment
    )
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30

    # Security
    bcrypt_rounds: int = 12

    class Config:
        env_file = ".env"


settings = Settings()
