"""Shared pytest fixtures.

Phase 0: `MockTransportBuilder` helper.
Phase 1+: `engine` (per-test in-memory SQLite), `db_session`, `client` (ASGI).
"""
from __future__ import annotations

import os
# Disable dotenv loading before any app module imports config.
os.environ["DOTENV_LOAD"] = "0"

from collections.abc import AsyncIterator, Callable

import httpx
import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.pool import StaticPool

from app.core.config import get_settings
from app.core.database import Base, get_db
from app.main import create_app
from app.models.farm import Farm  # noqa: F401 — register table for create_all
from app.models.advisory import Advisory  # noqa: F401 — register table for create_all
from app.models.quota import QuotaRecord  # noqa: F401 — register table for create_all
from app.models.tree_analysis import TreeAnalysis  # noqa: F401 — register table for create_all


class MockTransportBuilder:
    """Thin wrapper around `httpx.MockTransport` for readable test setup."""

    def __init__(self, handler: Callable[[httpx.Request], httpx.Response]) -> None:
        self._handler = handler

    def build(self) -> httpx.MockTransport:
        return httpx.MockTransport(self._handler)


@pytest_asyncio.fixture
async def engine() -> AsyncIterator[AsyncEngine]:
    """Per-test in-memory SQLite engine. StaticPool keeps the same connection."""
    eng = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        echo=False,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    async with eng.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    try:
        yield eng
    finally:
        async with eng.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
        await eng.dispose()


@pytest_asyncio.fixture
async def db_session(engine: AsyncEngine) -> AsyncIterator[AsyncSession]:
    """Per-test async session bound to the in-memory engine."""
    sessionmaker = async_sessionmaker(bind=engine, expire_on_commit=False)
    async with sessionmaker() as session:
        yield session


@pytest_asyncio.fixture
async def client(db_session: AsyncSession) -> AsyncIterator[AsyncClient]:
    """AsyncClient bound to the FastAPI app with `get_db` overridden to test session."""
    app = create_app()

    async def _override_get_db() -> AsyncIterator[AsyncSession]:
        try:
            yield db_session
            await db_session.commit()
        except Exception:
            await db_session.rollback()
            raise

    app.dependency_overrides[get_db] = _override_get_db
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c
    app.dependency_overrides.clear()