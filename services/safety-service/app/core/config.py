from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = "sqlite:///./test_safety.db"
    max_retry_attempts: int = 3


settings = Settings()


