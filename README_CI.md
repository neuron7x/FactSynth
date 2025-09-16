# CI/CD & Testing Quickstart

1. Install locally and run tests:

    ```bash
    python -m pip install -U pip wheel build pre-commit
    pip install -r requirements.lock && pip install -e .[dev,test]
    # опційно: scripts/update_dev_requirements.sh && pip install -r requirements-dev.txt
    pre-commit run --all-files || true
    pytest  # конфіг `pytest.ini` гарантує покриття та поріг 85%
    python tools/coverage_gate.py --xml coverage.xml --min 85
    python tools/validate_openapi.py || true
    pip-audit -r requirements.lock
    npm audit --production
    bandit -r src
    pytest tests/test_i18n_catalog_parity.py
    ```

> Contract tests rely on `requests`; they use `pytest.importorskip` to skip when it's absent.

> Поріг покриття контролюється через `--cov-fail-under=85` у `pytest.ini`. Репорти можна знайти у
> `coverage.xml` та каталозі `htmlcov/` після локального прогону.

Install [Node.js](https://nodejs.org/) ≥ 18 for Markdown linting:

```bash
npx markdownlint-cli2 README.md .github/PULL_REQUEST_TEMPLATE.md
```

1. Push to main/PR — GitHub Actions `CI` запуститься автоматично (matrix 3.10–3.12).

1. Реліз:

    ```bash
    git tag my-release-1
    git push origin my-release-1
    ```

    Отримаєш артефакти (wheel+sdist+checksums+SBOM) і контейнер у GHCR.

## CI limits

Документаційні пайплайни (`docs-build.yml`, `pages.yml`) мають обмеження `timeout-minutes: 20`,
щоб запобігти зависанням і пришвидшити фідбек. Коригуй за потреби.

## Cleanup branches with failed checks

Use the **Cleanup branches with failed checks** workflow to prune branches whose
checks have failed. Trigger it from the GitHub UI via:

```text
Actions → Cleanup branches with failed checks → Run workflow
```

### Prerequisites

* Requires repository write access.
* Protected branches `main` and `master` are skipped automatically.

### Caution

Branch deletions performed by this workflow are irreversible. Ensure any branch
you remove is no longer needed.
