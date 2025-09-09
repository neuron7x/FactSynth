# Evaluate (gate before merge)

```
RUN: tests {"AUTO_APPLY":"off","DRY_RUN":"on","TARGETS":["."],
"GOALS":["unit/integration scaffolding","coverage gate"],"COVERAGE_TARGET":90}
```

Expected: plan + commands + checks; apply false; artifacts: coverage report.
