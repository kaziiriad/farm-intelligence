"""Request ID middleware + structured logging configuration."""
import json
import logging
import sys
import uuid
from typing import Any

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request


class JsonFormatter(logging.Formatter):
    """JSON log formatter for machine-readable output."""

    def format(self, record: logging.LogRecord) -> str:
        log_data: dict[str, Any] = {
            "timestamp": self.formatTime(record, self.datefmt),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        if hasattr(record, "request_id"):
            log_data["request_id"] = record.request_id
        if hasattr(record, "method"):
            log_data["method"] = record.method
        if hasattr(record, "path"):
            log_data["path"] = record.path
        if hasattr(record, "status_code"):
            log_data["status_code"] = record.status_code
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)
        return json.dumps(log_data)


def setup_logging() -> None:
    """Configure root logger to output JSON to stdout."""
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JsonFormatter())
    logging.root.addHandler(handler)
    logging.root.setLevel(logging.INFO)


class RequestIDMiddleware(BaseHTTPMiddleware):
    """Injects X-Request-ID header into every request and logs request/response."""

    async def dispatch(self, request: Request, call_next):
        request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
        request.state.request_id = request_id

        extra = {"request_id": request_id, "method": request.method, "path": request.url.path}

        logger = logging.getLogger("app.middleware")
        logger.info(f"Request started", extra=extra)

        response = await call_next(request)

        extra["status_code"] = response.status_code
        logger.info(f"Request completed", extra=extra)

        response.headers["X-Request-ID"] = request_id
        return response