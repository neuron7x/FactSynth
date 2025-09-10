# FactSynth Prompt Pack
Production-ready prompts & templates to coordinate multi-agent CICD for FactSynth.

## Files
- Coordinator System Prompt → `prompts/coordinator.system.md`
- Builder System Prompt → `prompts/builder.system.md`
- Templates → `prompts/templates/*.json`
- Examples → `prompts/examples/*.json`
- Golden-12 → `prompts/golden-12.json`
- Config → `prompts/config/coordinator_config.json`

## Quickstart
1. Open a new Chat (Coordinator). Paste `prompts/coordinator.system.md`.
2. Provide an intent + a repo URL/path (e.g., add /v1/embed).
3. Take the JSON result → feed it to a Builder Agent loaded with `prompts/builder.system.md`.
4. Builder creates a branch, commits, opens PR with tests, OpenAPI & docs.
5. Review with Spectral & Schemathesis CI; security scans run via Trivy (digest).

## Policies
- Errors: application/problem+json
- OpenAPI: `openapi/openapi.yaml`
- Security: Trivy gating on HIGH,CRITICAL; SARIF category `trivy-image`; optional `.trivyignore`
- Observability: Prometheus metrics; dashboards updated if metrics change

## Notes
- Mark unclear facts as **[verification required]** and proceed.
- Use **Conventional Commits**.
