"""Opt-in xAI Grok Responses API adapter for ANNE integrations.

No network request is made unless ANNE_XAI_ENABLED=1 and XAI_API_KEY is
present. Credentials are read only from the server process environment and
are never included in errors or logs.
"""
from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from typing import Any

DEFAULT_BASE_URL = "https://api.x.ai/v1"
DEFAULT_MODEL = "grok-4.7"
DEFAULT_TIMEOUT_SECONDS = 120


class XAIAdapterError(RuntimeError):
    """Sanitized xAI adapter error; never contains credentials or response bodies."""


def is_enabled() -> bool:
    """Return whether outbound xAI calls have explicitly been enabled."""
    return os.getenv("ANNE_XAI_ENABLED", "").strip().lower() in {"1", "true", "yes"}


def create_response(
    input_data: str | list[dict[str, Any]],
    *,
    model: str | None = None,
    timeout: int = DEFAULT_TIMEOUT_SECONDS,
) -> dict[str, Any]:
    """Create a Grok Responses API result using server-side environment credentials.

    This function performs a billable external API request. It is disabled by
    default and requires both ANNE_XAI_ENABLED=1 and XAI_API_KEY.
    """
    if not is_enabled():
        raise XAIAdapterError("xAI adapter is disabled; set ANNE_XAI_ENABLED=1 to enable it.")

    api_key = os.getenv("XAI_API_KEY", "").strip()
    if not api_key:
        raise XAIAdapterError("xAI API key is not configured in the server environment.")

    if isinstance(timeout, bool) or not isinstance(timeout, int) or timeout < 1 or timeout > 3600:
        raise ValueError("timeout must be an integer between 1 and 3600 seconds")

    payload = {
        "model": (model or os.getenv("ANNE_XAI_MODEL") or DEFAULT_MODEL).strip(),
        "input": input_data,
        "store": False,
    }
    if not payload["model"]:
        raise ValueError("model must be a non-empty string")

    body = json.dumps(payload).encode("utf-8")
    request = urllib.request.Request(
        DEFAULT_BASE_URL + "/responses",
        data=body,
        headers={
            "Authorization": "Bearer " + api_key,
            "Content-Type": "application/json",
            "Accept": "application/json",
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            decoded = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        raise XAIAdapterError(f"xAI request failed (HTTP {exc.code}).") from None
    except urllib.error.URLError:
        raise XAIAdapterError("xAI request could not reach the API endpoint.") from None
    except (TimeoutError, json.JSONDecodeError, UnicodeDecodeError):
        raise XAIAdapterError("xAI request timed out or returned an invalid response.") from None

    if not isinstance(decoded, dict):
        raise XAIAdapterError("xAI returned an unexpected response format.")
    return decoded
