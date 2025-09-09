from __future__ import annotations

import re
from typing import Any, Iterable

import httpx
from fastapi import Depends, HTTPException, Request
from fastapi.responses import JSONResponse
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import jwt
from starlette.middleware.base import BaseHTTPMiddleware

from ..i18n import choose_language, translate
from .settings import load_settings


async def _verify_jwt(
    token: str,
    jwks_url: str | None,
    audience: str | None,
    issuer: str | None,
) -> dict[str, Any]:
    """Decode a JWT using a remote JWKS."""
    if not jwks_url:
        raise ValueError("jwks url not configured")
    async with httpx.AsyncClient(timeout=5.0) as client:
        jwks = (await client.get(jwks_url)).json()
    header = jwt.get_unverified_header(token)
    key_data = next(
        (k for k in jwks.get("keys", []) if k.get("kid") == header.get("kid")),
        None,
    )
    if not key_data:
        raise ValueError("key not found")
    return jwt.decode(
        token,
        key_data,
        algorithms=[key_data.get("alg", header.get("alg"))],
        audience=audience,
        issuer=issuer,
    )


_bearer = HTTPBearer(auto_error=False)


async def get_jwt_claims(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer),
) -> dict[str, Any]:
    """Return JWT claims if a Bearer token is supplied."""
    if credentials is None:
        return {}
    settings = load_settings()
    try:
        return await _verify_jwt(
            credentials.credentials,
            settings.oidc_jwks_url,
            settings.oidc_audience,
            settings.oidc_issuer,
        )
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=401, detail="Invalid token") from exc


class APIKeyAuthMiddleware(BaseHTTPMiddleware):
    """Authenticate via API key or JWT bearer token."""

    def __init__(
        self,
        app,
        api_key: str,
        header_name: str = "x-api-key",
        skip: Iterable[str] = ("/v1/healthz", "/metrics"),
        jwks_url: str | None = None,
        audience: str | None = None,
        issuer: str | None = None,
    ):
        super().__init__(app)
        self.api_key = api_key
        self.header_name = header_name
        self.jwks_url = jwks_url
        self.audience = audience
        self.issuer = issuer
        self.skip_exact: set[str] = set()
        patterns = []
        for s in skip:
            if s.startswith("^") and s.endswith("$"):
                patterns.append(re.compile(s))
            else:
                self.skip_exact.add(s)
        self.skip_patterns = tuple(patterns)

    async def dispatch(self, request: Request, call_next):
        path = request.url.path
        if path in self.skip_exact or any(p.fullmatch(path) for p in self.skip_patterns):
            return await call_next(request)
        provided = request.headers.get(self.header_name)
        if self.api_key and provided == self.api_key:
            return await call_next(request)
        authz = request.headers.get("authorization")
        if authz and authz.lower().startswith("bearer "):
            token = authz.split(" ", 1)[1]
            try:
                await _verify_jwt(token, self.jwks_url, self.audience, self.issuer)
                return await call_next(request)
            except Exception:  # noqa: BLE001
                pass
        lang = choose_language(request)
        title = translate(lang, "unauthorized")
        return JSONResponse(
            {"type": "about:blank", "title": title, "status": 401},
            status_code=401,
            media_type="application/problem+json",
        )
