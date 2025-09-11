# CI/CD & Testing Quickstart

1. Install locally and run tests:

```bash
    python -m pip install -U pip wheel build pre-commit
    pip install -r requirements.lock || pip install -e .[dev,test]
    pre-commit run --all-files || true
    pytest --cov --cov-report=xml
    python tools/coverage_gate.py --xml coverage.xml --min 90
    python tools/validate_openapi.py || true
    ```

    > Contract tests depend on the `requests` library; install dependencies first or
    > they will be skipped via `pytest.importorskip`.

2. Push to main/PR — GitHub Actions `CI` запуститься автоматично (matrix 3.10–3.12).

3. Реліз:

    ```bash
    git tag my-release-1
    git push origin my-release-1
    ```

    Отримаєш артефакти (wheel+sdist+checksums+SBOM) і контейнер у GHCR.
