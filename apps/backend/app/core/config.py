from functools import lru_cache
from urllib.parse import quote_plus

from pydantic import Field, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


_ALLOWED_JWT_ALGORITHMS = {"HS256", "HS384", "HS512"}


class Settings(BaseSettings):
    mongodb_url: str | None = Field(default=None, alias="MONGODB_URI")
    mongodb_host: str = Field(default="mongodb", alias="MONGODB_HOST")
    mongodb_port: int = Field(default=27017, alias="MONGODB_PORT")
    mongodb_user: str = Field(default="admin", alias="MONGODB_USER")
    mongodb_password: str | None = Field(default=None, alias="MONGODB_PASSWORD")
    mongodb_database: str = Field(default="smart_travel", alias="DB_NAME")
    postgres_url: str | None = Field(default=None, alias="POSTGRES_URL")
    postgres_host: str = Field(default="postgres", alias="POSTGRES_HOST")
    postgres_port: int = Field(default=5432, alias="POSTGRES_PORT")
    postgres_user: str = Field(default="admin", alias="POSTGRES_USER")
    postgres_password: str | None = Field(default=None, alias="POSTGRES_PASSWORD")
    postgres_db: str = Field(default="smart_travel", alias="POSTGRES_DB")
    redis_url: str | None = Field(default=None, alias="REDIS_URL")
    redis_host: str = Field(default="redis", alias="REDIS_HOST")
    redis_port: int = Field(default=6379, alias="REDIS_PORT")
    redis_password: str | None = Field(default=None, alias="REDIS_PASSWORD")

    secret_key: str | None = Field(default=None, alias="SECRET_KEY")
    jwt_secret: str | None = Field(default=None, alias="JWT_SECRET")
    algorithm: str = Field(default="HS256", alias="ALGORITHM")
    access_token_expire_minutes: int = Field(default=30, alias="ACCESS_TOKEN_EXPIRE_MINUTES")
    refresh_token_expire_days: int = Field(default=7, alias="REFRESH_TOKEN_EXPIRE_DAYS")

    google_places_api_key: str | None = Field(default=None, alias="GOOGLE_PLACES_API_KEY")
    minio_access_key: str | None = Field(default=None, alias="MINIO_ACCESS_KEY")
    minio_secret_key: str | None = Field(default=None, alias="MINIO_SECRET_KEY")
    minio_endpoint: str = Field(default="minio:9000", alias="MINIO_ENDPOINT")
    minio_secure: bool = Field(default=False, alias="MINIO_SECURE")

    environment: str = Field(default="development", alias="ENVIRONMENT")
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")
    debug: bool = Field(default=False, alias="DEBUG")

    allowed_origins: str = Field(default="http://localhost:3000", alias="ALLOWED_ORIGINS")
    rate_limit_enabled: bool = Field(default=True, alias="RATE_LIMIT_ENABLED")
    rate_limit_requests_per_minute: int = Field(
        default=60,
        alias="RATE_LIMIT_REQUESTS_PER_MINUTE",
    )
    rate_limit_requests_per_hour: int = Field(
        default=1000,
        alias="RATE_LIMIT_REQUESTS_PER_HOUR",
    )

    enable_https: bool = Field(default=False, alias="ENABLE_HTTPS")
    use_docker_secrets: bool = Field(default=True, alias="USE_DOCKER_SECRETS")
    vault_addr: str | None = Field(default=None, alias="VAULT_ADDR")

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        secrets_dir="/run/secrets",
        populate_by_name=True,
        extra="ignore",
    )

    @field_validator("algorithm")
    @classmethod
    def validate_algorithm(cls, value: str) -> str:
        normalized = value.upper().strip()
        if normalized not in _ALLOWED_JWT_ALGORITHMS:
            raise ValueError(
                f"Unsupported JWT algorithm '{value}'. Allowed: {sorted(_ALLOWED_JWT_ALGORITHMS)}"
            )
        return normalized

    @field_validator("allowed_origins")
    @classmethod
    def normalize_allowed_origins(cls, value: str) -> str:
        origins = [origin.strip() for origin in str(value).split(",") if origin.strip()]
        if not origins:
            raise ValueError("ALLOWED_ORIGINS must contain at least one origin")
        return ",".join(dict.fromkeys(origins))

    @model_validator(mode="after")
    def validate_security_configuration(self):
        print("DEBUG: Validation started")
        production_mode = self.environment.lower() in {"prod", "production"}

        if self.access_token_expire_minutes <= 0:
            raise ValueError("ACCESS_TOKEN_EXPIRE_MINUTES must be greater than 0")
        if self.refresh_token_expire_days <= 0:
            raise ValueError("REFRESH_TOKEN_EXPIRE_DAYS must be greater than 0")

        if production_mode:
            if self.debug:
                raise ValueError("DEBUG must be false in production")
            if not self.secret_key or len(self.secret_key) < 32:
                raise ValueError("SECRET_KEY must be configured and at least 32 characters")
            if not self.jwt_secret or len(self.jwt_secret) < 32:
                raise ValueError("JWT_SECRET must be configured and at least 32 characters")
            if not self.google_places_api_key:
                raise ValueError("GOOGLE_PLACES_API_KEY must be configured in production")
            if not self.minio_access_key:
                raise ValueError("MINIO_ACCESS_KEY must be configured in production")
            if not self.minio_secret_key:
                raise ValueError("MINIO_SECRET_KEY must be configured in production")
            if self.mongodb_url and ("localhost" in self.mongodb_url.lower() or "127.0.0.1" in self.mongodb_url.lower()):
                raise ValueError("MONGODB_URI must not point to localhost in production")
            if self.postgres_url and ("localhost" in self.postgres_url.lower() or "127.0.0.1" in self.postgres_url.lower()):
                raise ValueError("POSTGRES_URL must not point to localhost in production")
            if self.redis_url and ("localhost" in self.redis_url.lower() or "127.0.0.1" in self.redis_url.lower()):
                raise ValueError("REDIS_URL must not point to localhost in production")
            if self.enable_https is False:
                raise ValueError("ENABLE_HTTPS must be true in production")
            origins = self.allowed_origins_list
            if any(origin == "*" for origin in origins):
                raise ValueError("Wildcard CORS origins are not allowed in production")
            if any(origin.startswith("http://") for origin in origins):
                raise ValueError("HTTP CORS origins are not allowed in production")

        if self.mongodb_url is None:
            if not self.mongodb_password:
                raise ValueError("MONGODB_PASSWORD or MONGODB_URI must be configured")
            self.mongodb_url = (
                f"mongodb://{quote_plus(self.mongodb_user)}:{quote_plus(self.mongodb_password)}"
                f"@{self.mongodb_host}:{self.mongodb_port}/{self.mongodb_database}"
            )

        if self.postgres_url is None:
            if not self.postgres_password:
                raise ValueError("POSTGRES_PASSWORD or POSTGRES_URL must be configured")
            self.postgres_url = (
                f"postgresql+asyncpg://{quote_plus(self.postgres_user)}:{quote_plus(self.postgres_password)}"
                f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
            )

        if self.redis_url is None:
            if self.redis_password:
                self.redis_url = (
                    f"redis://:{quote_plus(self.redis_password)}@{self.redis_host}:{self.redis_port}/0"
                )
            else:
                self.redis_url = f"redis://{self.redis_host}:{self.redis_port}/0"

        if not self.secret_key or not self.jwt_secret:
            raise ValueError("SECRET_KEY and JWT_SECRET must be configured")

        return self

    @property
    def allowed_origins_list(self) -> list[str]:
        return [origin for origin in self.allowed_origins.split(",") if origin]

    @property
    def cors_origins_list(self) -> list[str]:
        return self.allowed_origins_list


@lru_cache()
def get_settings() -> Settings:
    return Settings()


settings = get_settings()