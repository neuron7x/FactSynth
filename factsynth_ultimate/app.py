from fastapi import FastAPI
from fastapi.responses import JSONResponse
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

from .config import settings
from .infra.db import init_db
from .logging import configure_logging
from .routers.claims import limiter
from .routers.claims import router as claims_router

configure_logging()
app = FastAPI(title=settings.app_name, version=settings.app_version)
app.state.limiter = limiter
app.add_middleware(SlowAPIMiddleware)


@app.on_event("startup")
async def _startup() -> None:
    await init_db()


@app.get("/healthz")
def health() -> dict:
    return {"status": "ok"}


@app.get("/readyz")
def ready() -> JSONResponse:
    return JSONResponse({"ready": True})


app.include_router(claims_router)


@app.exception_handler(RateLimitExceeded)
def _rate_limit_handler(request, exc):  # type: ignore[no-untyped-def]
    return JSONResponse({"detail": "rate limit exceeded"}, status_code=429)
