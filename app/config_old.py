from functools import lru_cache
from pydantic_settings import BaseSettings
from pydantic import Field, AnyUrl
from typing import List


class Settings(BaseSettings):
    # ========= APP =========
    APP_NAME: str = Field(default="OrderProcessingAPI")
    APP_VERSION: str = Field(default="1.0.0")
    ENVIRONMENT: str = Field(default="development")  # development | staging | production
    DEBUG: bool = Field(default=True)

    HOST: str = Field(default="0.0.0.0")
    PORT: int = Field(default=8000)

    # ========= LOGGING =========
    LOG_LEVEL: str = Field(default="INFO")  # DEBUG | INFO | WARNING | ERROR

    # ========= DATABASE =========
    DATABASE_URL: AnyUrl | str = Field(default="sqlite:///./database.db")

    # ========= CORS =========
    CORS_ORIGINS: List[str] = Field(default=["*"])
    CORS_METHODS: List[str] = Field(default=["*"])
    CORS_HEADERS: List[str] = Field(default=["*"])
    CORS_CREDENTIALS: bool = Field(default=True)

    class Config:
        env_file = ".env"
        case_sensitive = False


@lru_cache()
def get_settings():
    return Settings()


settings = get_settings()
