# syntax=docker/dockerfile:1

FROM python:3.11-slim AS builder
WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PIP_NO_CACHE_DIR=1
RUN apt-get update && apt-get install -y --no-install-recommends build-essential curl && rm -rf /var/lib/apt/lists/*
COPY pyproject.toml README.md LICENSE ./
RUN pip install --upgrade pip && pip install --no-cache-dir --prefix=/install .[ops]
COPY src ./src
RUN pip install --no-cache-dir --prefix=/install .

FROM python:3.11-slim AS runtime
WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PIP_NO_CACHE_DIR=1 \
    PYTHONPYCACHEPREFIX=/tmp/__pycache__ HOME=/home/nonroot
RUN apt-get update && apt-get install -y --no-install-recommends curl && rm -rf /var/lib/apt/lists/*
RUN groupadd --system --gid 65532 nonroot \
    && useradd --system --uid 65532 --gid nonroot --create-home --home-dir /home/nonroot nonroot
COPY --from=builder /install /usr/local
COPY --chown=nonroot:nonroot src ./src
COPY --chown=nonroot:nonroot .env.example ./.env
RUN mkdir -p /tmp/__pycache__ && chown -R nonroot:nonroot /app /home/nonroot /tmp \
    && chmod -R 755 /app /home/nonroot /tmp && rm -rf /root/.cache
USER nonroot
EXPOSE 8000
HEALTHCHECK CMD curl -f http://localhost:8000/health || exit 1
ENTRYPOINT ["fsu-api"]
CMD ["--host", "0.0.0.0", "--port", "8000"]
