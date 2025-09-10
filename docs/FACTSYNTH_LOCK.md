# Compatibility Guard: Do not change FactSynth runtime API
# Purpose: Canonical contract + operator notes (no placeholders)

# FACTSYNTH_LOCK — Output Contract (v1.0)

1) Verification Verdict
- status: SUPPORTED | REFUTED | UNCLEAR | OUT_OF_SCOPE | ERROR
- confidence: 0.0–1.0
- summary: коротке речення висновку

2) Source Synthesis
- key_findings: стислий синтез без CoT
- citations[]:
  - id: string
  - source: string
  - snippet: string (≤500)
  - relevance: number [0..1]
  - date: YYYY-MM-DD
  - url: uri

3) Traceability & Justification
- retrieval_query: string
- justification_steps[]: 3–7 коротких кроків (високорівнево)
- assumptions[]: ≤10 пунктів

4) Recommendations & Next Steps
- next_query_suggestion: string
- gaps_identified[]: string[]
- manual_review: bool

Operational Notes
- Режим за замовчуванням: `allow_untrusted=false`
- Offline-перевірка: вбудований офлайновий ретрівер для тестів (fixtures)
- Спостережуваність: метрики `factsynth_verify_total`, `factsynth_verify_latency_ms_bucket`, логування JSON
- Політика лімітів: 400 ≤ p95(ms) @ 10 RPS на інстанс
- Безпека: усі зовнішні ключі — тільки з ENV; при відсутності — graceful fallback із manual_review=true
