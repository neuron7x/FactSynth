```
RUN: apply {"AUTO_APPLY":"off","GOALS":["demonstrate loop gating"]}
```

Expected: apply.allowed=false until checks green; references to PLAN/DIFF/APPLY sequencing and PR requirements.
