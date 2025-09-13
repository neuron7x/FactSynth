import asyncio
import importlib.util
from pathlib import Path

from httpx import ASGITransport, AsyncClient
from pytest_httpx import HTTPXMock


def test_healthz(httpx_mock: HTTPXMock) -> None:
    httpx_mock.reset()

    async def _run() -> None:
        spec = importlib.util.spec_from_file_location(
            "fs_app", Path(__file__).resolve().parents[1] / "factsynth_ultimate" / "app.py"
        )
        if spec is None or spec.loader is None:
            raise ImportError("Cannot load app module")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        app = module.app
        transport = ASGITransport(app=app)
        async with AsyncClient(
            transport=transport, base_url="http://test", headers={"x-api-key": "change-me"}
        ) as ac:
            res = await ac.get("/healthz")
            assert res.status_code == 200  # noqa: S101
            assert res.json().get("status") == "ok"  # noqa: S101

    asyncio.run(_run())
