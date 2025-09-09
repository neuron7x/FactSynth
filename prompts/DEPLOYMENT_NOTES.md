# Deployment Notes

## Versioning

- Prompt package v1.2.0 (semver), tracks FactSynth API surface.

## Usage Checklist

1. Paste SYSTEM into your orchestrator.
2. Use templates (Create/Improve/Convert/Evaluate/Deploy).
3. Enforce output contract in PR bot (regex gates).
4. Track KPIs (lint/type/coverage/latency) in CI status.

## Monitoring

- Expose and watch: `factsynth_requests_total{method,route,status}`, `factsynth_request_latency_seconds_bucket{route}`, `factsynth_sse_tokens_total`.

## Rollback

- Keep last N images; use blue/green or canary; feature flags for new endpoints; DB migrations reversible.

## Extension Points

- Add “Security Profiler” sub-persona for headers/CSP.
- Add “Perf Surgeon” for hotspot profiling scripts.
