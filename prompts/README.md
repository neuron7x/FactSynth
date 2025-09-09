# FactSynth — Prompts пакет v1.2.0

Це канонічний пакет промптів для **FactSynth**. Містить системний промпт, шаблони задач, few-shot приклади, GOLDEN-12 тестсет, JSON-схеми та скрипти для швидкого старту.

## Швидкий запуск

```bash
cd prompts/scripts
./quickstart.sh
```

Перед запуском переконайтесь, що встановлено Node.js та утиліта `ajv` з пакета `ajv-cli` (`npm i -g ajv-cli`).

Скрипт:

1. Підкаже встановити `FACTSYNTH_API_KEY`.
2. Виконає smoke-тести `/v1/healthz` і `/v1/version`.
3. Запустить приклади `generate` і `score`.
4. Валідатором зіставить відповіді зі схемами JSON.
