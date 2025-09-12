# syntax=docker/dockerfile:1

FROM python:3.12-slim AS build
WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
RUN apt-get update && apt-get install -y --no-install-recommends build-essential \
    && rm -rf /var/lib/apt/lists/*
COPY pyproject.toml README.md LICENSE ./
RUN pip install -U pip && pip install .[dev,ops]
COPY src ./src

FROM python:3.12-slim
WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 UVICORN_WORKERS=2
RUN apt-get update && apt-get install -y --no-install-recommends tini curl \
    && rm -rf /var/lib/apt/lists/*
COPY pyproject.toml README.md LICENSE ./
COPY src ./src
ARG ENV=dev
ENV ENV=${ENV}
RUN pip install -U pip && pip install .[ops]
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
