# FactSynth Ultimate — Ready Product

API + CLI, юніт-тести з покриттям, CI/CD, GitHub Pages (coverage-бейдж, OpenAPI, live demo).

## Локальний запуск
```bash
python -m pip install -U pip
pip install -e .[test]
uvicorn factsynth_ultimate.app:app --host 0.0.0.0 --port 8000
````

## Ендпоїнти

* `GET /healthz`
* `GET /metrics`
* `POST /v1/generate` — {prompt, max_tokens} → {output}

## Бейджі (для neuron7x/FactSynth)

[![CI](https://github.com/neuron7x/FactSynth/actions/workflows/ci.yml/badge.svg?branch=main)](https://github.com/neuron7x/FactSynth/actions/workflows/ci.yml)
[![CodeQL](https://github.com/neuron7x/FactSynth/actions/workflows/codeql.yml/badge.svg?branch=main)](https://github.com/neuron7x/FactSynth/actions/workflows/codeql.yml)
![Coverage](https://neuron7x.github.io/FactSynth/badges/coverage.svg)

__Live demo / OpenAPI (Pages):__

* Demo: [https://neuron7x.github.io/FactSynth/?api=https://your-api-host](https://neuron7x.github.io/FactSynth/?api=https://your-api-host)
* OpenAPI: [https://neuron7x.github.io/FactSynth/openapi.html](https://neuron7x.github.io/FactSynth/openapi.html)
