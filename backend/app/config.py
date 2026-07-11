"""
PillScan Backend Configuration
Centralizes all environment-variable-driven settings using pydantic-settings.
"""

from pydantic_settings import BaseSettings
from pydantic import field_validator
from functools import lru_cache
from typing import Optional


class Settings(BaseSettings):
    """Application settings loaded from environment variables or .env file."""

    # ── App ──────────────────────────────────────────────────────────────
    APP_NAME: str = "PillScan API"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    ENVIRONMENT: str = "development"  # development | staging | production

    # ── Server ───────────────────────────────────────────────────────────
    HOST: str = "0.0.0.0"
    PORT: int = 8000

    # ── Database ─────────────────────────────────────────────────────────
    DATABASE_URL: str = "postgresql+asyncpg://pillscan:pillscan_password@localhost:5432/pillscan_db"
    DATABASE_ECHO: bool = False  # Log SQL queries (useful for debugging)

    # ── Redis ────────────────────────────────────────────────────────────
    REDIS_URL: str = "redis://localhost:6379/0"

    # ── JWT Authentication ───────────────────────────────────────────────
    JWT_SECRET_KEY: str = "CHANGE-THIS-TO-A-STRONG-RANDOM-SECRET-KEY-IN-PRODUCTION"
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    JWT_REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # ── AI Inference Service ─────────────────────────────────────────────
    AI_SERVICE_URL: str = "http://localhost:8001"
    AI_MODEL_PATH: str = "./ai/models"
    AI_CONFIDENCE_THRESHOLD: float = 0.5

    # ── Leaflet Summarizer (Vision LLM) ──────────────────────────────────
    # Reads a medication leaflet / prescription image and returns an Arabic
    # summary. Provider is switchable — set the API key for whichever you use.
    LLM_PROVIDER: str = "gemini"  # gemini | openai
    LLM_TIMEOUT_SECONDS: int = 60

    # Google Gemini
    GEMINI_API_KEY: Optional[str] = None
    GEMINI_MODEL: str = "gemini-2.0-flash"
    GEMINI_API_BASE: str = "https://generativelanguage.googleapis.com/v1beta"

    # OpenAI (ChatGPT)
    OPENAI_API_KEY: Optional[str] = None
    OPENAI_MODEL: str = "gpt-4o-mini"
    OPENAI_API_BASE: str = "https://api.openai.com/v1"

    # ── AWS S3 (Image Storage) ───────────────────────────────────────────
    AWS_ACCESS_KEY_ID: Optional[str] = None
    AWS_SECRET_ACCESS_KEY: Optional[str] = None
    AWS_REGION: str = "me-south-1"  # Bahrain region (closest to Saudi Arabia)
    S3_BUCKET_NAME: str = "pillscan-images"

    # ── Database Seeding ─────────────────────────────────────────────────
    # Auto-populate the default admin user + drug catalog on startup. Very
    # handy on hosts with an ephemeral filesystem (e.g. Render free tier),
    # where the SQLite file is wiped on every deploy. Idempotent — it skips
    # anything that already exists. Set SEED_ON_STARTUP=false to disable.
    SEED_ON_STARTUP: bool = True
    ADMIN_EMAIL: str = "admin@pillscan.com"
    ADMIN_PASSWORD: str = "admin123"  # override via env var in production!

    # ── Rate Limiting ────────────────────────────────────────────────────
    RATE_LIMIT_PER_MINUTE: int = 60

    # ── CORS ─────────────────────────────────────────────────────────────
    CORS_ORIGINS: list[str] = ["*"]  # Restrict in production

    # ── File Upload ──────────────────────────────────────────────────────
    MAX_UPLOAD_SIZE_MB: int = 10
    ALLOWED_IMAGE_TYPES: list[str] = ["image/jpeg", "image/png", "image/webp"]

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "case_sensitive": True,
    }

    @field_validator("DATABASE_URL", mode="before")
    @classmethod
    def _normalize_database_url(cls, v: str) -> str:
        """
        Managed Postgres providers (Render, Heroku, Railway...) hand out URLs
        with the sync ``postgres://`` or ``postgresql://`` scheme. This app uses
        an async engine, which requires the ``postgresql+asyncpg://`` driver, so
        rewrite the scheme automatically. SQLite and already-async URLs pass
        through unchanged.
        """
        if not isinstance(v, str) or not v:
            return v
        if v.startswith("postgres://"):
            v = "postgresql://" + v[len("postgres://"):]
        if v.startswith("postgresql://"):
            v = "postgresql+asyncpg://" + v[len("postgresql://"):]
        return v


@lru_cache()
def get_settings() -> Settings:
    """Cached settings instance — loaded once, reused across the app."""
    return Settings()
