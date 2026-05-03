from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    database_url: str = "postgresql+asyncpg://postgres:password@localhost:5432/products_api"
    secret_key: str = "change-this-in-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 60
    rate_limit: str = "100/minute"
    cors_origins: List[str] = ["http://localhost:3000", "http://localhost:8080"]

    class Config:
        env_file = ".env"


settings = Settings()
