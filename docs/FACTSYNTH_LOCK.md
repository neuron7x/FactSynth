# FACTSYNTH_LOCK v1.1

`FACTSYNTH_LOCK` defines the payload exchanged with the `/v1/verify` endpoint.  It guards the API by requiring clients to send a well‑formed lock document before access is granted.

## Fields

| Name       | Type   | Description |
|------------|--------|-------------|
| `version`  | string | Schema version. Must be `"1.1"`. |
| `nonce`    | string | Client‑generated identifier that makes each lock unique. |
| `api_guard` | string | Guard token protecting the API. Expected value: `"factsynth-lock/v1.1"`. |

All fields are mandatory. Requests are rejected when `api_guard` does not exactly match the expected token.
