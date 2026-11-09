"""ANNE's local, read-only MCP bridge to the existing Hermes and studio services."""
from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from typing import Any

from mcp.server.fastmcp import FastMCP

from .health import probe_http

mcp = FastMCP("ANNE Personal MCP")


def _env(name: str, default: str) -> str:
    return os.environ.get(name, default).rstrip("/")


def _safe_service_status(name: str, url: str) -> dict[str, Any]:
    return {"service": name, "url": url, **probe_http(url)}


@mcp.tool()
def anne_system_status() -> str:
    """Show ANNE MCP status and the configured local service addresses."""
    data = {
        "name": "ANNE Personal MCP",
        "version": "0.1.0",
        "status": "running",
        "checked_at": datetime.now(timezone.utc).isoformat(),
        "transport": os.environ.get("ANNE_MCP_TRANSPORT", "stdio"),
        "services": {
            "hermes": _env("HERMES_BASE_URL", "http://127.0.0.1:3000"),
            "studio": _env("ANNE_STUDIO_URL", "http://127.0.0.1:8787"),
            "ollama": _env("OLLAMA_BASE_URL", "http://127.0.0.1:11434"),
        },
        "safety": {
            "mode": "read-only",
            "automatic_spending": False,
            "external_network_binding": False,
            "secrets_in_tool_output": False,
        },
    }
    return json.dumps(data, indent=2)


@mcp.tool()
def hermes_status() -> str:
    """Check whether the configured Hermes Web UI responds over local HTTP."""
    url = _env("HERMES_BASE_URL", "http://127.0.0.1:3000")
    return json.dumps(_safe_service_status("Hermes", url), indent=2)


@mcp.tool()
def studio_status() -> str:
    """Check whether the existing ANNE Local AI Studio responds over HTTP."""
    url = _env("ANNE_STUDIO_URL", "http://127.0.0.1:8787")
    return json.dumps(_safe_service_status("ANNE Local AI Studio", url), indent=2)


@mcp.tool()
def ollama_status() -> str:
    """Check Ollama and list locally installed model names, if available."""
    base = _env("OLLAMA_BASE_URL", "http://127.0.0.1:11434")
    result = probe_http(f"{base}/api/tags")
    models: list[str] = []
    payload = result.get("json")
    if isinstance(payload, dict) and isinstance(payload.get("models"), list):
        models = [item["name"] for item in payload["models"] if isinstance(item, dict) and isinstance(item.get("name"), str)]
    return json.dumps({"service": "Ollama", "url": base, **{k: v for k, v in result.items() if k != "json"}, "models": models}, indent=2)


@mcp.tool()
def anne_safety_policy() -> str:
    """Return ANNE's active safety defaults; this MCP exposes no write or payment tools."""
    return json.dumps({
        "mode": "read-only",
        "automatic_spending": False,
        "purchases_and_subscriptions": "explicit approval required",
        "production_changes": "explicit approval required",
        "live_payments_and_trading": "not exposed",
        "shell_access": "not exposed",
        "arbitrary_file_access": "not exposed",
    }, indent=2)


def main() -> None:
    transport = os.environ.get("ANNE_MCP_TRANSPORT", "stdio").lower()
    if transport not in {"stdio", "streamable-http"}:
        raise SystemExit("ANNE_MCP_TRANSPORT must be 'stdio' or 'streamable-http'")
    # FastMCP's HTTP transport defaults to loopback; do not bind to 0.0.0.0.
    mcp.run(transport=transport)


if __name__ == "__main__":
    main()
