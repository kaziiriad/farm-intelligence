"""Shared pytest fixtures for all test modules.

Phase 0 introduces:
- `MockTransportBuilder`: tiny helper to build `httpx.MockTransport` for tests
  that need to intercept upstream WeatherAI calls without a network.

Later phases add:
- `client`: `AsyncClient` bound to the FastAPI app via ASGI transport
- `db_session`: per-test async SQLite session
- `cache`: fakeredis-backed cache instance
- `mock_weatherai`: a configured `httpx.MockTransport` for WeatherAI endpoints
"""
from __future__ import annotations

from collections.abc import Callable

import httpx


class MockTransportBuilder:
    """Thin wrapper around `httpx.MockTransport` for readable test setup.

    Usage in a test:
        transport = MockTransportBuilder(my_handler).build()
        async with httpx.AsyncClient(transport=transport) as client:
            ...

    This class exists so tests can import a stable name (`MockTransportBuilder`)
    even as the underlying fixture evolves across phases.
    """

    def __init__(self, handler: Callable[[httpx.Request], httpx.Response]) -> None:
        self._handler = handler

    def build(self) -> httpx.MockTransport:
        return httpx.MockTransport(self._handler)