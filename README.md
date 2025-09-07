# FactSynth Ultimate — v2.0.0
**Дата:** 06.09.2025 (Europe/Kyiv) • **Ліцензія:** MIT

Об'єднаний продакшен-продукт:
- **Intent→Insight**: один абзац **рівно N слів** (укр.), строгий контракт, детермінізм, J-індекс (Format/Relevance/Depth/Action/Novelty).
- **GLRTPM**: рольовий оркестратор (Раціоналіст/Критик/Естет/Інтегратор/Спостерігач), фаза **R–I–P–Ω**, TF‑IDF пам’ять і метрики (coherence/diversity/contradiction).
- **API/CLI/UI**, Docker/K8s, CI, **coverage≥90%** (pytest‑cov), Prometheus metrics, SSE stream.

## Quickstart (локально)
```bash
python -m venv .venv && . .venv/bin/activate
pip install -U pip && pip install -e .[dev,ops]
fsu-api &
curl -H 'x-api-key: change-me' -H 'content-type: application/json' \
  -d '{"intent":"Хочу сфокусувати KPI","length":100}' http://127.0.0.1:8000/v1/intent_reflector
# UI: відкрий ui/index.html (Insight) або ui/roleplay.html (GLRTPM)
```

## Змінні середовища

- `API_KEY` — ключ для авторизації (дефолт `change-me`)
- `API_HOST` — хост для запуску API (дефолт `0.0.0.0`)
- `API_PORT` — порт API (дефолт `8000`)

## Docker
```bash
docker build -t factsynth-ultimate:2.0 .
docker run --rm -p 8000:8000 -e API_KEY=change-me factsynth-ultimate:2.0
```

## Ендпоінти
- `POST /v1/intent_reflector` → абзац за контрактом
- `POST /v1/insight` → синонім intent_reflector
- `POST /v1/score` → текст + F/R/D/A/N/J
- `POST /v1/stream` → SSE
- `POST /v1/glrtpm/run` → рольова симуляція (R–I–P–Ω) з YAML/JSON конфігом
- `GET /v1/healthz`, `GET /metrics`

## Тести/coverage
```bash
pytest
# fail-under=90% (змінюй у pyproject.toml за потреби)
```

## K8s (приклад)
```
kubectl apply -f k8s/namespace.yaml
kubectl apply -f k8s/secret.yaml
kubectl apply -f k8s/deployment.yaml
kubectl apply -f k8s/service.yaml
kubectl apply -f k8s/ingress.yaml
kubectl apply -f k8s/hpa.yaml
kubectl apply -f k8s/pdb.yaml
kubectl apply -f k8s/networkpolicy.yaml
```
