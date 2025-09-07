from time import time
import asyncio
from collections import deque
from fastapi import Header, HTTPException

try:
    import jwt
except Exception:
    jwt = None

from .settings import Settings

S = Settings()

# rate limiting state
_BUCKET: dict[str, tuple[int, int]] = {}
_BUCKET_QUEUE: deque[tuple[int, str]] = deque()
_LOCK = asyncio.Lock()

async def api_key_auth(x_api_key: str | None = Header(None), authorization: str | None = Header(None)):
    """Validate API access using an API key or JWT.

    Clients may send the expected API key in the ``X-API-Key`` header or a
    bearer token in the ``Authorization`` header.  When a JWT is provided it is
    decoded using ``S.JWT_PUBLIC_KEY``/``S.JWT_ALG`` and optionally validated
    against ``S.JWT_REQUIRED_AUD``.  A mismatched audience triggers a ``403``
    ``jwt_audience_mismatch`` error while any other JWT issue results in ``401``
    ``invalid_jwt``.
    """
    if S.API_KEY and x_api_key == S.API_KEY:
        return
    if authorization and authorization.startswith("Bearer ") and S.JWT_PUBLIC_KEY and jwt:
        token = authorization.split(" ", 1)[1]
        try:
            payload = jwt.decode(token, S.JWT_PUBLIC_KEY, algorithms=[S.JWT_ALG])
            if S.JWT_REQUIRED_AUD and S.JWT_REQUIRED_AUD not in (payload.get("aud") or []):
                raise HTTPException(status_code=403, detail="jwt_audience_mismatch")
            return
        except HTTPException:
            raise
        except Exception:
            raise HTTPException(status_code=401, detail="invalid_jwt")
    raise HTTPException(status_code=401, detail="unauthorized")

async def rate_limiter(x_api_key: str | None = Header(None)):
    """Enforce a token bucket rate limit keyed by ``X-API-Key``.

    Each key maintains a bucket of ``S.RATE_MAX_REQ`` tokens for a window of
    ``S.RATE_WINDOW_SEC`` seconds.  Tokens are replenished proportionally to the
    elapsed time using ``cap * delta // window`` where ``delta`` is the number of
    seconds since the last request.  When a bucket is empty a ``429
    rate_limited`` error is raised.
    """
    key = x_api_key or "anon"
    cap, window = S.RATE_MAX_REQ, S.RATE_WINDOW_SEC
    now = int(time())
    async with _LOCK:
        # purge expired keys
        expiry = now - window
        while _BUCKET_QUEUE and _BUCKET_QUEUE[0][0] <= expiry:
            ts_old, k_old = _BUCKET_QUEUE.popleft()
            entry = _BUCKET.get(k_old)
            if entry and entry[1] <= expiry and entry[1] == ts_old:
                _BUCKET.pop(k_old, None)

        tok, ts = _BUCKET.get(key, (cap, now))
        if now > ts:
            delta = now - ts
            tok = min(cap, tok + (cap * delta // window))
            ts = now
        if tok <= 0:
            raise HTTPException(status_code=429, detail="rate_limited")
        _BUCKET[key] = (tok - 1, ts)
        _BUCKET_QUEUE.append((ts, key))
