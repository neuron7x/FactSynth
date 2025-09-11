# FactSynth Ultimate Pro — 1.0.3 (2025-09-07)

Захищений, спостережуваний сервіс **FastAPI** для рефлексії наміру,
скорингу, екстрактивної генерації, стримінгу (SSE/WebSocket) та
демонстраційного конвеєра GLRTPM.

> **EN short:** production-ready API with API-key auth, Prometheus metrics,
> SSE/WS streaming, noise filtering, batch scoring and Problem+JSON errors.

---

## Зміст

* [Можливості](#можливості)
* [Швидкий старт](#швидкий-старт)
* [Кінцеві точки](#кінцеві-точки)
* [Авторизація та ліміти](#авторизація-та-ліміти)
* [Помилки (Problem+JSON)](#помилки-problemjson)
* [Спостережуваність](#спостережуваність)
* [Конфігурація](#конфігурація)
* [Docker](#docker)
* [Postman та OpenAPI](#postman-та-openapi)
* [Тестування](#тестування)
* [Безпека](#безпека)
* [Дорожня карта](#дорожня-карта)
* [Ліцензія](#ліцензія)

---

## Можливості

* **API-ключ** у заголовку `x-api-key` (пропускає `/v1/healthz`, `/metrics`, `/v1/version`).
* **Лімітування запитів** (за замовчуванням 120/хв) з заголовками `X-RateLimit-*`.
* **Стрімінг SSE та WebSocket** для токеноподібних оновлень.
* **Екстрактивна генерація**: `title`, `summary`, `keywords` з тексту.
* **Евристики скорингу**: coverage, length saturation, alpha density, entropy; фільтр гібберіш.
* **Фільтрація шуму**: видаляє HTML/URL/електронну пошту, дедуплікує цілі, зупиняє UA/EN стоп-слова.
* **Пакетний скоринг** та необов'язкові **webhook**-колбеки (з повторами).
* **Структуровані помилки** у форматі Problem+JSON.
* **Метрики Prometheus** + **JSON-логи**; за бажанням OpenTelemetry.
* **HSTS/CSP** заголовки безпеки; обмеження розміру тіла; необов'язковий список дозволених IP.

---

## Швидкий старт

```bash
python -m venv .venv && . .venv/bin/activate
pip install -U pip && pip install -e .[dev,ops]
export API_KEY=change-me        # у продакшені використайте секрет або Vault
uvicorn factsynth_ultimate.app:app --host 0.0.0.0 --port 8000
```

Допоміжні утиліти, такі як класифікатор NLI, простий оцінювач тверджень та
локальний пошук фікстур, тепер знаходяться в пакеті
`factsynth_ultimate.services`. Попередній модуль `app` видалено.

### Перевірка

```bash
curl -s http://127.0.0.1:8000/v1/healthz
```

---

## Кінцеві точки

### Версія

```bash
curl -s http://127.0.0.1:8000/v1/version
```

### Відображення наміру

```bash
curl -s -H 'x-api-key: change-me' \
  -H 'content-type: application/json' \
  -d '{"intent":"Summarize Q4 plan","length":48}' \
  http://127.0.0.1:8000/v1/intent_reflector
```

### Скоринг

```bash
curl -s -H 'x-api-key: change-me' \
  -H 'content-type: application/json' \
  -d '{"text":"hello world","targets":["hello"]}' \
  http://127.0.0.1:8000/v1/score
```

### Пакетний скоринг

```bash
curl -s -H 'x-api-key: change-me' \
  -H 'content-type: application/json' \
  -d '{"items":[{"text":"a"},{"text":"hello doc","targets":["doc"]}]}' \
  http://127.0.0.1:8000/v1/score/batch
```

### SSE Стрім

```bash
curl -N -H 'x-api-key: change-me' \
  -H 'content-type: application/json' \
  -d '{"text":"stream this text"}' \
  http://127.0.0.1:8000/v1/stream
```

### WebSocket Стрім

```text
WS /ws/stream
Header: x-api-key: change-me
Send: "your text"
Recv: {"t":"token"...} ... {"end":true}
```

### Конвеєр GLRTPM (демо)

```bash
curl -s -H 'x-api-key: change-me' \
  -H 'content-type: application/json' \
  -d '{"text":"pipeline test"}' \
  http://127.0.0.1:8000/v1/glrtpm/run
```

---

## Авторизація та ліміти

* Передайте API-ключ у заголовку `x-api-key`.
* Ліміти: 120 запитів на хвилину на ключ або IP. Заголовок `Retry-After` у секундах.

---

## Помилки (Problem+JSON)

Усі помилки повертаються у форматі [RFC 9457](https://www.rfc-editor.org/rfc/rfc9457).

---

## Спостережуваність

* Метрики доступні за `/metrics`.
* Логи у форматі JSON.
* За бажанням інтегрується з OpenTelemetry.

---

## Конфігурація

Змінні середовища: `API_KEY`, `RATE_LIMIT_PER_MINUTE`, `BODY_MAX_BYTES`, `IP_ALLOWLIST`, тощо.

---

## Docker

```bash
docker build -t factsynth .
docker run -p 8000:8000 -e API_KEY=change-me factsynth
```

---

## Postman та OpenAPI

Файл Postman та OpenAPI схему шукайте у директорії `openapi/`.

---

## Тестування

```bash
pip install -e .[dev] || pip install -r requirements.lock
pytest
```

---

## Безпека

* Використовуйте HTTPS у продакшені.
* Зберігайте секрети поза репозиторієм.
* Мінімізуйте дозволені IP.
* Розташуйте CDN/WAF перед ingress для захисту та rate limiting.
* Примусово обмежуйте розмір тіла запиту 1 МБ через `MAX_BODY_BYTES` та проксі.
* Кешуйте легкі ендпоїнти (`/v1/version`, `/metrics`) на edge.

---

## Дорожня карта

* Інтеграція з повноцінною LLM.
* Більше локалізацій.
* Розширені метрики.

---

## Ліцензія

Проєкт поширюється за ліцензією MIT. Див. файл [LICENSE](LICENSE).
