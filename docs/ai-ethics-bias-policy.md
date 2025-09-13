# AI Ethics & Bias Policy

This document outlines FactSynth's approach to evaluating and mitigating bias in AI systems.

## Bias Assessment Process
1. **Data Collection** – curate a control dataset representing relevant user groups.
2. **Fairness Testing** – execute automated fairness tests that compute metrics such as demographic parity on the control dataset.
3. **Review** – document results and escalate disparities beyond agreed thresholds.
4. **Mitigation** – adjust data or models and re‑run tests until metrics meet policy standards.

## Regular Audits
- Audit sessions occur **quarterly** and review fairness metrics across releases.
- Key metrics include demographic parity difference and equal opportunity difference.
- Findings are archived and tracked for remediation.

## Continuous Integration
Fairness tests are executed in CI to prevent regressions. The CI pipeline runs dedicated
fairness tests on the control dataset and fails when disparities exceed policy thresholds.
