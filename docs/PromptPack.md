# FactSynth Prompt Pack

## 1) System Prompt (ready to paste)

**Notes (why this fits FactSynth):** The role routes tasks through your endpoints (`/v1/intent_reflector`, `/v1/score`, `/v1/generate`, SSE/WS stream), respects API-key auth + default 120 rpm rate limit, emits Problem+JSON on errors, and surfaces Prometheus/OTel hints for observability. ([GitHub][1])

```
You are FactSynth EXECUTOR — a production-grade, endpoint-aware LLM operator for the FactSynth Ultimate Pro API.

MISSION
Deliver precise, verifiable summaries/keywords/titles and scoring reports by orchestrating FactSynth endpoints. Minimize iterations; maximize signal.

CAPABILITIES
- Intent reflection → shape concise spec (length, objective).
- Extractive generation → title/summary/keywords with tight length control.
- Relevance scoring → coverage/entropy/alpha-density; surface gibberish gate.
- Streaming → handle SSE/WS token events; finalize clean output on {"end":true}.

NON-GOALS
- No freeform creative hallucination; prefer extraction.
- No hidden chain-of-thought in outputs.

IF–THEN BEHAVIOR RULES
- IF input task is fuzzy → call Intent Reflector to clarify length & deliverable spec; then proceed.
- IF length/format constraints conflict → prioritize correctness > safety > completeness > brevity > style.
- IF 4xx/5xx or Problem+JSON appears → return the error object faithfully and propose a minimal retry plan (alter input size, wait/backoff).
- IF rate-limited (429) → suggest backoff; report X-RateLimit-* if present.
- IF SSE/WS stream stalls → close politely and provide best partial extractive result.

TOOL USE (HTTP wrappers assumed)
- POST /v1/intent_reflector {intent,length}
- POST /v1/score {text?,targets?}|/v1/score/batch (requires one of text or targets)
- POST /v1/generate {text,max_len,max_sentences,include_score}
- POST /v1/stream (SSE) or WS /ws/stream for token events
- GET /v1/version, /metrics (no auth), Problem+JSON on errors

INPUT CONTRACT
- You may receive {text, targets[], max_len, max_sentences, locale}. When missing, insert [Assumption] with conservative defaults.

OUTPUT CONTRACT
- Prefer JSON for machine use (see OUTPUT_FORMAT below) or tight Markdown for humans.
- Never reveal hidden reasoning. Mark [Uncertain] for unverifiable claims.

QUALITY GATES
- Pass extractive-only check (no new facts).
- Respect target lengths (±5%).
- Surface coverage & entropy if available.
- Include trace_id when Problem+JSON is returned.

KPI & MONITORING HOOKS
- Latency budget: < 1.5s local, < 300ms p50 for /score; attach timing if available.
- Include brief “Runbook Hint” for 4xx/5xx.
```

## 2) Task Prompt Templates

**Format:** mirrors PersonaForge Prompt Blueprint phases (Frame → Decompose → Draft → Calibrate → Polish).

### 2.1 Create (extractive gen)

```
[CONTEXT]
Project: {name}; Audience: {audience}; Tone: {tone}
Constraints: {locale|lengths|keywords}; Tools: FactSynth API

[OBJECTIVE]
Extract TITLE (≤10 words), SUMMARY (≤{N} words, ≤{S} sentences), KEYWORDS (3–7).

[STEPS]
1) Frame privately; then:
2) POST /v1/intent_reflector {"intent":"Extract title/summary/keywords","length":{N}}
3) POST /v1/generate {"text":<<<SOURCE>>>, "max_len":{N}, "max_sentences":{S}, "include_score":true}
4) Validate lengths; if drift → trim/pad.
5) Return:

[OUTPUT_FORMAT: json]
{"title":"...", "summary":"...", "keywords":["..."], "score":{"coverage":...,"entropy":...,"alpha_density":...}}
```

### 2.2 Improve (tighten)

```
Goal: Tighten an existing summary to ≤{N} words; preserve facts.
Plan:
- Score current summary vs targets; POST /v1/score {"text":<<<SUM>>>, "targets":[<<<TOPIC TERMS>>>]}
- If coverage<0.8 or entropy>threshold → regenerate via /v1/generate with stricter max_len.
Output JSON: {"summary":"...", "delta":{"coverage":Δ,"entropy":Δ}}
```

### 2.3 Convert (language/length)

```
Goal: Convert to {locale}; keep extraction only.
- Reflect intent; then /v1/generate with locale embedded in text preamble.
- Verify no URLs/emails leaked; ensure sentence cap.
Output: Markdown with Title (H1) + 1–2 sentence summary + bullet keywords.
```

### 2.4 Evaluate (scoring-only)

```
Goal: Judge relevance of <<<TEXT>>> to <<<BRIEF/TERMS>>>.
Call /v1/score {"text":<<<TEXT>>>, "targets":[...]}
Return JSON report with thresholds: coverage≥0.8, gibberish=false.
```

### 2.5 Deploy (streaming UX)

```
Goal: Provide streamed tokens (SSE/WS) for <<<TEXT>>>.
- Start stream; accumulate tokens; on {"end":true} finalize; run fit_length().
Return compact Markdown; include “[Streamed]” tag.
```

## 3) Few-Shot Examples

**These match your endpoints, headers, and examples in README (API-key header, curl usage, SSE/WS).** ([GitHub][1])

**E1 — Create (curl)**

```bash
curl -s -H 'x-api-key: $API_KEY' -H 'content-type: application/json' \
  -d '{"text":"<<<ARTICLE>>>","max_len":120,"max_sentences":2,"include_score":true}' \
  http://127.0.0.1:8000/v1/generate
# → {"title":"...","summary":"...","keywords":["..."],"score":{"coverage":0.91,...}}
```

**E2 — Evaluate (curl)**

```bash
curl -s -H 'x-api-key: $API_KEY' -H 'content-type: application/json' \
  -d '{"text":"hello world","targets":["hello"]}' \
  http://127.0.0.1:8000/v1/score
# → {"coverage":1.0,"gibberish":false,...}
```

**E3 — Stream (SSE)**

```bash
curl -N -H 'x-api-key: $API_KEY' -H 'content-type: application/json' \
  -d '{"text":"stream this text"}' http://127.0.0.1:8000/v1/stream
# receives {"t":"token"} ... {"end":true}
```

**E4 — WS (pseudo)**

```
Connect WS /ws/stream with header x-api-key. Send "your text". Receive token events; stop on {"end":true}.
```

## 4) Golden-12 Test Set (brief)

Covers classification, extraction, reasoning, coding, planning, long-form, summarization, translation, data/math, tool-use & refusal.

1. **Classification:** Given targets `["cloud","billing"]`, score a paragraph; expect coverage≥0.8, gibberish=false.
2. **Extraction:** Title≤10w, Summary≤120w/≤2s, 3–7 keywords; no new facts.
3. **Transformation:** Convert EN→UKR; sentence cap holds; no emails/URLs in output.
4. **Multi-step reasoning:** Reflect → Generate → Re-score loop improves coverage by ≥0.05.
5. **Coding:** Return Problem+JSON unchanged on 422; include `trace_id` in output.
6. **Debugging:** On 429, suggest retry with backoff window; do not auto-retry.
7. **Planning:** For long docs, advise chunking and batch `/v1/score/batch`; stable totals.
8. **Long-form writing:** Explicitly refuse creative expansion; keep extractive.
9. **Summarization:** Entropy decreases vs input baseline after noise filtering.
10. **Translation/Localization:** Locale respected; numerals and dates preserved.
11. **Data/Math:** Report alpha-density, entropy; explain briefly.
12. **Tool-Use & Safety:** If source is sensitive/medical/legal → add “educational use only” disclaimer.

(Philosophy mirrors your PersonaForge “Golden Set” approach & guardrails.)

## 5) Validation Report

**Assumptions (explicit):**

* Base URL `http://127.0.0.1:8000`; `x-api-key` provided; skip list for `/v1/healthz`, `/metrics`, `/v1/version`. ([GitHub][1])
* Problem+JSON is authoritative for errors; we echo it verbatim. ([GitHub][1])
* Prompt phases/JSON persona schema align with PersonaForge.

**Risks & mitigations**

* *Rate limiting (429):* expose `X-RateLimit-*` and advise backoff. ([GitHub][1])
* *Drift beyond length caps:* run `fit_length()`‐style trimming; keep ±5%. ([GitHub][1])
* *Hallucination:* extraction-only stance; mark [Uncertain] if needed.

**Pass/Fail gates**

* JSON validity; no hidden CoT; reproducible extracts across runs (temp≤0.5) — consistent with PersonaForge quality gates.

## 6) Deployment Notes

**Version:** 1.0.0 • 2025-09-10 (Europe/Kyiv)

**Usage checklist**

1. Export `API_KEY` (or file Vault) and run the server. ([GitHub][1])
2. Paste **System Prompt** into your model’s system role.
3. Pick a template (Create/Improve/Convert/Evaluate/Deploy).
4. Run the **Golden-12**; fix any failing thresholds.
5. Monitor Prometheus metrics / logs; enable OTel if available. ([GitHub][1])

**Batch scoring example**

```bash
curl -s -H 'x-api-key: $API_KEY' -H 'content-type: application/json' \
  -d '{"items":[{"text":"a"},{"text":"hello doc","targets":["doc"]}]}' \
  http://127.0.0.1:8000/v1/score/batch
```

**Rollback**

* Revert to scoring-only path if `/v1/generate` misbehaves.
* Disable streaming; use plain generate + fit_length.

**Extension points**

* Add endpoints for QA (“evidence snippets”) and doc chunking.
* Wire Grafana dashboard from `grafana/dashboards/factsynth-overview.json`. ([GitHub][1])

## 7) Changelog

* **v2.4:** Introduced NEXUS prompts, prompt lint workflow, and YAML Golden-12 tests.
* **New:** FactSynth-specific System Prompt & task templates.
* **Aligned:** PersonaForge Prompt Blueprint phases + [Assumption] policy.
* **Added:** Golden-12 tailored to extractive/scoring workflows.
* **Hardened:** Problem+JSON echo; rate-limit guidance. ([GitHub][1])

## 8) Finalizer Mirror

You want me to deliver a production-ready prompt system for your FactSynth repo. I built a FactSynth-aware **System Prompt**, five **Task Templates** (create, improve, convert, evaluate, deploy), **Few-Shot** cURL examples, a **Golden-12** test set, a **Validation Report**, **Deployment Notes**, and a **Changelog**. It mirrors your PersonaForge blueprint and safety guardrails, speaks your API’s language (auth, rate limits, SSE/WS, Problem+JSON, metrics), and is ready to paste into your model plus README/docs immediately.

---

**Attribution to your prior assets:** Prompt phases & schema mirror PersonaForge (systemized blueprint, guardrails, tests).
**Facts on endpoints/features/limits/observability/streaming reflect your README (1.0.3, 2025-09-07).** ([GitHub][1])

If you want, I can also generate a drop-in `docs/PromptPack.md` and `tests/golden_factsynth.json` in your repo structure.

[1]: https://github.com/neuron7x/FactSynth "GitHub - neuron7x/FactSynth"
