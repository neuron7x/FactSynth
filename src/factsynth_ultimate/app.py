from __future__ import annotations
from time import perf_counter
from fastapi import FastAPI, Response, Request
from .core.settings import Settings, load_settings
from .core.metrics import metrics_bytes, metrics_content_type, REQUESTS, LATENCY
from .core.auth import APIKeyAuthMiddleware
from .api.routers import api_router


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or load_settings()
    app = FastAPI(title="FactSynth Ultimate API", version="1.0.0")
    app.add_middleware(APIKeyAuthMiddleware, api_key=settings.api_key)

    @app.middleware("http")
    async def record_metrics(request: Request, call_next):
        start = perf_counter()
        response = await call_next(request)
        route = request.scope.get("path", request.url.path)
        try:
            REQUESTS.labels(request.method, route, str(response.status_code)).inc()
            LATENCY.labels(route).observe(max(0.0, perf_counter() - start))
        except Exception:
            # Metrics are best-effort
            pass
        return response

    app.include_router(api_router)

    @app.get("/v1/healthz")
    def healthz():
        return {"status": "ok"}

    @app.get("/metrics")
    def metrics():
        data = metrics_bytes()
        return Response(content=data, media_type=metrics_content_type())

    return app

app = create_app()


def main() -> None:
    import uvicorn
    settings = load_settings()
    uvicorn.run(create_app(settings), host="0.0.0.0", port=8000)
