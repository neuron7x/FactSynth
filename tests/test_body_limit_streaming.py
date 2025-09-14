from http import HTTPStatus
import tracemalloc

import pytest
from fastapi import FastAPI, Request
from httpx import ASGITransport, AsyncClient

from factsynth_ultimate.core.body_limit import BodySizeLimitMiddleware

MAX_BYTES = 2_000_000
CHUNK_SIZE = 1_000_000
EXPECTED_CHUNKS = MAX_BYTES // CHUNK_SIZE + 1


class _DummyHTTPXMock:
    def add_callback(self, handler) -> None:  # pragma: no cover - test helper
        pass


@pytest.fixture
def httpx_mock():
    return _DummyHTTPXMock()


def _make_app() -> FastAPI:
    app = FastAPI()
    app.add_middleware(BodySizeLimitMiddleware, max_bytes=MAX_BYTES)

    @app.post("/")
    async def root(request: Request) -> dict[str, int]:
        body = await request.body()
        return {"size": len(body)}

    return app


@pytest.mark.anyio
async def test_streaming_body_over_limit_stops_early() -> None:
    app = _make_app()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        count = {"chunks": 0}

        async def gen():
            chunk = b"x" * CHUNK_SIZE
            while True:
                count["chunks"] += 1
                yield chunk

        tracemalloc.start()
        r = await client.post("/", content=gen())
        _current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()

    assert r.status_code == HTTPStatus.REQUEST_ENTITY_TOO_LARGE
    assert count["chunks"] == EXPECTED_CHUNKS
    assert peak < MAX_BYTES * 2


@pytest.mark.anyio
async def test_streaming_body_at_limit_ok() -> None:
    app = _make_app()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        async def gen():
            yield b"x" * MAX_BYTES

        r = await client.post("/", content=gen())

    assert r.status_code == HTTPStatus.OK
    assert r.json()["size"] == MAX_BYTES
