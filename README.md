# FactSynth Ultimate Pro — 1.0.3 (2025-09-07)

Secure, observable **FastAPI** service for intent reflection, scoring, extractive generation, streaming (SSE/WebSocket), and a toy GLRTPM pipeline.

> **UA коротко:** продакшн-готовий API з автентифікацією за ключем, метриками Prometheus, стримінгом SSE/WS, фільтрацією шуму, батч-скорингом і Problem+JSON помилками.

[🇺🇦 Повна документація українською](README_UA.md)

---

## Contents

* [Features](#features)
* [Quickstart](#quickstart)
* [Endpoints](#endpoints)
* [Auth & Rate Limits](#auth--rate-limits)
* [Errors (Problem+JSON)](#errors-problemjson)
* [Observability](#observability)
* [Configuration](#configuration)
* [Docker](#docker)
* [Postman & OpenAPI](#postman--openapi)
* [Testing](#testing)
* [Security Hardening](#security-hardening)
* [Roadmap](#roadmap)
* [License](#license)

---

## Features

* **API-key auth** via `x-api-key` header (skips `/v1/healthz`, `/metrics`, `/v1/version`).
* **Rate limiting** (default 120 req/min) with `X-RateLimit-*` headers.
* **SSE & WebSocket streaming** for token-like updates.
* **Extractive generation**: `title`, `summary`, `keywords` from input text.
* **Scoring heuristics**: coverage, length saturation, alpha density, entropy; gibberish gate.
* **Noise filtering**: strips HTML/URLs/emails, dedupes targets, stops UA/EN stopwords.
* **Batch scoring** & optional **webhook callbacks** (with retries).
* **Problem+JSON** structured errors.
* **Prometheus metrics** + **JSON logs**; optional OpenTelemetry.
* **HSTS/CSP** security headers; body size limit; optional IP allowlist.

---

## Quickstart

```bash
python -m venv .venv && . .venv/bin/activate
pip install -U pip && pip install -e .[dev,ops]
export API_KEY=change-me        # use secret file or Vault in prod
uvicorn factsynth_ultimate.app:app --host 0.0.0.0 --port 8000
```

Health:

```bash
curl -s http://127.0.0.1:8000/v1/healthz
```

---

## Endpoints

### Version

```bash
curl -s http://127.0.0.1:8000/v1/version
```

### Intent Reflector

```bash
curl -s -H 'x-api-key: change-me' \
  -H 'content-type: application/json' \
  -d '{"intent":"Summarize Q4 plan","length":48}' \
  http://127.0.0.1:8000/v1/intent_reflector
```

### Score

```bash
curl -s -H 'x-api-key: change-me' \
  -H 'content-type: application/json' \
  -d '{"text":"hello world","targets":["hello"]}' \
  http://127.0.0.1:8000/v1/score
```

### Batch Score

```bash
curl -s -H 'x-api-key: change-me' \
  -H 'content-type: application/json' \
  -d '{"items":[{"text":"a"},{"text":"hello doc","targets":["doc"]}]}' \
  http://127.0.0.1:8000/v1/score/batch
```

### SSE Stream

```bash
curl -N -H 'x-api-key: change-me' \
  -H 'content-type: application/json' \
  -d '{"text":"stream this text"}' \
  http://127.0.0.1:8000/v1/stream
```

### WebSocket Stream

```
WS /ws/stream
Header: x-api-key: change-me
Send: "your text"
Recv: {"t":"token"...} ... {"end":true}
```

### GLRTPM Pipeline (toy)

```bash
curl -s -H 'x-api-key: change-me' \
  -H 'content-type: application/json' \
  -d '{"text":"pipeline test"}' \
  http://127.0.0.1:8000/v1/glrtpm/run
```

### Generate (title/summary/keywords)

```bash
curl -s -H 'x-api-key: change-me' \
  -H 'content-type: application/json' \
  -d '{"text":"Long text here","max_len":300,"max_sentences":2,"include_score":true}' \
  http://127.0.0.1:8000/v1/generate
```

### Metrics

```bash
curl -s http://127.0.0.1:8000/metrics
```

---

## Auth & Rate Limits

* API key sources: `API_KEY_FILE` → Vault → `API_KEY` → default `change-me` (dev only)
* Auth: `x-api-key: <your-secret>`
* Default skip list (no auth): `/v1/healthz`, `/metrics`, `/v1/version`
* Rate limit: `RATE_LIMIT_PER_MIN` (default **120**) per API key / client IP
* Response headers:

  * `X-RateLimit-Limit`
  * `X-RateLimit-Remaining`
  * `Retry-After` on `429`

---

## Errors (Problem+JSON)

All errors use `application/problem+json`:

```json
{
  "type": "about:blank",
  "title": "Validation Failed",
  "status": 422,
  "detail": "...",
  "trace_id": "request-id"
}
```

---

## Observability

**Prometheus metrics**

* `factsynth_requests_total{method,route,status}`
* `factsynth_request_latency_seconds_bucket{route}`
* `factsynth_scoring_seconds_bucket`
* `factsynth_sse_tokens_total`
* `factsynth_generation_seconds_bucket`

Grafana example dashboard: `grafana/dashboards/factsynth-overview.json`

**Logs**

* JSON lines with fields: `ts,lvl,msg,logger,request_id,path,method,status_code,latency_ms`

**Tracing (optional)**

* Install `.[otel]` extras and set OTEL envs; auto-instrumentation via FastAPI.

---

## Configuration

Environment variables (examples):

* `ENV` = `dev`|`prod`
* `API_KEY` or **file** via `API_KEY_FILE`
* `AUTH_HEADER_NAME` (default `x-api-key`)
* `SKIP_AUTH_PATHS` (CSV; default `/v1/healthz,/metrics,/v1/version`)
* `CORS_ALLOW_ORIGINS` (CSV; default `*` in dev)
* `HTTPS_REDIRECT` = `1` to force HTTPS
* `TRUSTED_HOSTS` (CSV; prod only)
* `IP_ALLOWLIST` (CIDR CSV; prod only)
* `MAX_BODY_BYTES` (default `2000000`)
* `RATE_LIMIT_PER_MIN` (default `120`)
* `HEALTH_TCP_CHECKS` (CSV like `127.0.0.1:5432,[::1]:6379`)

Vault support (optional): set `VAULT_ADDR`, `VAULT_TOKEN`, `VAULT_PATH` (reads `API_KEY`).

---

## Docker

Example `Dockerfile`:

```dockerfile
FROM python:3.12-slim
WORKDIR /app
COPY . /app
RUN pip install -U pip && pip install -e .[ops]
ENV UVICORN_WORKERS=2
EXPOSE 8000
CMD ["uvicorn", "factsynth_ultimate.app:app", "--host", "0.0.0.0", "--port", "8000"]
```

Build & run:

```bash
docker build -t factsynth:1.0.3 .
docker run -e API_KEY=change-me -p 8000:8000 factsynth:1.0.3
```

---

## Postman & OpenAPI

* OpenAPI: `openapi/openapi.yaml`
* Postman: `openapi/postman/FactSynth.postman_collection.json`

---

## Testing

```bash
pytest -q
pytest -q --cov=src --cov-report=term-missing
```

---

## Security Hardening

* Use real secrets (Vault or `API_KEY_FILE`), **never** `change-me` in prod.
* Set `ENV=prod`, `HTTPS_REDIRECT=1`, enable reverse proxy TLS termination.
* Configure `TRUSTED_HOSTS`, `CORS_ALLOW_ORIGINS` (exact origins), `IP_ALLOWLIST` if needed.
* Keep `MAX_BODY_BYTES` reasonable; front with WAF / CDN where applicable.

---

## Roadmap

* Pluggable scoring backends (LLM/semantic coverage)
* Rich Web UI (admin + live metrics)
* JWT/OIDC alternative auth
* Distributed cache (Redis) for heavy pipelines

---

## License

[MIT](./LICENSE)
