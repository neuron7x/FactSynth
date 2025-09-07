from __future__ import annotations
from time import perf_counter
import logging, os
from fastapi import FastAPI, Response, Request
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.httpsredirect import HTTPSRedirectMiddleware
from starlette.middleware.trustedhost import TrustedHostMiddleware
from .core.settings import load_settings, Settings
from .core.metrics import metrics_bytes, metrics_content_type, REQUESTS, LATENCY
from .core.auth import APIKeyAuthMiddleware
from .core.request_id import RequestIDMiddleware
from .core.ratelimit import RateLimitMiddleware
from .core.errors import install_handlers
from .core.logging import setup_logging
from .core.tracing import try_enable_otel
from .core.security_headers import SecurityHeadersMiddleware
from .core.secrets import read_api_key
from .core.health import multi_tcp_check
from .core.ip_allowlist import IPAllowlistMiddleware
from .core.body_limit import BodySizeLimitMiddleware
from .api.routers import api

def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or load_settings()
    setup_logging()
    app = FastAPI(title="FactSynth Ultimate Pro API", version="1.0.1")

    # HTTPS, headers, body limit
    if settings.https_redirect: app.add_middleware(HTTPSRedirectMiddleware)
    app.add_middleware(SecurityHeadersMiddleware, hsts=settings.env.lower()=="prod")
    app.add_middleware(BodySizeLimitMiddleware, max_bytes=int(os.getenv("MAX_BODY_BYTES","2000000")))

    # Trusted hosts/IP allowlist у prod
    if settings.env.lower()=="prod":
        hosts = [h.strip() for h in os.getenv("TRUSTED_HOSTS","" ).split(",") if h.strip()]
        if hosts: app.add_middleware(TrustedHostMiddleware, allowed_hosts=hosts)
        cidrs = [c.strip() for c in os.getenv("IP_ALLOWLIST","" ).split(",") if c.strip()]
        if cidrs: app.add_middleware(IPAllowlistMiddleware, cidrs=cidrs)

    # CORS
    allow = [o.strip() for o in settings.cors_allow_origins.split(",") if o.strip()]
    app.add_middleware(
        CORSMiddleware,
        allow_origins=allow,
        allow_methods=["GET","POST","OPTIONS"],
        allow_headers=["*"],
        expose_headers=["x-request-id","X-RateLimit-Limit","X-RateLimit-Remaining"],
        allow_credentials=False,
    )

    # Middlewares
    app.add_middleware(RequestIDMiddleware)
    api_key = read_api_key("API_KEY","API_KEY_FILE", default=("change-me" if settings.env!="prod" else ""), env_name="API_KEY")
    if settings.env.lower()=="prod" and (not api_key or api_key=="change-me"):
        raise RuntimeError("API_KEY is not configured for prod")
    app.add_middleware(APIKeyAuthMiddleware, api_key=api_key, header_name=settings.auth_header_name, skip=tuple(s.strip() for s in settings.skip_auth_paths.split(",") if s.strip()))
    app.add_middleware(RateLimitMiddleware, per_minute=settings.ratelimit_per_minute)

    # Metrics + access logs
    log = logging.getLogger("factsynth")
    @app.middleware("http")
    async def record_metrics(request: Request, call_next):
        start = perf_counter()
        response = await call_next(request)
        route = request.scope.get("path", request.url.path)
        dur = max(0.0, perf_counter()-start)
        try:
            REQUESTS.labels(request.method, route, str(response.status_code)).inc()
            LATENCY.labels(route).observe(dur)
        except Exception:
            pass
        try:
            rec = logging.LogRecord("factsynth", logging.INFO, __file__, 0, f"{request.method} {route}", args=(), exc_info=None)
            rec.path = route; rec.method = request.method; rec.status_code = response.status_code; rec.latency_ms = int(dur*1000)
            log.handle(rec)
        except Exception:
            pass
        return response

    install_handlers(app)
    try_enable_otel(app)

    app.include_router(api)

    @app.get("/v1/healthz")
    def healthz():
        items = [s for s in (settings.health_tcp_checks.split(",") if settings.health_tcp_checks else []) if s]
        checks = multi_tcp_check(items) if items else {}
        return {"status":"ok","checks":checks}

    @app.get("/metrics")
    def metrics():
        return Response(content=metrics_bytes(), media_type=metrics_content_type())

    return app

app = create_app()
