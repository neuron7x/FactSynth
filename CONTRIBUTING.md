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

Before committing, refresh dependency artifacts:

```bash
pre-commit run pip-compile --files pyproject.toml requirements.lock
scripts/update_dev_requirements.sh
```

## Conventional Commits

All commit messages and pull request titles must follow the
[Conventional Commits](https://www.conventionalcommits.org/) specification.
Use the `cz` (Commitizen) helper to craft messages automatically:

```bash
npm run commit
```

The basic structure is:

```
type(optional-scope): short summary

[optional body]

[optional footers]
```

- **Allowed types:** `build`, `chore`, `ci`, `docs`, `feat`, `fix`, `perf`,
  `refactor`, `revert`, `style`, and `test`.
- **Scope** is optional but encouraged for complex areas of the codebase.
- Use the body to explain _why_ the change is needed when the subject is not
  enough.
- Breaking changes must include a footer beginning with `BREAKING CHANGE:` that
  describes the impact.
- Reference issues or pull requests with a footer such as `Refs: #123`.

Pre-commit hooks, CI, and GitHub Actions will reject commits and pull requests
that do not follow this format.

## Branch protection

The `main` branch is protected to keep the codebase stable:

- Pushes must come through pull requests.
- All required status checks must pass before merging.
- Force pushes are disabled.

Please open a pull request against `main` and ensure all checks succeed.
