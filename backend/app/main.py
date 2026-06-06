"""FastAPI application factory."""
from fastapi import FastAPI

from app.routers import advisories, farms
from app.utils.exceptions import register_exception_handlers


def create_app() -> FastAPI:
    """Build the FastAPI app with all routers wired up."""
    app = FastAPI(
        title="Kenya Farm & Weather Intelligence API",
        version="0.1.0",
        description="Backend for farm advisories and tree analysis using WeatherAI free tier.",
    )

    @app.get("/health", tags=["health"])
    async def health() -> dict[str, str]:
        return {"status": "ok"}

    app.include_router(farms.router)
    app.include_router(advisories.router)
    register_exception_handlers(app)
    return app


app = create_app()