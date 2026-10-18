import os
from typing import List, Union
from pydantic import AnyHttpUrl, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    PROJECT_NAME: str = "IdeaLens"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    
    # Environment & Deployment Mode (development, testing, production)
    ENVIRONMENT: str = "development"

    # Security & Authentication
    SECRET_KEY: str = "idealens_super_secret_jwt_key_development_change_in_production_2026"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days

    # Database
    # Defaults to local SQLite file for friction-free dev, easily swapped to PostgreSQL via env var:
    # postgresql+psycopg2://postgres:postgres@localhost:5432/idealens
    DATABASE_URL: str = "sqlite:///./idealens.db"
    DATABASE_POOL_SIZE: int = 15
    DATABASE_MAX_OVERFLOW: int = 25
    DATABASE_POOL_TIMEOUT: int = 30
    DATABASE_POOL_RECYCLE: int = 1800

    # API Security & Body Limits
    MAX_REQUEST_SIZE_BYTES: int = 10 * 1024 * 1024  # 10MB max request body

    @field_validator("BACKEND_CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> List[str]:
        if isinstance(v, str):
            v = v.strip()
            if not v:
                return []
            if v.startswith("[") and v.endswith("]"):
                import json
                try:
                    return json.loads(v)
                except Exception:
                    pass
            return [i.strip() for i in v.split(",") if i.strip()]
        elif isinstance(v, (list, tuple)):
            return list(v)
        return v

    @model_validator(mode="after")
    def validate_production_configuration(self) -> "Settings":
        env = (self.ENVIRONMENT or "development").strip().lower()
        if env == "production":
            # 1. DATABASE_URL must be a valid PostgreSQL URL
            db_url = (self.DATABASE_URL or "").strip()
            if not db_url or db_url.startswith("sqlite"):
                raise ValueError(
                    "Production configuration error: SQLite is strictly prohibited in production mode. "
                    "Configure a valid PostgreSQL DATABASE_URL (e.g. postgresql+psycopg2://user:password@host:5432/dbname)."
                )
            if not (db_url.startswith("postgresql://") or db_url.startswith("postgresql+psycopg2://") or db_url.startswith("postgres://")):
                raise ValueError(
                    f"Production configuration error: DATABASE_URL must use the PostgreSQL dialect. "
                    f"Received: '{db_url.split('://')[0]}://...'. Expected 'postgresql+psycopg2://' or 'postgresql://'."
                )

            # 2. SECRET_KEY must be strong, non-empty, and not a known placeholder
            secret = (self.SECRET_KEY or "").strip()
            insecure_placeholders = [
                "idealens_super_secret",
                "change_in_production",
                "change_me",
                "secret_key_development",
                "development",
                "your-secure-random",
                "replace_me",
                "secret",
            ]
            if not secret or len(secret) < 32:
                raise ValueError(
                    "Production configuration error: SECRET_KEY must be at least 32 characters long. "
                    "Generate a secure 64-character hex key using 'openssl rand -hex 32'."
                )
            if any(placeholder in secret.lower() for placeholder in insecure_placeholders):
                raise ValueError(
                    "Production configuration error: Insecure or placeholder SECRET_KEY detected in production mode. "
                    "Set a dedicated cryptographic secret in environment variables (e.g. via 'openssl rand -hex 32')."
                )

            # 3. BACKEND_CORS_ORIGINS must be explicitly configured with non-localhost origins
            if not self.BACKEND_CORS_ORIGINS:
                raise ValueError(
                    "Production configuration error: BACKEND_CORS_ORIGINS must be explicitly set for production."
                )

            has_production_origin = any(
                not ("localhost" in o or "127.0.0.1" in o)
                for o in self.BACKEND_CORS_ORIGINS
            )
            if not has_production_origin:
                raise ValueError(
                    "Production configuration error: BACKEND_CORS_ORIGINS contains only local development addresses. "
                    "Configure your production domain(s) (e.g. ['https://idealens.ai', 'https://app.idealens.ai'])."
                )

            if "*" in self.BACKEND_CORS_ORIGINS:
                raise ValueError(
                    "Production configuration error: Wildcard '*' in BACKEND_CORS_ORIGINS is prohibited when credentials are enabled."
                )

        return self
    
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
    IEEE_API_KEY: str = ""
    USPTO_API_KEY: str = ""
    EPO_CONSUMER_KEY: str = ""
    EPO_CONSUMER_SECRET: str = ""
    
    # CORS
    BACKEND_CORS_ORIGINS: Union[List[str], str] = [
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
