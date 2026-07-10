"""Unified configuration management.

Uses pydantic-settings BaseSettings to load from .env.
All modules share a single Settings instance via import.
"""
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=Path(__file__).resolve().parent.parent.parent / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    APP_NAME: str = "Project Machine"
    APP_VERSION: str = "0.1.0"
    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str = ""
    POSTGRES_DB: str = "machine"
    DATABASE_URL: str = ""
    LOG_LEVEL: str = "INFO"
    API_PREFIX: str = "/api/v1"
    LLM_API_KEY: str = ""
    LLM_BASE_URL: str = "https://api.deepseek.com"
    LLM_MODEL: str = "deepseek-chat"
    BAIDU_API_KEY: str = ""
    BAIDU_SECRET_KEY: str = ""

    def model_post_init(self, __context):
        if not self.DATABASE_URL:
            self.DATABASE_URL = (
                f"postgresql://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
                f"@localhost:5432/{self.POSTGRES_DB}"
            )


settings = Settings()