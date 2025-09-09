PRs welcome. Follow ruff/mypy/pytest. Keep coverage≥90%.

## Branches

- Base branch is `main`.
- Create short descriptive branches: `feature/<topic>`, `bugfix/<issue>`, `docs/<change>`
  or `chore/<task>`.
- Do **not** push directly to `main`; branch protection requires PRs, reviews, and green checks.

## Code style

- Python 3.10+.
- Lint and format with `ruff`; type check with `mypy`.
- Keep tests under `tests/` and maintain coverage≥90%.

## Pre-commit & local CI

Install hooks and run the full suite before pushing:

```bash
pip install pre-commit
pre-commit install
pre-commit run --all-files
pytest --cov --cov-report=xml
python tools/coverage_gate.py --xml coverage.xml --min 90
```

## Testing

- Add or update tests for new code and bug fixes.
- Ensure `pytest` passes locally and in CI.

## PR checklist

- [ ] Branch name follows conventions.
- [ ] `pre-commit run --all-files` passes.
- [ ] `pytest` and coverage gate pass (coverage≥90%).
- [ ] Code is linted (`ruff`) and typed (`mypy`).
- [ ] Documentation updated as needed.

## Branch protection & releases

- `main` is protected: merging requires passing CI and at least one review.
- Release by tagging (`git tag vX.Y.Z && git push origin vX.Y.Z`) or `make release` to build
  artifacts and SBOM.
