# CI/CD & Testing Quickstart

1. Install locally and run tests:

    ```bash
    python -m pip install -U pip wheel build pre-commit
    pip install -e .[dev] || pip install -r requirements.lock
    pre-commit run --all-files || true
    pytest --cov --cov-report=xml
    python tools/coverage_gate.py --xml coverage.xml --min 90
    python tools/validate_openapi.py || true
    ```

   Install [Node.js](https://nodejs.org/) ≥ 18 for Markdown linting:

    ```bash
    npx markdownlint-cli2 README.md .github/PULL_REQUEST_TEMPLATE.md
    ```

2. Push to main/PR — GitHub Actions `CI` запуститься автоматично (matrix 3.10–3.12).

3. Реліз:

    ```bash
    git tag my-release-1
    git push origin my-release-1
    ```

    Отримаєш артефакти (wheel+sdist+checksums+SBOM) і контейнер у GHCR.

## Cleanup branches with failed checks

Use the **Cleanup branches with failed checks** workflow to prune branches whose
checks have failed. Trigger it from the GitHub UI via:

```
Actions → Cleanup branches with failed checks → Run workflow
```

### Prerequisites

* Requires repository write access.
* Protected branches `main` and `master` are skipped automatically.

### Caution

Branch deletions performed by this workflow are irreversible. Ensure any branch
you remove is no longer needed.
