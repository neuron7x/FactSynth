# syntax=docker/dockerfile:1

FROM python:3.12-slim@sha256:a2dd6679f8a13a533f44782cd31584d4ca4ec7170c84e7e726dc9cc3f862ed42 AS build
WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
RUN apt-get update && apt-get install -y --no-install-recommends build-essential=12.9 \
    && rm -rf /var/lib/apt/lists/*
COPY pyproject.toml requirements.lock README.md LICENSE ./
RUN pip install -U pip \
    && pip install --require-hashes -r requirements.lock \
    && pip install .[dev,ops] --no-deps
COPY src ./src

FROM python:3.12-slim@sha256:a2dd6679f8a13a533f44782cd31584d4ca4ec7170c84e7e726dc9cc3f862ed42
WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 UVICORN_WORKERS=2
RUN apt-get update && apt-get install -y --no-install-recommends tini=0.19.0-1 curl=7.88.1-10+deb12u14 \
    && rm -rf /var/lib/apt/lists/*
COPY pyproject.toml requirements.lock README.md LICENSE ./
COPY src ./src
ARG ENV=dev
ENV ENV=${ENV}
RUN pip install -U pip \
    && pip install --require-hashes -r requirements.lock \
    && pip install .[ops] --no-deps
# Create non-root user
RUN useradd -m appuser && chown -R appuser:appuser /app
USER appuser
EXPOSE 8000
VOLUME ["/tmp"]
HEALTHCHECK CMD curl -f http://localhost:8000/v1/healthz || exit 1
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
