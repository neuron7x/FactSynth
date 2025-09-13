- **Version**: `factsynth-prompt-pack v1.0.0` (2025-09-09)
- **Usage checklist**:
  1. Lock system prompt string.
  2. Validate JSON schema.
  3. Seed randomness.
  4. Record `METRICS`.
  5. Fail CI on schema violation or calibration regression.
- **Monitoring**: Track `claims_confirmed/refuted/mixed/not_enough_evidence/not_a_fact` ratios; alert on sudden confidence inflation.
- **Rollback**: Keep previous prompt under `prompts/fact_judge_<semver>.txt`.
- **Extension points**: Plug a retrieval tool; add domain adapters (finance, bio, geo) with unit catalogs.
