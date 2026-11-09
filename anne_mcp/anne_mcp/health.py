"""Read-only health probes for the ANNE personal MCP."""
from __future__ import annotations

import json
import urllib.error
import urllib.request
from typing import Any


def probe_http(url: str, timeout: float = 2.5) -> dict[str, Any]:
    """Return a small, secret-free summary of an HTTP endpoint."""
    request = urllib.request.Request(url, headers={"User-Agent": "ANNE-Personal-MCP/0.1"})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            body = response.read(256_000)
            result: dict[str, Any] = {
                "reachable": True,
                "status_code": response.status,
                "content_type": response.headers.get("Content-Type", ""),
            }
            if "json" in result["content_type"].lower():
                try:
                    result["json"] = json.loads(body.decode("utf-8"))
                except (UnicodeDecodeError, json.JSONDecodeError):
                    result["json"] = None
            return result
    except urllib.error.HTTPError as exc:
        return {"reachable": True, "status_code": exc.code, "http_error": True}
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        reason = getattr(exc, "reason", exc)
        return {"reachable": False, "error": type(reason).__name__}
