# Чекліст використання

- [ ] Встановлено `FACTSYNTH_API_KEY` (секрети — не в git).
- [ ] Сервер відповідає на `/v1/healthz` і `/v1/version`.
- [ ] Валідовано відповіді за JSON-схемами (`scripts/validate.sh`).
- [ ] Застосовано backoff на `429` згідно `Retry-After`.
- [ ] Увімкнені метрики Prometheus і Grafana дашборд (за потреби).
- [ ] Пройдено `GOLDEN_12_TESTSET.json`.
