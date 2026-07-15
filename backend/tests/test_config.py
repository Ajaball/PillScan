"""
Tests for DATABASE_URL normalization — ensures hosted Postgres connection
strings (Neon / Supabase / Render) are rewritten to the async driver and that
libpq-only query params asyncpg rejects are stripped.
"""

from app.config import Settings


def _norm(url: str) -> str:
    return Settings._normalize_database_url.__func__(Settings, url)


def test_sqlite_passthrough():
    url = "sqlite+aiosqlite:///./test.db"
    assert _norm(url) == url


def test_postgres_scheme_rewritten_to_asyncpg():
    assert _norm("postgres://u:p@host:5432/db").startswith("postgresql+asyncpg://")
    assert _norm("postgresql://u:p@host:5432/db").startswith("postgresql+asyncpg://")


def test_neon_sslmode_and_channel_binding_stripped():
    url = "postgresql://u:p@ep-x.neon.tech/db?sslmode=require&channel_binding=require"
    out = _norm(url)
    assert out.startswith("postgresql+asyncpg://")
    assert "sslmode" not in out
    assert "channel_binding" not in out


def test_other_query_params_are_kept():
    url = "postgresql://u:p@host/db?sslmode=require&application_name=pillscan"
    out = _norm(url)
    assert "application_name=pillscan" in out
    assert "sslmode" not in out
