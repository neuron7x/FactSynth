```
RUN: repo_scan {"AUTO_APPLY":"off","TARGETS":["."],"GOALS":["audit repo","list gaps"]}
```

Expected JSON with plan (files/CI/gaps), commands (gh/git/npm/pip), artifacts: audit-report.md; next: triage → lint_format → tests.
