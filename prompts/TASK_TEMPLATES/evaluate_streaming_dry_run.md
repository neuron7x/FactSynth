# Evaluate → Streaming Dry-Run (SSE)

**Call:** `POST /v1/stream` → receive SSE events.

**Events (validate `SCHEMAS/stream.event.schema.json`):**
```json
{"t":"token","v":"…","ts":"2025-09-09T12:00:00Z"}
{"t":"token","v":"…","ts":"2025-09-09T12:00:00Z"}
{"end":true,"tokens":123,"meta":{"tool":"stream","trace_id":"…","elapsed_ms":1234}}
```

