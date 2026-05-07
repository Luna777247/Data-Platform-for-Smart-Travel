from pydantic_settings import BaseSettings
from pydantic import Field
from functools import lru_cache


class Settings(BaseSettings):
    # Database
    mongodb_url: str = Field(default="mongodb://localhost:27017", alias="MONGODB_URI")
    mongodb_database: str = Field(default="smart_travel", alias="DB_NAME")
    postgres_url: str = Field(
        default="postgresql+asyncpg://user:password@localhost:5432/smart_travel",
        alias="POSTGRES_URL",
    )
    redis_url: str = Field(default="redis://localhost:6379", alias="REDIS_URL")

    # API Security
    secret_key: str = Field(default="change-me-in-production-please", alias="SECRET_KEY")
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30

    # External APIs
    google_places_api_key: str = Field(default="", alias="GOOGLE_PLACES_API_KEY")

    # App
    environment: str = Field(default="development", alias="ENVIRONMENT")
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")
    debug: bool = Field(default=False, alias="DEBUG")

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "populate_by_name": True,
        "extra": "ignore",
    }


@lru_cache()
def get_settings() -> Settings:
    return Settings()


settings = get_settings()