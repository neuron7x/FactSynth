from __future__ import annotations

import time
from fastapi import FastAPI, Response

from .api.routers import api
from .core.auth import APIKeyAuthMiddleware
from .core.body_limit import BodySizeLimitMiddleware
from .core.errors import install_handlers
from .core.logging import setup_logging
from .core.metrics import LATENCY, REQUESTS, metrics_bytes, metrics_content_type
from .core.request_id import RequestIDMiddleware
from .core.security_headers import SecurityHeadersMiddleware
from .core.settings import load_settings
from .core.ratelimit import RateLimitMiddleware
from starlette.middleware.base import BaseHTTPMiddleware


class _MetricsMiddleware(BaseHTTPMiddleware):
    """Collect basic Prometheus-style metrics."""

    async def dispatch(self, request, call_next):
        path = request.url.path
        method = request.method
        start = time.perf_counter()
        response = await call_next(request)
        duration = max(0.0, time.perf_counter() - start)
        try:
            REQUESTS.labels(method, path, str(response.status_code)).inc()
            LATENCY.labels(path).observe(duration)
        except Exception:
            pass
        return response


def create_app() -> FastAPI:
    """Application factory used by tests and ASGI server."""
    settings = load_settings()
    setup_logging()

    app = FastAPI()
    install_handlers(app)

    # core routes
    app.include_router(api)

    @app.get("/v1/healthz")
    def healthz() -> dict[str, str]:
        return {"status": "ok"}

    @app.get("/metrics")
    def metrics() -> Response:
        return Response(metrics_bytes(), media_type=metrics_content_type())

    # middleware stack
    app.add_middleware(RequestIDMiddleware)
    app.add_middleware(SecurityHeadersMiddleware, hsts=settings.https_redirect)
    app.add_middleware(BodySizeLimitMiddleware)
    app.add_middleware(
        APIKeyAuthMiddleware,
        api_key="change-me",
        header_name=settings.auth_header_name,
        skip=tuple(settings.skip_auth_paths.split(",")),
    )
    app.add_middleware(
        RateLimitMiddleware,
        per_minute=settings.ratelimit_per_minute,
        key_header=settings.auth_header_name,
    )
    app.add_middleware(_MetricsMiddleware)

    return app


# module-level app for import from tests
app = create_app()
