# Validation Report

**Assumptions**

- Primary runtime: Python 3.12, FastAPI, uvicorn; Prometheus metrics enabled.
- Auth via `x-api-key`; some routes bypass auth; rate limit ~120 req/min; SSE/WS supported; Problem+JSON used.
- You want standardized output structure and CI-friendly snippets.

**Risks & Mitigations**

- _Drifting repo details_: isolate any repo-specific claims; verify before release (**Verification Required** tag).
- _Streaming pitfalls_: add keepalive, cancellation, backpressure tests.
- _Security_: enforce headers, IP allowlist, body size limit; pin deps; secret via env/file/Vault (documented in README).

**Pass/Fail Notes (Golden-12 dry run)**

- Prompts cover all categories; examples compile; tests illustrate Problem+JSON, SSE, metrics.
- Lint/type hints assumed strict; adjust mypy config if project differs.

**Recommended Guardrails**

- CI gates: ruff + mypy strict + coverage ≥90% on diffs.
- Pre-merge checklist: security review (headers, CORS), perf smoke (wrk autocannon), error budget.
