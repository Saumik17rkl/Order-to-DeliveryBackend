from functools import lru_cache
from typing import List

from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field


class Settings(BaseSettings):
    """
    Central application configuration loaded from environment (.env).
    All values are typed — invalid types fail fast but cleanly.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",      # ignore unknown env vars safely
    )

    # ======================
    # DATABASE
    # ======================
    database_url: str = Field(
        default="sqlite:///./database.db",
        alias="DATABASE_URL",
        description="SQLAlchemy database connection URL",
    )

    # ======================
    # SERVER
    # ======================
    host: str = Field(default="0.0.0.0", alias="HOST")
    port: int = Field(default=8000, alias="PORT")
    debug: bool = Field(default=False, alias="DEBUG")

    # ======================
    # API META
    # ======================
    app_name: str = Field(default="OrderProcessingAPI", alias="APP_NAME")
    app_version: str = Field(default="1.0.0", alias="APP_VERSION")
    environment: str = Field(default="development", alias="ENVIRONMENT")

    # ======================
    # CORS (SAFE DEFAULTS)
    # ======================
    cors_origins: List[str] = Field(
        default=["http://localhost:3000"],
        alias="CORS_ORIGINS",
    )
    cors_methods: List[str] = Field(
        default=["GET", "POST", "PATCH", "OPTIONS"],
        alias="CORS_METHODS",
    )
    cors_headers: List[str] = Field(
        default=["*"],
        alias="CORS_HEADERS",
    )
    cors_credentials: bool = Field(
        default=False,
        alias="CORS_CREDENTIALS",
    )

    # ======================
    # LOGGING
    # ======================
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
