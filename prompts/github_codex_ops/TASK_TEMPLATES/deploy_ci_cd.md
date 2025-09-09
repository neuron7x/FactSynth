# Deploy (CI/CD)

```
RUN: ci_cd {"AUTO_APPLY":"on","DRY_RUN":"off","TARGETS":["."],
"GOALS":["build/test/lint jobs","release tagging","branch protections"]}
```

Expected: GH Actions plan, PR/commit conventions, protections.
