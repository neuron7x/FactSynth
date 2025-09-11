# CI/CD & Testing Quickstart

1. Install locally and run tests:

    ```bash
    python -m pip install -U pip wheel build pre-commit
    pip install -e .[dev,test] || pip install -e . || pip install .
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
