"""FastAPI application factory."""
from fastapi import FastAPI

from app.middleware.logging import RequestIDMiddleware, setup_logging
from app.routers import advisories, farms, trees, usage
from app.utils.exceptions import register_exception_handlers


def create_app() -> FastAPI:
    """Build the FastAPI app with all routers wired up."""
    setup_logging()

    app = FastAPI(
        title="Kenya Farm & Weather Intelligence API",
        version="0.1.0",
        description="Backend for farm advisories and tree analysis using WeatherAI free tier.",
    )

    app.add_middleware(RequestIDMiddleware)

    @app.get("/health", tags=["health"])
    async def health() -> dict[str, str]:
        return {"status": "ok"}

    @app.get("/health/ready", tags=["health"])
    async def readiness() -> dict[str, str]:
        """Readiness probe — checks DB and Redis connectivity."""
        from app.core.database import engine
        from app.core.cache import RedisCache

        try:
            from sqlalchemy import text
            async with engine.connect() as conn:
                await conn.execute(text("SELECT 1"))
        except Exception:
            return {"status": "not ready", "reason": "database unavailable"}

        try:
            cache = RedisCache()
            await cache.get("_health_check")
        except Exception:
            return {"status": "not ready", "reason": "cache unavailable"}

        return {"status": "ok"}

    app.include_router(farms.router)
    app.include_router(advisories.router)
    app.include_router(trees.router)
    app.include_router(usage.router)
    register_exception_handlers(app)
    return app


app = create_app()