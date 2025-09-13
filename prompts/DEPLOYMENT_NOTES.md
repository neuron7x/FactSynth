# Нотатки з деплойменту

- **Auth:** усі прод-виклики з `x-api-key` (окрім `/v1/healthz`, `/v1/version`, `/metrics`).
- **Rate limiting:** читайте `X-RateLimit-*`; на `429` чекайте `Retry-After`.
- **SSE:** `/v1/stream` — відправляє події до `{"end":true}`.
- **Спостережність:** Prometheus `/metrics`; `/v1/feedback` для оцінок пояснень і цитат; логіку трейсингу переносьте у `meta.trace_id`.
- **Безпека:** HSTS/CSP, `TRUSTED_HOSTS`, CORS, ліміти тіла запиту, опційний IP-allowlist.
