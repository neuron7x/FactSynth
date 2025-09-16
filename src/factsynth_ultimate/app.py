"""FastAPI application factory and middleware setup."""

from __future__ import annotations

import logging
import time
from collections.abc import Awaitable, Callable
from contextlib import asynccontextmanager, suppress

import fastapi.routing as fastapi_routing
import fastapi.utils as fastapi_utils
from fastapi._compat import (
    BaseConfig,
    FieldInfo,
    ModelField,
    PydanticUndefined,
    PydanticUndefinedType,
)
from fastapi import FastAPI, Request, Response
from fastapi import exceptions as fastapi_exceptions
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from typing import Any, Literal

from . import VERSION
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
from .store.redis import check_health


logger = logging.getLogger(__name__)

_CreateModelField = Callable[
    [
        str,
        Any,
        dict[str, Any] | None,
        Any,
        bool | PydanticUndefinedType,
        type[BaseConfig],
        FieldInfo | None,
        str | None,
        Literal["validation", "serialization"],
    ],
    ModelField,
]


if not getattr(fastapi_utils, "_factsynth_safe_field", False):
    _original_create_model_field: _CreateModelField = fastapi_utils.create_model_field

    def _safe_create_model_field(
        name: str,
        type_: Any,
        class_validators: dict[str, Any] | None = None,
        default: Any = PydanticUndefined,
        required: bool | PydanticUndefinedType = PydanticUndefined,
        model_config: type[BaseConfig] = BaseConfig,
        field_info: FieldInfo | None = None,
        alias: str | None = None,
        mode: Literal["validation", "serialization"] = "validation",
    ) -> ModelField | None:
        try:
            return _original_create_model_field(
                name,
                type_,
                class_validators=class_validators,
                default=default,
                required=required,
                model_config=model_config,
                field_info=field_info,
                alias=alias,
                mode=mode,
            )
        except fastapi_exceptions.FastAPIError as exc:
            if "Invalid args for response field" not in str(exc):
                raise
            return None

    fastapi_utils.create_model_field = _safe_create_model_field
    fastapi_routing.create_model_field = _safe_create_model_field
    fastapi_utils._factsynth_safe_field = True


from .api.routers import api


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

    try:
        settings = load_settings()
    except Exception as exc:  # pragma: no cover - configuration errors
        raise RuntimeError("Invalid configuration") from exc
    setup_logging()

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        try:
            healthy = await check_health(settings.rate_limit_redis_url)
        except Exception:  # pragma: no cover - defensive guard
            logger.warning("Failed to run Redis health check", exc_info=True)
        else:
            if not healthy:
                logger.warning(
                    "Redis health check failed for rate limit backend",
                    extra={"redis_url": settings.rate_limit_redis_url},
                )
        yield

    app = FastAPI(title="FactSynth Ultimate Pro API", version=VERSION, lifespan=lifespan)
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
    # SlowAPIMiddleware is added last so rate limiting happens before auth
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
    app.add_middleware(SlowAPIMiddleware)

    return app


# module-level app for import from tests
app = create_app()
