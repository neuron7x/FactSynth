# FACTSYNTH_LOCK — Output Contract (v1.1)
**Compatibility Guard: Do not change FactSynth runtime API**

## 1) Verification Verdict
- **status**: SUPPORTED | REFUTED | UNCLEAR | OUT_OF_SCOPE | ERROR
- **confidence**: 0.0–1.0 (калібрований)
- **summary**: ≤300 символів, одне речення висновку

## 2) Source Synthesis
- **key_findings**: синтез без CoT, ≤1000 символів
- **citations[]**:
  - id: string
  - source: string
  - snippet: string (≤500)
  - relevance: number [0..1]
  - date: YYYY-MM-DD
  - url: uri

## 3) Traceability & Justification
- **retrieval_query**: string (≤500)
- **justification_steps[]**: 3–7 високорівневих кроків (без CoT)
- **assumptions[]**: ≤10

## 4) Recommendations & Next Steps
- **next_query_suggestion**: string
- **gaps_identified[]**: string[]
- **manual_review**: boolean

## 5) Quality Report (optional)
- **coverage**: { total_candidates, passed_hard_filters, used_in_synthesis }
- **quality_scores**: { sqs_median, sqs_iqr, ess_median }
- **diversity**: { domain_entropy, geo_spread, media_mix:{primary,secondary} }
- **recency**: { median_age_days, staleness_flag }
- **contradictions**: { conflict_pairs, max_pair_confidence }
- **adversarial_risk**: { level: LOW|MEDIUM|HIGH, signals: string[] }

## 6) Provenance (optional)
- **policy_snapshot_sha256**: string
- **citation_hashes[]**: sha256(url|date|snippet)
- **retrieval_id**: string

## 7) Policy Snapshot (optional)
- **name**: "default-quality-policy"
- **version**: "1.0.0"
- **weights**: див. `config/quality_policy.yaml`
