### A) CREATE — New Endpoint / Module

[Objective]
Implement <feature> as <module/endpoint>. Constraints: <perf/security>. Integrate with: SSE/WS? metrics? rate limits?

[Inputs/Artifacts]

- Domain: …
- Data contracts (Pydantic): …
- Perf target: p95 ≤ … ms @ … RPS

[Deliverables]

- Design (diagram/text)
- Code (paths)
- Tests (happy/edge/failure)
- Metrics, logging, Problem+JSON
- Runbook

[Assumptions]

- …

---

### B) IMPROVE — Optimization / Refactor

[Objective]
Refactor <file(s)> for readability/perf. Keep behavior identical.

[Targets]

- Complexity: from O(?) → O(?)
- Memory: −?
- Latency: p95 −? ms

[Deliverables] Diff-ready code, microbench, tests, risk notes.

---

### C) CONVERT — Port / Interface

[Objective]
Port <logic> to <lang/runtime>. Preserve contracts; include adapter layer and tests.

---

### D) EVALUATE — Design/Code Review

[Objective]
Critique <design/code>. Cover: correctness, security, ops, perf, readability. Produce severity-ranked issues and fixes.

---

### E) DEPLOY — Ops Recipe

[Objective]
Add CI job / Dockerfile / Helm chart changes for <change>. Include secrets strategy, health checks, rollback plan.
