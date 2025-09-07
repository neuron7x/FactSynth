# FactSynth Ultimate Pro — 1.0.1 (2025-09-07)

## What’s new
- ✅ Pydantic validation for all requests
- ✅ Security: HSTS, CSP, IP allowlist (CIDR), body size limit, no wildcard CORS in prod
- ✅ Observability: business metrics (`factsynth_scoring_seconds`, `factsynth_sse_tokens_total`)
- ✅ Batch scoring & webhooks with retries (httpx)
- ✅ SSE limits & WebSocket endpoint
- ✅ Postman collection, troubleshooting, changelog

## Quickstart
```bash
python -m venv .venv && . .venv/bin/activate
pip install -U pip && pip install -e .[dev,ops]
export API_KEY=change-me   # use secret file or Vault in prod!
uvicorn factsynth_ultimate.app:app --host 0.0.0.0 --port 8000
```
