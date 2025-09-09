# syntax=docker/dockerfile:1

FROM python:3.11-slim@sha256:316d89b74c4d467565864be703299878ca7a97893ed44ae45f6acba5af09d154 AS build
WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
RUN apt-get update && apt-get install -y --no-install-recommends build-essential && rm -rf /var/lib/apt/lists/*
COPY pyproject.toml README.md LICENSE ./
RUN pip install -U pip && pip install .[dev,ops]
COPY src ./src

FROM python:3.11-slim@sha256:316d89b74c4d467565864be703299878ca7a97893ed44ae45f6acba5af09d154
WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
COPY pyproject.toml README.md LICENSE ./
COPY src ./src
COPY .env.example ./.env
RUN pip install -U pip && pip install .[ops]
EXPOSE 8000
USER 10001
CMD ["fsu-api"]
