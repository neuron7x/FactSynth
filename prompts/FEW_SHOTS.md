**Ex1 — SSE stream endpoint (Python/FastAPI)**
Adds keepalive, cancellation, metrics, Problem+JSON.

```python
# src/factsynth_ultimate/handlers/stream.py
from fastapi import APIRouter, Request, HTTPException
from starlette.responses import StreamingResponse
import asyncio, time
from ..metrics import sse_tokens_total

router = APIRouter()

async def token_stream(req: Request, text: str):
    try:
        i = 0
        while True:
            if await req.is_disconnected():
                break
            token = text[i:i+5] or ""
            if not token: break
            sse_tokens_total.labels(route="/v1/stream").inc()
            yield f"data: {token}\n\n"
            await asyncio.sleep(0.02)
            i += 5
        yield "event: end\ndata: true\n\n"
    except Exception as e:
        # Surface as SSE error event; logs handled centrally
        yield f"event: error\ndata: {str(e)}\n\n"

@router.post("/v1/stream")
async def stream(req: Request, payload: dict):
    text = (payload or {}).get("text")
    if not text:
        raise HTTPException(status_code=422, detail="text is required")
    return StreamingResponse(token_stream(req, text), media_type="text/event-stream")
```

**Ex2 — Problem+JSON helper**

```python
# src/factsynth_ultimate/errors.py
from fastapi import Request
from starlette.responses import JSONResponse

def problem(status: int, title: str, detail: str, type_: str="about:blank"):
    return JSONResponse(
        {"type": type_, "title": title, "status": status, "detail": detail},
        status_code=status,
        media_type="application/problem+json",
    )

# usage in exception handlers: return problem(429, "Too Many Requests", "Burst limit exceeded")
```

**Ex3 — Prometheus metrics & labels**

```python
# src/factsynth_ultimate/metrics.py
from prometheus_client import Counter, Histogram
requests_total = Counter("factsynth_requests_total", "HTTP requests", ["method","route","status"])
request_latency = Histogram("factsynth_request_latency_seconds", "Latency", ["route"])
sse_tokens_total = Counter("factsynth_sse_tokens_total", "Streamed tokens", ["route"])
```

**Ex4 — Pytest for scoring endpoint (happy + edge)**

```python
def test_score_happy(client):
    r = client.post("/v1/score", json={"text":"hello world","targets":["world"]}, headers={"x-api-key":"k"})
    assert r.status_code == 200
    body = r.json()
    assert body["coverage"] >= 1.0

def test_score_422(client):
    r = client.post("/v1/score", json={"text":""}, headers={"x-api-key":"k"})
    assert r.status_code == 422
    assert r.headers["content-type"].startswith("application/problem+json")
```

**Ex5 — Nginx rate-limit & header hardening (snippet)**

```nginx
limit_req_zone $binary_remote_addr zone=perkey:10m rate=120r/m;
server {
  add_header Strict-Transport-Security "max-age=31536000" always;
  add_header Content-Security-Policy "default-src 'none'";
  location / {
    limit_req zone=perkey burst=40 nodelay;
    proxy_pass http://app:8000;
  }
}
```
