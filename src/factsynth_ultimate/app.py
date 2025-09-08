from __future__ import annotations

import contextlib
import time
from contextlib import suppress
from typing import Awaitable, Callable

from fastapi import FastAPI, Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from .api.routers import api
from .core.auth import APIKeyAuthMiddleware
from .core.body_limit import BodySizeLimitMiddleware
from .core.errors import install_handlers
from .core.ip_allowlist import IPAllowlistMiddleware
from .core.logging import setup_logging
from .core.metrics import LATENCY, REQUESTS, metrics_bytes, metrics_content_type
from .core.ratelimit import RateLimitMiddleware
from .core.request_id import RequestIDMiddleware
from .core.secrets import read_api_key
from .core.tracing import try_enable_otel
from .core.security_headers import SecurityHeadersMiddleware
from .core.settings import load_settings


class _MetricsMiddleware(BaseHTTPMiddleware):
    """Collect basic Prometheus-style metrics."""

    async def dispatch(
        self,
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
        path = request.url.path
        method = request.method
        start = time.perf_counter()
        response = await call_next(request)
        duration = max(0.0, time.perf_counter() - start)
        with suppress(Exception):
            REQUESTS.labels(method, path, str(response.status_code)).inc()
            LATENCY.labels(path).observe(duration)
        return response


def create_app(
    bucket_ttl: int | None = None,
    cleanup_interval: int | None = None,
) -> FastAPI:
    """Application factory used by tests and ASGI server."""
    settings = load_settings()
    setup_logging()

    app = FastAPI()
    install_handlers(app)
    try_enable_otel(app)

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
    if settings.ip_allowlist:
        app.add_middleware(
            IPAllowlistMiddleware,
            cidrs=settings.ip_allowlist.split(","),
        )
    app.add_middleware(BodySizeLimitMiddleware)
    app.add_middleware(
        APIKeyAuthMiddleware,
        api_key=read_api_key("API_KEY", "API_KEY_FILE", "change-me", "API_KEY"),
        header_name=settings.auth_header_name,
        skip=tuple(settings.skip_auth_paths),
    )
    app.add_middleware(
        RateLimitMiddleware,
        per_minute=settings.rate_limit_per_minute,
        key_header=settings.auth_header_name,
        bucket_ttl=bucket_ttl
        if bucket_ttl is not None
        else settings.rate_limit_bucket_ttl,
        cleanup_interval=cleanup_interval
        if cleanup_interval is not None
        else settings.rate_limit_cleanup_interval,
    )
    app.add_middleware(_MetricsMiddleware)

    return app


# module-level app for import from tests
app = create_app()
