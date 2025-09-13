# Security and Authorization

FactSynth protects its endpoints with API key headers, optional IP and CORS allowlists, and Redis-backed rate limits. Errors follow the [RFC 9457](https://www.rfc-editor.org/rfc/rfc9457) Problem+JSON format.

## API key authentication

Each request must include an API key in the `x-api-key` header (configurable via `AUTH_HEADER_NAME`). The key value comes from the `API_KEY` environment variable or `API_KEY_FILE`.

### curl example

```bash
curl -s -X POST http://localhost:8000/v1/generate \
  -H "x-api-key: ${API_KEY}" \
  -H "content-type: application/json" \
  -d '{"prompt": "Extract facts about water."}'
```

### wscat example

```bash
wscat -c ws://localhost:8000/ws/stream -H "x-api-key: $API_KEY"
```

## IP allowlist

Set `IP_ALLOWLIST` to a comma-separated list of CIDR ranges. Requests from other addresses receive a 403 response.

## CORS allowlist

Cross-origin requests are denied unless an origin appears in `CORS_ALLOW_ORIGINS`. Provide a comma-separated list or `*` to allow any origin.

## Problem+JSON errors

Unauthorized, forbidden, and throttled requests return Problem+JSON payloads:

### 401 Unauthorized

```json
{
  "type": "about:blank",
  "title": "Unauthorized",
  "status": 401,
  "detail": "Invalid or missing API key",
  "trace_id": "..."
}
```

### 403 Forbidden

```json
{
  "type": "about:blank",
  "title": "Forbidden",
  "status": 403,
  "detail": "IP 203.0.113.10 not allowed",
  "trace_id": "..."
}
```

### 429 Too Many Requests

```json
{
  "type": "about:blank",
  "title": "Too Many Requests",
  "status": 429,
  "detail": "Request rate limit exceeded",
  "trace_id": "..."
}
```

## Rate limiting

Requests are limited per API key, IP address, and organization within a sliding one‑minute window. Limits default to 120 requests and are set with `RATE_LIMIT_PER_KEY`, `RATE_LIMIT_PER_IP`, and `RATE_LIMIT_PER_ORG`. Exceeding a limit returns a 429 response and includes `Retry-After` and standard `X-RateLimit-*` headers. Redis connection is configured via `RATE_LIMIT_REDIS_URL`.

## Environment variables

| Variable | Description |
| --- | --- |
| `AUTH_HEADER_NAME` | Name of the HTTP header carrying the API key (default `x-api-key`). |
| `API_KEY`/`API_KEY_FILE` | Value or file path for the required API key. |
| `IP_ALLOWLIST` | Comma-separated CIDR blocks permitted to access the service. |
| `CORS_ALLOW_ORIGINS` | Comma-separated origins allowed for cross-origin requests. |
| `RATE_LIMIT_REDIS_URL` | Redis URL backing the rate limiter. |
| `RATE_LIMIT_PER_KEY` | Requests per minute allowed per API key (default 120). |
| `RATE_LIMIT_PER_IP` | Requests per minute allowed per IP address (default 120). |
| `RATE_LIMIT_PER_ORG` | Requests per minute allowed per `x-organization` header (default 120). |
