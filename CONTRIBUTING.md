PRs welcome. Follow ruff/mypy/pytest. Keep coverage≥90%.

## Pre-commit

Install git hooks:

```bash
pip install pre-commit
pre-commit install
```

Run checks on staged files:

```bash
pre-commit run --files <path/to/file.py>
```

## Branch protection

The `main` branch is protected to keep the codebase stable:

- Pushes must come through pull requests.
- All required status checks must pass before merging.
- Force pushes are disabled.

Please open a pull request against `main` and ensure all checks succeed.
