PRs welcome. Follow ruff/mypy/pytest. Keep coverage≥90%.

## Branch Naming

Use short, descriptive, kebab-case names prefixed with the change type:

- `feature-<description>` for new features
- `bugfix-<description>` for bug fixes
- `docs-<description>` for documentation updates
- `chore-<description>` for maintenance tasks
- `backup-YYYY-MM-DD` for repo snapshots

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
