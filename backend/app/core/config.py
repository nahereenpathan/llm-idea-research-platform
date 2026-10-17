import os
from typing import List, Union
from pydantic import AnyHttpUrl, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    PROJECT_NAME: str = "IdeaLens"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    
    # Security & Authentication
    SECRET_KEY: str = "idealens_super_secret_jwt_key_development_change_in_production_2026"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days
    
    # Database
    # Defaults to local SQLite file for friction-free dev, easily swapped to PostgreSQL via env var:
    # postgresql+psycopg2://postgres:postgres@localhost:5432/idealens
    DATABASE_URL: str = "sqlite:///./idealens.db"
    
    # Celery & Redis
    REDIS_URL: str = "redis://localhost:6379/0"
    CELERY_BROKER_URL: str = "redis://localhost:6379/0"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/0"
    USE_IN_PROCESS_BACKGROUND_TASKS: bool = True  # Fallback gracefully when Celery daemon is inactive
    
    # AI Providers (Configurable)
    LLM_PROVIDER: str = "auto"  # "gemini", "openai", "heuristic_fallback"
    OPENAI_API_KEY: str = ""
    OPENAI_MODEL: str = "gpt-4o-mini"
    GEMINI_API_KEY: str = ""
    GEMINI_MODEL: str = "gemini-1.5-flash"
    
    # External Research API configurations
    OPENALEX_MAILTO: str = "research@idealens.ai"
    CROSSREF_MAILTO: str = "research@idealens.ai"
    
    # CORS
    BACKEND_CORS_ORIGINS: List[str] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
    ]
    
    # Storage / Exports
    EXPORT_STORAGE_DIR: str = "./exports_storage"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore"
    )


settings = Settings()
