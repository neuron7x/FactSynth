import os
from http import HTTPStatus
from importlib import reload
from unittest.mock import patch

from fastapi.testclient import TestClient

from factsynth_ultimate.app import create_app
from factsynth_ultimate.core import settings as settings_module

ALLOWED_BODY = {"text": "ok"}


def test_ip_allowlist_allows_request():
    env = {"API_KEY": "secret", "IP_ALLOWLIST": "1.2.3.0/24"}
    with patch.dict(os.environ, env):
        reload(settings_module)
        app = create_app()
        with TestClient(app, client=("1.2.3.4", 50000)) as client:
            r = client.post("/v1/score", headers={"x-api-key": "secret"}, json=ALLOWED_BODY)
            assert r.status_code == HTTPStatus.OK
    reload(settings_module)


def test_ip_allowlist_blocks_request():
    env = {"API_KEY": "secret", "IP_ALLOWLIST": "1.2.3.0/24"}
    with patch.dict(os.environ, env):
        reload(settings_module)
        app = create_app()
        with TestClient(app, client=("5.6.7.8", 50000)) as client:
            r = client.post("/v1/score", headers={"x-api-key": "secret"}, json=ALLOWED_BODY)
            assert r.status_code == HTTPStatus.FORBIDDEN
    reload(settings_module)
