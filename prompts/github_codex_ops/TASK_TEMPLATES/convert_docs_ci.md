# Convert (docs/CI)

```
RUN: docs {"AUTO_APPLY":"on","DRY_RUN":"off","TARGETS":["."],
"GOALS":["README/USAGE/SECURITY/CONTRIBUTING baselines"]}
```

Expected: doc skeletons + diff_preview; link with PR checklist.
