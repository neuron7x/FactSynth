# Deploy → Ops Health Check (Non-auth)

**Goal:** CI smoke test with no API key.

**Steps:**

- `GET /v1/healthz` → expect `200`.
- `GET /v1/version` → expect semver `x.y.z`.

**Expected JSON:**

```json
{ "healthz": "ok", "version": "1.0.3" }
```
