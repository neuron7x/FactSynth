from __future__ import annotations

from fastapi import FastAPI
from prometheus_client import make_asgi_app

from factsynth.api.middleware import MetricsMiddleware
from factsynth.api.routers import feedback as feedback_router

app = FastAPI(title="FactSynth API")
app.include_router(feedback_router.router)
app.add_middleware(MetricsMiddleware)
app.mount("/metrics", make_asgi_app())
