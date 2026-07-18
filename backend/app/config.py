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

    # ── Vision LLM (Google Gemini) ───────────────────────────────────────
    # Powers both pill identification and the Arabic leaflet summary — the
    # sole identification path (no local CV model). Users add their own keys
    # in the app; these env keys are an optional server-wide fallback. Up to
    # five keys are tried in order — when one is exhausted (quota/rate-limit)
    # or fails, the next is used.
    LLM_TIMEOUT_SECONDS: int = 60

    GEMINI_MODEL: str = "gemini-2.5-flash"
    # If the primary model returns 404 (not available on the caller's key/region),
    # these are tried in order so identification keeps working instead of failing.
    GEMINI_MODEL_FALLBACKS: list[str] = [
        "gemini-2.5-pro",
        "gemini-2.0-flash",
        "gemini-1.5-flash",
    ]
    GEMINI_API_BASE: str = "https://generativelanguage.googleapis.com/v1beta"
    GEMINI_API_KEY: Optional[str] = None
    GEMINI_API_KEY_2: Optional[str] = None
    GEMINI_API_KEY_3: Optional[str] = None
    GEMINI_API_KEY_4: Optional[str] = None
    GEMINI_API_KEY_5: Optional[str] = None

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
    ADMIN_PHONE: str = "+966500000000"  # override via env var in production!
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
        Managed Postgres providers (Render, Heroku, Railway, Neon, Supabase...)
        hand out URLs with the sync ``postgres://`` or ``postgresql://`` scheme,
        often with ``?sslmode=require&channel_binding=require`` query params.

        This app uses an async engine (``postgresql+asyncpg://``), and the
        asyncpg driver does NOT understand libpq's ``sslmode`` / ``channel_binding``
        query params — leaving them in the URL makes the connection crash. So we:
          1. rewrite the scheme to the async driver, and
          2. strip the libpq-only query params (SSL itself is enabled in
             database.py via connect_args for remote hosts).
        SQLite and already-async URLs pass through unchanged.
        """
        if not isinstance(v, str) or not v:
            return v
        if v.startswith("postgres://"):
            v = "postgresql://" + v[len("postgres://"):]
        if v.startswith("postgresql://"):
            v = "postgresql+asyncpg://" + v[len("postgresql://"):]

        # Drop libpq-only query params that asyncpg rejects.
        if v.startswith("postgresql+asyncpg://") and "?" in v:
            from urllib.parse import urlsplit, urlunsplit, parse_qsl, urlencode

            parts = urlsplit(v)
            drop = {"sslmode", "channel_binding"}
            kept = [(k, val) for k, val in parse_qsl(parts.query) if k not in drop]
            v = urlunsplit(parts._replace(query=urlencode(kept)))
        return v


@lru_cache()
def get_settings() -> Settings:
    """Cached settings instance — loaded once, reused across the app."""
    return Settings()
