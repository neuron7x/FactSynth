# FactSynth — Тестовий пакет (CI + юніт тести)

## Що всередині

- `.github/workflows/ci.yml` — CI: тести + покриття + gate (мінімум 90% якщо є виміряні рядки).
- `.github/workflows/release-on-tag.yml` — реліз при пуші тега: тести, покриття, збірка пакету,
  контейнер, SBOM, реліз.
- `.github/workflows/codeql.yml` — CodeQL-скан.
- `.github/dependabot.yml` — авто-оновлення залежностей.
- `pytest.ini`, `.coveragerc` — конфіг тесу та покриття.
- `tools/coverage_gate.py` — скрипт, що валідуює coverage.xml.
- `tests/` — адаптивні smoke/CLI/ASGI/конфіг-тести, що не ламають збірку,
  якщо відсутні відповідні шари.

## Використання

1. Розпакуй у корінь репозиторію.
2. Налаштуй секрети (за потреби): `PYPI_API_TOKEN`, `DOCKERHUB_USERNAME`, `DOCKERHUB_TOKEN`.
3. Встанови залежності та запусти тести:

    ```bash
    python -m pip install -U pip wheel build
    pip install -r requirements.lock && pip install -e .[dev]
    # опційно: scripts/update_dev_requirements.sh && pip install -r requirements-dev.txt
    pytest --cov --cov-report=xml
    python tools/coverage_gate.py --xml coverage.xml --min 90
    ```

4. Мутаційне тестування:

    ```bash
    mutmut run
    # або використай Makefile:
    make mutmut
    ```

> Примітка: якщо у коді поки відсутні імпортовані модулі/ASGI/CLI —
> відповідні тести будуть **skip**,
> а gate трактує «0 виміряних рядків» як **PASS**, щоб не блокувати інтеграцію.
> Додатково: тест `tests/test_isr.py` залежить від `jax` та `diffrax`.
> Для його запуску встановіть опцію `isr`:
>
> ```bash
> pip install -e .[isr]
> ```
>
> Також `tests/test_akpshi.py` та `tests/test_ndmaco.py` потребують `numpy`:
>
> ```bash
> pip install -e .[numpy]
> ```
