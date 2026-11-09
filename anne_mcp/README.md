# ANNE Personal MCP

A small, private MCP bridge added alongside the existing Hermes Web UI. It does not replace Hermes, create another model runtime, or modify production data.

## Included tools

- `anne_system_status` — MCP and configured service addresses
- `hermes_status` — read-only HTTP reachability check for Hermes Web UI
- `studio_status` — read-only HTTP reachability check for the existing Local AI Studio
- `ollama_status` — Ollama reachability and installed model names
- `anne_safety_policy` — confirms read-only, zero-spend defaults

No shell execution, arbitrary file access, payment, trading, or production-write tools are exposed.

## Install on the Mac

From the existing `hermes-webui` checkout:

```bash
cd anne_mcp
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e .
```

Run directly with stdio (recommended for a local MCP client):

```bash
anne-mcp
```

Example MCP client configuration (adjust the absolute path):

```json
{
  "mcpServers": {
    "anne-personal": {
      "command": "/absolute/path/to/hermes-webui/anne_mcp/.venv/bin/anne-mcp",
      "env": {
        "ANNE_MCP_TRANSPORT": "stdio",
        "HERMES_BASE_URL": "http://127.0.0.1:3000",
        "ANNE_STUDIO_URL": "http://127.0.0.1:8787",
        "OLLAMA_BASE_URL": "http://127.0.0.1:11434"
      }
    }
  }
}
```

The MCP process starts locally and inherits the client's environment. The HTTP URLs above are defaults, not claims that those services are currently running; set them to the actual local ports used by the existing installation.

## Private HTTP transport (optional)

For a trusted local MCP client that requires HTTP, set `ANNE_MCP_TRANSPORT=streamable-http` and start `anne-mcp`. Keep it bound to loopback. To reach it from another device, use an authenticated private network proxy such as Tailscale Serve; do not expose it with a public tunnel or bind the MCP server to `0.0.0.0`.

## Verification

```bash
python -m unittest discover -s tests -v
```

The tests cover HTTP health parsing and ensure connection errors do not leak exception details. A live integration check still requires the Mac and its existing services to be online.
