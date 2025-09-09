import os
from http import HTTPStatus
from unittest.mock import patch

import httpx
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from fastapi.testclient import TestClient
from jose import jwt
from jose.utils import base64url_encode

from factsynth_ultimate.app import create_app


def test_auth_required() -> None:
    with patch.dict(os.environ, {"API_KEY": "secret"}), TestClient(create_app()) as client:
        url = "/v1/score"
        assert client.post(url, json={"text": "x"}).status_code == HTTPStatus.UNAUTHORIZED
        assert (
            client.post(url, headers={"x-api-key": "secret"}, json={"text": "x"}).status_code
            == HTTPStatus.OK
        )


def test_score_values() -> None:
    with patch.dict(os.environ, {"API_KEY": "secret"}), TestClient(create_app()) as client:
        r = client.post(
            "/v1/score",
            headers={"x-api-key": "secret"},
            json={"text": "hello world", "targets": ["hello", "x"]},
        )
        assert r.status_code == HTTPStatus.OK
        s = r.json()["score"]
        assert 0.0 <= s <= 1.0


def test_jwt_auth(monkeypatch) -> None:
    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    priv = key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    )
    numbers = key.public_key().public_numbers()
    n = base64url_encode(numbers.n.to_bytes((numbers.n.bit_length() + 7) // 8, "big")).decode()
    e = base64url_encode(numbers.e.to_bytes((numbers.e.bit_length() + 7) // 8, "big")).decode()
    jwks = {
        "keys": [
            {
                "kty": "RSA",
                "kid": "test",
                "use": "sig",
                "alg": "RS256",
                "n": n,
                "e": e,
            }
        ]
    }

    token = jwt.encode(
        {"sub": "alice", "aud": "aud", "iss": "iss"},
        priv,
        algorithm="RS256",
        headers={"kid": "test"},
    )

    async def fake_get(self, url, *args, **kwargs):  # noqa: D401
        class Resp:
            def json(self_inner):
                return jwks

        return Resp()

    monkeypatch.setattr(httpx.AsyncClient, "get", fake_get)
    env = {
        "API_KEY": "secret",
        "OIDC_JWKS_URL": "https://example/jwks",
        "OIDC_AUDIENCE": "aud",
        "OIDC_ISSUER": "iss",
    }
    with patch.dict(os.environ, env), TestClient(create_app()) as client:
        r = client.post(
            "/v1/score",
            headers={"Authorization": f"Bearer {token}"},
            json={"text": "hello"},
        )
        assert r.status_code == HTTPStatus.OK
