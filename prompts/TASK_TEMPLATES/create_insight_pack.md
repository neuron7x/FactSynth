# Create → Extractive Insight Pack

**Goal:** Produce `{title,summary,keywords}` from source text (extractive only).

**Call:** `POST /v1/generate`
```json
{
  "text": "<paste raw text>",
  "max_len": 300,
  "max_sentences": 2,
  "include_score": true
}
```

**Output (must validate `SCHEMAS/generate.output.schema.json`):**

```json
{
  "title": "…",
  "summary": "…",
  "keywords": ["k1","k2","k3"],
  "score": {"coverage":0.0,"entropy":0.0},
  "meta": {"tool":"generate","trace_id":"…","elapsed_ms":123}
}
```

**Rules:** title ≤ 12 words; summary ≤ `max_len` and ≤ `max_sentences`; all keywords present verbatim in source.

