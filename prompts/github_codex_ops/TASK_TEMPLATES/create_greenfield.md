# Create (greenfield)

```
RUN: repo_scan {"AUTO_APPLY":"off","DRY_RUN":"on","TARGETS":["."],
"GOALS":["baseline audit","identify gaps for lint/tests/CI"],
"COVERAGE_TARGET":85,"PERF_BUDGET":{"p95_build":"<=10m"},"IGNORE":["dist","build","node_modules"]}
```

Expected: JSON per contract with audit plan, CI/lint/test recommendations, next steps.
