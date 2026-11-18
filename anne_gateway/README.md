# ANNE zero-spend local model gateway

This optional adapter exposes an OpenAI-compatible chat-completions endpoint
for Hermes WebUI while forwarding **only** to a local Ollama server. It is
intentionally cloud-blind: there is no Grok, xAI, or other hosted-provider
client in this implementation. The enforced spend cap is **$0**.

## Safety properties

- Binds to `127.0.0.1` by default; do not expose it to a LAN or public interface.
- Accepts only a loopback Ollama upstream URL ending in `/v1`.
- Allows only model IDs in `ANNE_LOCAL_MODELS`.
- Has no API-key storage and does not forward authorization headers.
- Does not log prompts, request headers, or credentials.
- Does not silently fall back to a cloud provider if Ollama is unavailable.
- Limits request bodies to 8 MiB.

## Start

Requires Python 3 and a running Ollama server with an OpenAI-compatible API
(default: `http://127.0.0.1:11434/v1`).

From the repository root:

```bash
ANNE_LOCAL_MODEL=qwen3:4b \
ANNE_LOCAL_MODELS=qwen3:4b,hermes3:3b-mylm \
python3 anne_gateway/local_gateway.py
```

Optional environment variables:

| Variable | Default | Purpose |
|---|---|---|
| `ANNE_GATEWAY_HOST` | `127.0.0.1` | Bind address; keep loopback |
| `ANNE_GATEWAY_PORT` | `8765` | Local listener port |
| `ANNE_OLLAMA_OPENAI_URL` | `http://127.0.0.1:11434/v1` | Loopback Ollama API |
| `ANNE_LOCAL_MODEL` | `qwen3:4b` | Default allowed model |
| `ANNE_LOCAL_MODELS` | default model | Comma-separated allowlist |
| `ANNE_GATEWAY_TIMEOUT` | `300` | Upstream timeout in seconds |

Health check:

```bash
curl -fsS http://127.0.0.1:8765/health
curl -fsS http://127.0.0.1:8765/v1/models
```

## Connect Hermes WebUI

In Hermes WebUI, add a custom OpenAI-compatible provider in **Settings →
Providers**:

- Base URL: `http://127.0.0.1:8765/v1`
- API key: leave blank if the UI permits; otherwise use a non-secret local
  placeholder only if the UI requires a value (the gateway ignores auth).
- Model: one of the configured local model IDs, e.g. `qwen3:4b`.

Keep Hermes WebUI and this gateway on the same host. If Hermes is running in a
container, `127.0.0.1` refers to that container; configure a safe host-loopback
route appropriate to the container runtime rather than exposing this service
publicly.

## Grok status

Grok is deliberately **not implemented or configured** in this zero-spend
branch. A SuperGrok subscription does not establish that API calls are free.
Do not add an xAI API key, enable hosted routing, or introduce paid fallback
until a separate explicit budget authorization is provided.

## Verification still required on the Mac

This repository change does not itself start services or modify the user's
Hermes configuration. Before connecting it to the real instance:

1. Run the gateway in an isolated terminal.
2. Confirm `/health` reports `grok_enabled: false` and `spend_cap_usd: 0`.
3. Confirm `/v1/models` lists only the configured local models.
4. Send a harmless test completion and verify it is served by Ollama.
5. Stop the gateway and confirm Hermes remains unchanged.

Do not replace existing Hermes profiles, credentials, sessions, or production
settings as part of this test.
