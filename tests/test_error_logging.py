from http import HTTPStatus
from unittest.mock import patch

from fastapi.testclient import TestClient

from factsynth_ultimate.app import create_app


def test_internal_error_logs_path_and_exception():
    app = create_app()

    @app.get("/boom")
    def boom():
        raise RuntimeError("boom")

    with TestClient(app, raise_server_exceptions=False) as client, patch(
        "factsynth_ultimate.core.errors.logger"
    ) as mock_logger:
        r = client.get("/boom", headers={"x-api-key": "change-me"})
        assert r.status_code == HTTPStatus.INTERNAL_SERVER_ERROR
        body = r.json()
        instance = body.pop("instance")
        assert instance
        assert body == {
            "type": "about:blank",
            "title": "Internal Server Error",
            "status": HTTPStatus.INTERNAL_SERVER_ERROR,
            "detail": "boom",
        }
        mock_logger.exception.assert_called_once()
        msg, path, exc = mock_logger.exception.call_args[0]
        assert path == "/boom"
        assert isinstance(exc, RuntimeError)
