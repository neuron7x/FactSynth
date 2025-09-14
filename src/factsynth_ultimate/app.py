"""FastAPI application factory and middleware setup."""

from __future__ import annotations

import time
from collections.abc import Awaitable, Callable
from contextlib import suppress

from fastapi import FastAPI, Request, Response
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from starlette.middleware.base import BaseHTTPMiddleware

from . import VERSION
from .api.routers import api
from .core.auth import APIKeyAuthMiddleware
from .core.body_limit import BodySizeLimitMiddleware
from .core.errors import install_handlers
from .core.ip_allowlist import IPAllowlistMiddleware
from .core.logging import setup_logging
from .core.metrics import LATENCY, REQUESTS, metrics_bytes, metrics_content_type
from .core.request_id import RequestIDMiddleware
from .core.security_headers import SecurityHeadersMiddleware
from .core.settings import load_settings
from .core.tracing import try_enable_otel


class _MetricsMiddleware(BaseHTTPMiddleware):
    """Collect basic Prometheus-style metrics."""

    async def dispatch(
        self,
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
        route = request.scope.get("route")
        path = route.path if route else request.url.path
        method = request.method
        start = time.perf_counter()
        response = await call_next(request)
        duration = max(0.0, time.perf_counter() - start)
        with suppress(Exception):
            REQUESTS.labels(method, path, str(response.status_code)).inc()
            LATENCY.labels(path).observe(duration)
        return response


def create_app(rate_limit_window: int | None = None) -> FastAPI:
    """Application factory used by tests and ASGI server."""
    settings = load_settings()
    setup_logging()

    app = FastAPI(title="FactSynth Ultimate Pro API", version=VERSION)
    install_handlers(app)
    try_enable_otel(app)

    window = rate_limit_window or 60
    limiter = Limiter(
        key_func=lambda request: request.headers.get(settings.auth_header_name, ""),
        default_limits=[f"{settings.rate_limit_per_key}/{window} second"],
        storage_uri=settings.rate_limit_redis_url,
        headers_enabled=True,
    )
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
    app.add_middleware(SlowAPIMiddleware)

    # core routes
    app.include_router(api)

    @limiter.exempt
    @app.get("/v1/healthz")
    def healthz() -> dict[str, str]:
        """Simple liveness probe."""

        return {"status": "ok"}

    @limiter.exempt
    @app.get("/metrics")
    def metrics() -> Response:
        """Expose Prometheus metrics."""

        return Response(metrics_bytes(), media_type=metrics_content_type())

    # middleware stack (order matters: last added runs first)
    app.add_middleware(SecurityHeadersMiddleware, hsts=settings.https_redirect)
    if settings.ip_allowlist:
        app.add_middleware(IPAllowlistMiddleware, cidrs=settings.ip_allowlist)
    app.add_middleware(BodySizeLimitMiddleware)

    allowed_keys = settings.allowed_api_keys or [settings.api_key]
    if settings.env == "prod" and any(k in {"", "change-me"} for k in allowed_keys):
        raise RuntimeError("API key must be set in production")

    app.add_middleware(
        APIKeyAuthMiddleware,
        api_keys=allowed_keys,
        header_name=settings.auth_header_name,
        skip=tuple(settings.skip_auth_paths),
    )
    app.add_middleware(_MetricsMiddleware)
    app.add_middleware(RequestIDMiddleware)

    return app


# module-level app for import from tests
app = create_app()
