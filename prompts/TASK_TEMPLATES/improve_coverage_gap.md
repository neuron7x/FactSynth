# Improve → Coverage & Gap Report

**Call:** `POST /v1/score`
```json
{"text":"<doc>","targets":["term1","term2","term3"]}
```

**Output (validate `SCHEMAS/score.output.schema.json`):**

```json
{
  "covered":[{"target":"term1","score":0.92}],
  "missing":["termX","termY"],
  "meta":{"tool":"score","trace_id":"…","elapsed_ms":85}
}
```

**Notes:** rank `covered` by score desc; `missing` are targets with zero/low coverage; dedupe input targets.

