# FactSynth Ultimate — Refactored (2025-09-07)

Логіка незмінна. Структура покращена: фабрика додатка, розділення на `api/`, `schemas/`, `services/`, `core/`.
Ендпоїнти та контракт лишилися як були. Додано:
- API-key аутентифікацію через заголовок `x-api-key` (крім `/v1/healthz` і `/metrics`).
- Prometheus метрики (`/metrics`).
- SSE для `/v1/stream`.

## Quickstart
```bash
python -m venv .venv && . .venv/bin/activate
pip install -U pip && pip install -e .[dev,ops]
export API_KEY=change-me
fsu-api &
curl -s -H 'x-api-key: change-me' http://127.0.0.1:8000/v1/healthz
```
