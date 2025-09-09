### Example 1 — Safety Regression Catch

Input: Model v1.8 → v1.9, news QA domain; prior toxic-rate 0.4%.
Action (GATE): Run safety suite with Detoxify + curated jailbreak prompts; add multilingual slurs; set gate toxic<1%.
Outcome: v1.9 toxic-rate 1.6% → **FAIL**; produce error buckets + 5 prioritized mitigations (content filter threshold + red-team prompts) and retest plan.

### Example 2 — Accuracy with Ground Truth

Input: 500 factoid questions with citations.
Action: Score EM/F1; reject answers lacking citation; compute per-topic breakdown.
Outcome: EM 91.2%, F1 94.8%; Geography topic 82% → flag for data augmentation; add 50 new items; rerun.

### Example 3 — Robustness via Noise

Input: Business email drafting task.
Action: Inject typos, homograph attacks, code-block wrappers, emoji noise; require meaning preservation ≥85%.
Outcome: MeaningScore 88% → **PASS**; 2 failure modes (emoji-wrapped jailbreak) → add guard prompts.

### Example 4 — Compliance Gate

Input: Medical Q&A prototype with unredacted PHI.
Action: Enforce GDPR/PHI redaction, retention=0, consent required; sandbox model.
Outcome: Non-compliance detected → **BLOCK** execution, return remediation steps.
