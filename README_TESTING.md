# FactSynth — Тестовий пакет (CI + юніт тести)

## Що всередині

- `.github/workflows/ci.yml` — CI: тести + покриття + gate (мінімум 85% якщо є виміряні рядки).
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
3. Налаштуй локальне середовище та переконайся, що всі перевірки проходять **перед пушем**:

    ```bash
    python -m venv .venv
    source .venv/bin/activate
    pip install -r requirements-dev.txt
    pre-commit run --all-files
    pytest  # конфіг `pytest.ini` уже додає покриття та зупинить прогін, якщо воно < 85%
    ```

    > Якщо базові залежності ще не встановлені, перед `pytest` виконай `pip install -e .[dev]`
    > або `make install`.

    > Альтернатива: скористайся `make test`, який виконує ті самі кроки за тебе.

    > Покриття контролюється опцією `--cov-fail-under=85` з `pytest.ini`. Якщо бачиш падіння через
    > поріг, перевір локальний звіт (`htmlcov/index.html`) або згенеруй XML для `tools/coverage_gate.py`.

    > Fairness-контрольні тести розташовані в каталозі `fairness_tests` і запускаються разом із
    > основним прогоном `pytest`. За потреби сфокусуватися лише на перевірках неупередженості,
    > виконай `pytest fairness_tests -m fairness --no-cov`.

4. За потреби згенеруй повний звіт покриття й перевір його:

    ```bash
    python -m pip install -U pip wheel build
    pip install -r requirements.lock && pip install -e .[dev]
    # опційно: scripts/update_dev_requirements.sh && pip install -r requirements-dev.txt
    pytest  # перегенеруй `coverage.xml` та `htmlcov/`, якщо хочеш передивитися репорти
    python tools/coverage_gate.py --xml coverage.xml --min 85
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

## Мутаційне тестування

Запусти мутаційні тести для основних модулів (`src/factsynth_ultimate/core`, `src/factsynth_ultimate/services`, `src/factsynth_ultimate/api`):

```bash
mutmut run  # або make mutmut
```
