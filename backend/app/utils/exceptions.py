"""Custom exception types and FastAPI handlers.

Filled in incrementally — Phase 0 registers an empty handler registry so the
app factory can wire it up from day one. Specific handlers (422, 429, 502,
etc.) land in later phases as the relevant endpoints are built.
"""
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse


def register_exception_handlers(app: FastAPI) -> None:
    """Register exception handlers on the FastAPI app.

    Phase 0: a single 404-ish fallback for unhandled errors. Phases 1+
    register domain-specific handlers (e.g. quota exhausted, upstream
    upstream failure) here.
    """

    @app.exception_handler(Exception)
    async def _unhandled(request: Request, exc: Exception) -> JSONResponse:
        # Intentionally generic — domain handlers must be more specific.
        return JSONResponse(
            status_code=500,
            content={"detail": "Internal server error", "path": str(request.url.path)},
        )