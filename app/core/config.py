"""Configuration centralisee de l'application (variables d'environnement)."""
from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    APP_NAME: str = "StageFlow API"
    API_V1_PREFIX: str = "/api/v1"
    DEBUG: bool = False

    # Base de donnees : PostgreSQL en production, SQLite autorise pour certains tests
    DATABASE_URL: str = "postgresql+asyncpg://stageflow:stageflow@localhost:5432/stageflow"

    # Securite / JWT
    SECRET_KEY: str = "change-me-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    # Pagination
    DEFAULT_PAGE_SIZE: int = 20
    MAX_PAGE_SIZE: int = 100

    # Regle metier : nombre minimal d'items/annotateurs (reutilise si besoin par d'autres sujets)
    ENV: str = "development"


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
