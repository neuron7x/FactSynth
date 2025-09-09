# Convert → Intent Reflection

**Call:** `POST /v1/intent_reflector`

```json
{ "intent": "prep slides from Q4 ops plan", "length": 48 }
```

**Output (validate `SCHEMAS/intent_reflector.output.schema.json`):**

```json
{
  "intent": "Summarize Q4 plan for slides",
  "meta": { "tool": "intent_reflector", "trace_id": "…", "elapsed_ms": 7 }
}
```
