* **Version**: v4.1.1-en (2025-09-09), derived from v4.1 (UA).
* **Usage checklist**: choose mode → set TARGETS/GOALS → run DRY_RUN → review plan/diff/risks/checks → flip AUTO_APPLY:on when green → open PR with Conventional Commits.
* **Monitoring**: emit KPIs (coverage, p95 build/test, lint, vulns) into `checks`/artifacts.
* **Rollback**: enforce branch policy; revert via PR; keep DRY_RUN snapshots in artifacts.
* **Extension points**: add modes (SCA, license-audit), expand PERF_BUDGET schema, org-level CI templates.
