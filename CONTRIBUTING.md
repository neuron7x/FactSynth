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

## Markdown lint

`markdownlint-cli2` runs via `npx` and requires Node.js (v18+).
Lint all Markdown files with:

```bash
npx -y markdownlint-cli2 "**/*.md"
```

## Branch protection

The `main` branch is protected to keep the codebase stable:

- Pushes must come through pull requests.
- All required status checks must pass before merging.
- Force pushes are disabled.

Please open a pull request against `main` and ensure all checks succeed.
