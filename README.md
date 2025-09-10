# FactSynth Ultimate Pro — 1.0.3 (2025-09-07)
[![OpenAPI docs](https://img.shields.io/badge/docs-openapi-blue)](https://neuron7x.github.io/FactSynth/openapi/)

Secure, observable **FastAPI** service for intent reflection, scoring, extractive generation, streaming (SSE/WebSocket), and a toy GLRTPM pipeline.

> **UA коротко:** продакшн-готовий API з автентифікацією за ключем, метриками Prometheus, стримінгом SSE/WS, фільтрацією шуму, батч-скорингом і Problem+JSON помилками.

[🇺🇦 Повна документація українською](README_UA.md)

---

## Contents

* [Features](#features)
* [Quickstart](#quickstart)
* [Endpoints](#endpoints)
* [Auth & Rate Limits](#auth--rate-limits)
* [IP Allowlist](#ip-allowlist)
* [Errors (Problem+JSON)](#errors-problemjson)
* [Observability](#observability)
* [Configuration](#configuration)
* [Docker](#docker)
* [Postman & OpenAPI](#postman--openapi)
* [Testing](#testing)
* [Prompt Pack](#prompt-pack)
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

## Конфігурація виконання

Генератор приймає обʼєкт [`FSUConfig`](src/factsynth_ultimate/config.py), який
визначає мову, довжину та інші правила формату. Docstring класу описує призначення
кожного поля та значення за замовчуванням, тож ви можете змінювати їх перед
викликом `generate_insight` чи зверненням до API.

### Formatting helpers

The module [`formatting`](src/factsynth_ultimate/formatting.py) provides small
utilities for cleaning free-form text.  Use `sanitize()` to strip headings,
lists or emojis, `ensure_period()` to finalise sentences and `fit_length()` to
pad or trim a fragment to an exact word count.

## Bootstrap повного продукту

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

## IP Allowlist

Restrict access by client IP. Set `IP_ALLOWLIST` to a comma-separated list of CIDRs:

```bash
export IP_ALLOWLIST="10.0.0.0/8,192.168.1.0/24"
```

Requests from other addresses receive `403 Forbidden`. Health (`/v1/healthz`) and metrics (`/metrics`) always bypass the check. Leaving the variable empty disables the allowlist.

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

**Tracing (OpenTelemetry)**

Install with OTEL extras and configure standard env vars (for example `OTEL_EXPORTER_OTLP_ENDPOINT`). The app calls `try_enable_otel()` on startup and instruments FastAPI if dependencies are available.

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

For deployment, start from the provided `.env.production` file next to `.env.example` and adjust the values to match your environment.

Vault support (optional): set `VAULT_ADDR`, `VAULT_TOKEN`, `VAULT_PATH` (reads `API_KEY`).

---

## Docker

The container uses Python 3.12 with `tini`, runs as a non-root `appuser`,
declares a writable `/tmp` volume to support a read-only root filesystem, and
exposes a default `UVICORN_WORKERS` environment variable. The server runs with
proxy header support and a 30-second keep-alive timeout.

Example `Dockerfile`:

```dockerfile
FROM python:3.12-slim
RUN apt-get update && apt-get install -y --no-install-recommends tini \
    && rm -rf /var/lib/apt/lists/*
WORKDIR /app
COPY . /app
RUN pip install -U pip && pip install -e .[ops]
ENV UVICORN_WORKERS=2
RUN useradd -m appuser && chown -R appuser:appuser /app
USER appuser
EXPOSE 8000
VOLUME ["/tmp"]
ENTRYPOINT ["/usr/bin/tini","--"]
CMD [
  "uvicorn",
  "factsynth_ultimate.app:app",
  "--host",
  "0.0.0.0",
  "--port",
  "8000",
  "--proxy-headers",
  "--timeout-keep-alive",
  "30"
]
```

Build & run:

```bash
docker build -t factsynth:1.0.3 .
docker run -e API_KEY=change-me -p 8000:8000 factsynth:1.0.3
```

## Helm

```bash
helm registry login ghcr.io -u <user> --password <token>
helm upgrade --install factsynth oci://ghcr.io/<owner>/charts/factsynth \
  -f values-prod.yaml \
  --set secrets.apiKey=change-me \
  --set ingress.enabled=true \
  --set ingress.host=factsynth.local
```

---

## Postman & OpenAPI

* Docs: [OpenAPI documentation](https://neuron7x.github.io/FactSynth/openapi/)
* OpenAPI: `openapi/openapi.yaml`
* Postman: `openapi/postman/FactSynth.postman_collection.json`

---

## Testing
### Test Setup

The test suite requires the following packages:

* `pytest`
* `pytest-cov`
* `httpx`
* `uvicorn`
* `schemathesis`
* `websockets`
* `jax`
* `diffrax`
* `numpy`

Install them via extras or the helper script:

```bash
pip install -e .[dev,isr,numpy]
# or
./scripts/setup-tests.sh
```

### Running Tests

```bash
pytest -q
pytest -q --cov=src --cov-report=term-missing
```

---

## Prompt Pack

See [docs/PromptPack.md](docs/PromptPack.md) for a production-ready system prompt, task templates, few-shot examples, and the Golden-12 test set.

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

---

**Incubation Pack merge note**: додано workflow `.github/workflows/release-artifact.yml`, каталог `charts/factsynth`, `tests/test_openapi_contract.py`, `docs/INCUBATION_CO_DEV_UA.md`, Makefile-таргети. Helm використовує `ghcr.io/neuron7x/factsynth` і `.Chart.AppVersion` = версія з `pyproject.toml`.
