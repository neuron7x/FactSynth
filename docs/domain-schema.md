# Domain Schema

This document defines domain-level attributes required for claim ingestion.

## Attributes

### `region`
- **Type:** string (ISO 3166-1 alpha-2)
- **Required:** yes
- **Validation:** must be two uppercase letters (e.g. `US`).

### `language`
- **Type:** string (ISO 639-1)
- **Required:** yes
- **Validation:** must be two lowercase letters (e.g. `en`).

### `time_range`
- **Type:** object with `start` and `end` fields
- **Required:** yes
- **Validation:**
  - `start` and `end` are ISO 8601 timestamps.
  - `end` must not precede `start`.

### Evidence `source`
- **Type:** string (URL)
- **Required:** yes
- **Validation:** must be a valid HTTP or HTTPS URL.

## Schemas

JSON Schema: [`prompts/SCHEMAS/domain.schema.json`](../prompts/SCHEMAS/domain.schema.json)

Avro Schema: [`prompts/SCHEMAS/domain.avsc`](../prompts/SCHEMAS/domain.avsc)

