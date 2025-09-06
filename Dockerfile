FROM python:3.11-slim AS base
WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
RUN apt-get update && apt-get install -y --no-install-recommends build-essential && rm -rf /var/lib/apt/lists/*
COPY pyproject.toml README.md LICENSE ./
RUN pip install -U pip && pip install .[dev,ops]
COPY src ./src
COPY .env.example ./.env
EXPOSE 8000
USER 10001
CMD ["fsu-api"]
