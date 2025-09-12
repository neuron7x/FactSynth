# Production Runbook

This runbook outlines baseline settings for running FactSynth in a production container.

## Resource limits

- **CPU:** request 500m, limit 1 vCPU
- **Memory:** request 512Mi, limit 1Gi

## Uvicorn workers

Set `UVICORN_WORKERS` to the number of available CPU cores (default 2).  Each worker handles independent connections; do not exceed memory limits.

## Timeouts

- `--timeout-keep-alive 30` to drop idle connections.
- Upstream proxies should enforce a request timeout of 60s.

## ulimit recommendations

Ensure sufficient file descriptors for concurrent clients:

```bash
ulimit -n 4096
```

Adjust process limits as needed:

```bash
ulimit -u 1024
```

