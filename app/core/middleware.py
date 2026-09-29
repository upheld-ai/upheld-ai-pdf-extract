from __future__ import annotations

import time
import uuid
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response
from app.core.logging import logger


class RequestCorrelationMiddleware(BaseHTTPMiddleware):
    """
    Middleware to inject correlation IDs, track processing duration,
    and enforce security headers.
    """

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
        request.state.request_id = request_id

        start_time = time.perf_counter()

        try:
            response = await call_next(request)
        except Exception:
            duration_ms = (time.perf_counter() - start_time) * 1000
            logger.error(
                f"[{request_id}] Failed {request.method} {request.url.path} in {duration_ms:.2f}ms"
            )
            raise

        duration_ms = (time.perf_counter() - start_time) * 1000
        response.headers["X-Request-ID"] = request_id
        response.headers["X-Process-Time"] = f"{duration_ms:.2f}ms"

        # Security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"

        if request.url.path not in ("/health/live", "/health/ready", "/"):
            logger.info(
                f"[{request_id}] {request.method} {request.url.path} -> {response.status_code} ({duration_ms:.2f}ms)"
            )

        return response
