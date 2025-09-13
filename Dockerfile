# syntax=docker/dockerfile:1

FROM python:3.12-slim@sha256:31551bd80310d95ed82a4a14dba8c908c85098f07457e8a5b6a946385cfd86c8 AS builder
WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1
RUN apt-get update && apt-get install -y --no-install-recommends build-essential \
    && rm -rf /var/lib/apt/lists/*
COPY pyproject.toml requirements.lock README.md LICENSE ./
RUN pip install --upgrade pip \
    && pip install --prefix=/install --require-hashes -r requirements.lock
COPY src ./src
RUN pip install --prefix=/install .[ops] uvloop --no-deps

FROM python:3.12-slim@sha256:31551bd80310d95ed82a4a14dba8c908c85098f07457e8a5b6a946385cfd86c8 AS runtime
WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    UVICORN_WORKERS=2 \
    UVICORN_TIMEOUT_KEEP_ALIVE=30 \
    UVICORN_TIMEOUT_GRACEFUL_SHUTDOWN=15 \
    HEALTHCHECK_CONNECT_TIMEOUT=2 \
    HEALTHCHECK_TIMEOUT=5
RUN apt-get update && apt-get install -y --no-install-recommends tini curl \
    && rm -rf /var/lib/apt/lists/* \
    && useradd -m appuser
COPY --from=builder /install /usr/local
COPY --chown=appuser:appuser pyproject.toml requirements.lock README.md LICENSE ./
USER appuser
EXPOSE 8000
VOLUME ["/tmp"]
HEALTHCHECK --interval=30s --start-period=5s --retries=3 CMD curl -fsS --connect-timeout ${HEALTHCHECK_CONNECT_TIMEOUT} --max-time ${HEALTHCHECK_TIMEOUT} http://localhost:8000/v1/healthz || exit 1
ENTRYPOINT ["/usr/bin/tini","--"]
CMD ["sh","-c","uvicorn factsynth_ultimate.app:app --host 0.0.0.0 --port 8000 --proxy-headers --timeout-keep-alive ${UVICORN_TIMEOUT_KEEP_ALIVE} --timeout-graceful-shutdown ${UVICORN_TIMEOUT_GRACEFUL_SHUTDOWN}"]
