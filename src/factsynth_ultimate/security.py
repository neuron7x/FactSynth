from time import time
from fastapi import Header, HTTPException

try:
    import jwt
except Exception:  # pragma: no cover - optional dependency
    jwt = None

from .settings import Settings


class Security:
    """Collection of security dependencies parameterized by :class:`Settings`."""

    def __init__(self, settings: Settings):
        self.settings = settings
        self._bucket: dict[str, tuple[int, int]] = {}

    async def api_key_auth(self, x_api_key: str | None = Header(None), authorization: str | None = Header(None)):
        S = self.settings
        if S.API_KEY and x_api_key == S.API_KEY:
            return
        if authorization and authorization.startswith("Bearer ") and S.JWT_PUBLIC_KEY and jwt:
            token = authorization.split(" ", 1)[1]
            try:
                payload = jwt.decode(token, S.JWT_PUBLIC_KEY, algorithms=[S.JWT_ALG])
                aud = payload.get("aud") or []
                if S.JWT_REQUIRED_AUD and S.JWT_REQUIRED_AUD not in aud:
                    raise HTTPException(status_code=403, detail="jwt_audience_mismatch")
                return
            except Exception:
                raise HTTPException(status_code=401, detail="invalid_jwt")
        raise HTTPException(status_code=401, detail="unauthorized")

    async def rate_limiter(self, x_api_key: str | None = Header(None)):
        S = self.settings
        key = x_api_key or "anon"
        cap, window = S.RATE_MAX_REQ, S.RATE_WINDOW_SEC
        now = int(time())
        tok, ts = self._bucket.get(key, (cap, now))
        if now > ts:
            delta = now - ts
            tok = min(cap, tok + (cap * delta // window))
            ts = now
        if tok <= 0:
            raise HTTPException(status_code=429, detail="rate_limited")
        self._bucket[key] = (tok - 1, ts)
