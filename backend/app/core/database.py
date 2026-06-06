"""Async SQLAlchemy engine and session factory.

`get_db` is the FastAPI dependency routers use. Tests override this dependency
in `tests/conftest.py` to bind each test to a fresh in-memory SQLite DB.
"""
from collections.abc import AsyncIterator

from sqlalchemy.engine import make_url
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase

from app.core.config import get_settings


class Base(DeclarativeBase):
    """Declarative base for all ORM models."""


_engine: AsyncEngine | None = None
_sessionmaker: async_sessionmaker[AsyncSession] | None = None


def build_engine_config(database_url: str) -> tuple[str, dict]:
    """Normalize deployment database URLs for SQLAlchemy's async engine.

    Supabase commonly provides a postgresql:// URL with sslmode=require.
    SQLAlchemy async engines need the asyncpg driver name, and asyncpg expects
    SSL as a connect argument instead of libpq-style sslmode.
    """
    url = make_url(database_url)
    connect_args: dict = {}

    if url.drivername in {"postgresql", "postgres"}:
        url = url.set(drivername="postgresql+asyncpg")

    if url.drivername == "postgresql+asyncpg":
        query = dict(url.query)
        sslmode = query.pop("sslmode", None)
        if sslmode:
            if sslmode == "disable":
                connect_args["ssl"] = False
            else:
                connect_args["ssl"] = True
            url = url.set(query=query)

    return url.render_as_string(hide_password=False), connect_args


def get_engine() -> AsyncEngine:
    global _engine
    if _engine is None:
        database_url, connect_args = build_engine_config(get_settings().database_url)
        _engine = create_async_engine(
            database_url,
            connect_args=connect_args,
            echo=False,
            future=True,
        )
    return _engine


def get_sessionmaker() -> async_sessionmaker[AsyncSession]:
    global _sessionmaker
    if _sessionmaker is None:
        _sessionmaker = async_sessionmaker(
            bind=get_engine(),
            expire_on_commit=False,
            class_=AsyncSession,
        )
    return _sessionmaker


async def get_db() -> AsyncIterator[AsyncSession]:
    """FastAPI dependency. Yields a session; commits on success, rolls back on error."""
    session = get_sessionmaker()()
    try:
        yield session
        await session.commit()
    except Exception:
        await session.rollback()
        raise
    finally:
        await session.close()


async def reset_engine_for_tests() -> None:
    """Test helper: drop cached engine so the next call re-reads settings."""
    global _engine, _sessionmaker
    if _engine is not None:
        await _engine.dispose()
    _engine = None
    _sessionmaker = None
