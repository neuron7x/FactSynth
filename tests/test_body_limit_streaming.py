from http import HTTPStatus

import pytest
from fastapi import FastAPI, Request
from httpx import ASGITransport, AsyncClient

from factsynth_ultimate.core.body_limit import BodySizeLimitMiddleware

MAX_BYTES = 1024
CHUNK = b"x" * 512

def create_app() -> FastAPI:
    app = FastAPI()
    app.add_middleware(BodySizeLimitMiddleware, max_bytes=MAX_BYTES)

    @app.post("/")
    async def root(request: Request):
        data = await request.body()
        return {"received": len(data)}

    return app

@pytest.mark.anyio
async def test_streaming_request_exceeds_limit() -> None:
    app = create_app()
    calls = 0
    sent = 0
    total_chunks = 5  # total 2560 bytes

    async def gen():
        nonlocal calls, sent
        for _ in range(total_chunks):
            calls += 1
            sent += len(CHUNK)
            yield CHUNK

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post("/", content=gen())

    assert resp.status_code == HTTPStatus.REQUEST_ENTITY_TOO_LARGE
    assert calls < total_chunks  # server stopped reading early
    assert sent <= MAX_BYTES + len(CHUNK)

@pytest.mark.anyio
async def test_streaming_request_at_limit_ok() -> None:
    app = create_app()
    calls = 0
    sent = 0
    total_chunks = 2  # total 1024 bytes equals limit

    async def gen():
        nonlocal calls, sent
        for _ in range(total_chunks):
            calls += 1
            sent += len(CHUNK)
            yield CHUNK

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post("/", content=gen())

    assert resp.status_code == HTTPStatus.OK
    assert calls == total_chunks
    assert sent == MAX_BYTES
