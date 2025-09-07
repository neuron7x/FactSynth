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
    if S.API_KEY and x_api_key == S.API_KEY:
        return
    if authorization and authorization.startswith("Bearer ") and S.JWT_PUBLIC_KEY and jwt:
        token = authorization.split(" ",1)[1]
        try:
            payload = jwt.decode(token, S.JWT_PUBLIC_KEY, algorithms=[S.JWT_ALG])
            if S.JWT_REQUIRED_AUD and S.JWT_REQUIRED_AUD not in (payload.get("aud") or []):
                raise HTTPException(status_code=403, detail="jwt_audience_mismatch")
            return
        except Exception:
            raise HTTPException(status_code=401, detail="invalid_jwt")
    raise HTTPException(status_code=401, detail="unauthorized")

async def rate_limiter(x_api_key: str | None = Header(None)):
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
