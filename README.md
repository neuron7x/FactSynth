# FactSynth

[![CI](https://github.com/neuron7x/FactSynth/actions/workflows/ci.yml/badge.svg)](https://github.com/neuron7x/FactSynth/actions/workflows/ci.yml)
[![CodeQL](https://github.com/neuron7x/FactSynth/actions/workflows/codeql.yml/badge.svg)](https://github.com/neuron7x/FactSynth/actions/workflows/codeql.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![GitHub stars](https://img.shields.io/github/stars/neuron7x/FactSynth?style=flat)](https://github.com/neuron7x/FactSynth/stargazers)

[![GitHub issues](https://img.shields.io/github/issues/neuron7x/FactSynth)](https://github.com/neuron7x/FactSynth/issues)
[![GitHub pull requests](https://img.shields.io/github/issues-pr/neuron7x/FactSynth)](https://github.com/neuron7x/FactSynth/pulls)
<!-- markdownlint-disable-next-line MD013 -->
[![docs](https://img.shields.io/badge/docs-OpenAPI%20Pages-0D1117.svg)](https://neuron7x.github.io/FactSynth/)

![FactSynth service banner](./assets/banner.svg)

FastAPI service for intent reflection and extractive generation with
SSE/WebSocket streaming,
Problem+JSON errors, rate limits, and rich observability.

Language: EN · [Українська](./README_UA.md)

## Table of Contents

- [About](#about)
- [Features](#features)
- [Tech Stack](#tech-stack)
- [Quick Start](#quick-start)
- [Installation](#installation)
- [Usage](#usage)
- [Examples](#examples)
- [Configuration](#configuration)
- [Demo & OpenAPI](#demo--openapi)
- [Observability](#observability)
- [Security](#security)
- [Roadmap](#roadmap)
- [Contributing](#contributing)
- [Maintainers](#maintainers)
- [License](#license)
- [Acknowledgements](#-acknowledgements)

## About

FactSynth is a FastAPI microservice for extractive text generation.
It targets teams needing secure, observable APIs that stream responses via
Server-Sent Events or WebSocket.
Clients receive standards-based Problem+JSON errors, and operators get metrics,
structured logs, and tracing hooks.

## Features

- Extractive generation — handled through FastAPI endpoints.
- Streaming responses — Server-Sent Events and WebSocket support.
- Security controls — API key header and optional IP allowlist.
- Rate limiting — sliding window limits per client.
- Problem+JSON — RFC 9457 compliant error payloads.
- Observability — Prometheus metrics, structured logs, and tracing hooks.

## Tech Stack

[![Python](assets/python.svg)](https://www.python.org/)
[![FastAPI](assets/fastapi.svg)](https://fastapi.tiangolo.com/)
[![Uvicorn](assets/uvicorn.svg)](https://www.uvicorn.org/)

Python 3.10+ · FastAPI 0.116 · Uvicorn 0.35  
See full [dependency graph](https://github.com/neuron7x/FactSynth/network/dependencies).

## Quick Start

```bash
git clone https://github.com/neuron7x/FactSynth.git
cd FactSynth
python -m venv .venv && source .venv/bin/activate
pip install -U pip && scripts/update_dev_requirements.sh && pip install -r requirements-dev.txt && pip install -e .
uvicorn factsynth_ultimate.app:app --reload
```

## Installation

Set up a local development environment:

1. **Clone and enter the repository**

   ```bash
   git clone https://github.com/neuron7x/FactSynth.git
   cd FactSynth
   ```

2. **Create a virtual environment**

   ```bash
   python -m venv .venv
   source .venv/bin/activate
   ```

3. **Install dependencies**

   ```bash
   pip install -U pip
   scripts/update_dev_requirements.sh
   pip install -r requirements-dev.txt && pip install -e .
   ```

### Development dependencies

`requests` powers the contract tests while `PyYAML` supports schema
validation. These and all other development dependencies live in
`pyproject.toml` under the `dev` extra and are **pinned** in
`requirements-dev.txt`. Regenerate the lockfile with
`scripts/update_dev_requirements.sh` (a thin wrapper around
`pip-compile`) and install with `pip install -r requirements-dev.txt`.
Pre-commit and the CI workflow both run `pip-compile` and fail if the
lockfile differs from `pyproject.toml`, ensuring the two stay in sync.

## Usage

Run the service locally:

1. **Activate the environment**

   ```bash
   source .venv/bin/activate
   ```

2. **Set an optional API key**

   ```bash
   export API_KEY=change-me
   ```

3. **Start the server**

   ```bash
   uvicorn factsynth_ultimate.app:app --host 0.0.0.0 --port 8000 --reload
   ```

Helper utilities such as the NLI classifier, simple claim evaluator, and
in-memory fixture retriever now live under the `factsynth_ultimate.services`
package. The legacy `app` module has been removed.

Or run with Docker:

```bash
docker run --rm -p 8000:8000 ghcr.io/neuron7x/factsynth:latest
```

## Examples

Perform a request and observe the response:

1. **Send a generation request**

   ```bash
   curl -s -X POST http://localhost:8000/v1/generate \
     -H "x-api-key: ${API_KEY:-test-key}" \
     -H "content-type: application/json" \
     -d '{"prompt": "Extract facts about water."}'
   ```

2. **Typical JSON response**

   ```json
   {
     "facts": ["Water freezes at 0°C", "Water boils at 100°C"]
   }
   ```

## Configuration

A Redis instance is required for rate limiting; set `RATE_LIMIT_REDIS_URL` to the connection URL.

| Variable | Default | Description |
| -------- | ------- | ----------- |
| `ENV` | `dev` | Environment name. |
| `HTTPS_REDIRECT` | `false` | Redirect HTTP to HTTPS. |
| `CORS_ALLOW_ORIGINS` | *(empty)* | Comma-separated origins. Defaults to denying all; set explicitly to allow specific domains. |
| `AUTH_HEADER_NAME` | `x-api-key` | Header carrying API key. |
| `IP_ALLOWLIST` | *(empty)* | Allowed IPs, comma-separated. |
| `RATE_LIMIT_REDIS_URL` | *(none)* | Redis connection URL for rate limiting. |
| `RATE_LIMIT_PER_KEY` | `120` | Requests per API key per minute. |
| `RATE_LIMIT_PER_IP` | `120` | Requests per IP per minute. |
| `RATE_LIMIT_PER_ORG` | `120` | Requests per organization per minute. |
| `SKIP_AUTH_PATHS` | `/v1/healthz,/metrics` | Paths that skip auth. |
| `LOG_LEVEL` | `INFO` | Logging verbosity level. |
| `VAULT_ADDR` | *(empty)* | URL of Vault server. |
| `VAULT_TOKEN` | *(empty)* | Authentication token for Vault. |
| `VAULT_PATH` | *(empty)* | Secret path in Vault. |

### Allowed origins

By default, no cross-origin requests are permitted. To enable cross-origin
access, set `CORS_ALLOW_ORIGINS` to a comma-separated list of allowed origins,
for example:

```bash
export CORS_ALLOW_ORIGINS="https://example.com,https://another.example"
```

To permit any origin (not recommended for production), use
`CORS_ALLOW_ORIGINS="*"`.

Secrets are supplied via GitHub Secrets or environment variables.

## Deployment

Refer to the [production runbook](docs/prod-runbook.md) for recommended CPU and
memory limits, `uvicorn` worker counts, timeout values, and `ulimit` settings.

## Demo & OpenAPI

View the [OpenAPI docs](https://neuron7x.github.io/FactSynth/).

```bash
curl -X POST http://localhost:8000/v1/generate \
  -H "x-api-key: $API_KEY" \
  -d '{"prompt": "extract facts"}'
```

## Observability

- Metrics exposed at `/metrics` for Prometheus.
- Structured logging with request IDs.
- Tracing hooks ready for OpenTelemetry.

## Security

See [SECURITY.md](SECURITY.md) for private vulnerability reporting.
CodeQL and Dependabot help monitor dependencies and code.

## Roadmap

Planned features and fixes are tracked in
[issues](https://github.com/neuron7x/FactSynth/issues).

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md).
This project follows the [Code of Conduct](CODE_OF_CONDUCT.md).

## Maintainers

- [Yaroslav (neuron7x)](https://github.com/neuron7x)

For guidelines on contributing, see the [contributing guide](CONTRIBUTING.md).

## License

[MIT](LICENSE)

## 🙏 Acknowledgements

<!-- ALL-CONTRIBUTORS-LIST:START - Do not remove or modify this section -->
<!-- prettier-ignore-start -->
<!-- markdownlint-disable -->
<table>
  <tbody>
    <tr>
      <td align="center" valign="top" width="12.5%"><a href="https://github.com/neuron7x"><img src="https://avatars.githubusercontent.com/u/206596321?v=4?s=80" width="80px;" alt="Yaroslav Vasylenko"/><br /><sub><b>Yaroslav Vasylenko</b></sub></a><br /><a href="https://github.com/neuron7x/FactSynth/commits?author=neuron7x" title="Code">💻</a></td>
    </tr>
  </tbody>
</table>

<!-- markdownlint-restore -->
<!-- prettier-ignore-end -->

<!-- ALL-CONTRIBUTORS-LIST:END -->

This project follows the all-contributors specification.
