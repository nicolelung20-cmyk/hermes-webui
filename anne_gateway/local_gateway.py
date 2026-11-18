#!/usr/bin/env python3
"""ANNE zero-spend local OpenAI-compatible gateway.

This gateway only forwards to a loopback Ollama server. It has no cloud
provider integration and cannot send requests to Grok or any other paid API.
"""
from __future__ import annotations

import json
import os
import re
import urllib.error
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any

HOST = os.environ.get("ANNE_GATEWAY_HOST", "127.0.0.1")
PORT = int(os.environ.get("ANNE_GATEWAY_PORT", "8765"))
UPSTREAM = os.environ.get("ANNE_OLLAMA_OPENAI_URL", "http://127.0.0.1:11434/v1").rstrip("/")
DEFAULT_MODEL = os.environ.get("ANNE_LOCAL_MODEL", "qwen3:4b").strip()
MODELS = tuple(
    item.strip()
    for item in os.environ.get("ANNE_LOCAL_MODELS", DEFAULT_MODEL).split(",")
    if item.strip()
)
MAX_BODY = 8 * 1024 * 1024
TIMEOUT = float(os.environ.get("ANNE_GATEWAY_TIMEOUT", "300"))


def _valid_loopback_url(value: str) -> bool:
    # Deliberately restrict upstream to localhost; no remote proxying/SSRF.
    return bool(re.match(r"^https?://(127\.0\.0\.1|localhost|\[::1\])(?::\d+)?/v1$", value))


if HOST not in {"127.0.0.1", "localhost"}:
    raise SystemExit("ANNE_GATEWAY_HOST must be 127.0.0.1 or localhost; public binds are disabled.")
if not _valid_loopback_url(UPSTREAM):
    raise SystemExit("ANNE_OLLAMA_OPENAI_URL must be a loopback /v1 URL.")
if not MODELS or DEFAULT_MODEL not in MODELS:
    raise SystemExit("Configure ANNE_LOCAL_MODEL and include it in ANNE_LOCAL_MODELS.")


class Handler(BaseHTTPRequestHandler):
    server_version = "ANNE-Local-Gateway/1.0"

    def log_message(self, fmt: str, *args: Any) -> None:
        # Avoid logging prompts, headers, tokens, or other request content.
        return

    def _json(self, status: int, payload: dict[str, Any]) -> None:
        raw = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(raw)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(raw)

    def do_GET(self) -> None:
        if self.path == "/health":
            self._json(200, {
                "ok": True,
                "provider": "ollama-local",
                "models": list(MODELS),
                "grok_enabled": False,
                "spend_cap_usd": 0,
            })
            return
        if self.path == "/v1/models":
            self._json(200, {
                "object": "list",
                "data": [
                    {"id": model, "object": "model", "owned_by": "local"}
                    for model in MODELS
                ],
            })
            return
        self._json(404, {"error": {"message": "Not found", "type": "not_found"}})

    def do_POST(self) -> None:
        if self.path != "/v1/chat/completions":
            self._json(404, {"error": {"message": "Not found", "type": "not_found"}})
            return
        try:
            length = int(self.headers.get("Content-Length", "0"))
        except ValueError:
            length = 0
        if length <= 0 or length > MAX_BODY:
            self._json(413, {"error": {"message": "Invalid or oversized request body", "type": "invalid_request_error"}})
            return
        try:
            payload = json.loads(self.rfile.read(length))
        except (json.JSONDecodeError, UnicodeDecodeError):
            self._json(400, {"error": {"message": "Request body must be valid JSON", "type": "invalid_request_error"}})
            return
        if not isinstance(payload, dict):
            self._json(400, {"error": {"message": "Request body must be a JSON object", "type": "invalid_request_error"}})
            return
        model = str(payload.get("model") or DEFAULT_MODEL)
        if model not in MODELS:
            self._json(403, {"error": {
                "message": "Model is not allowlisted for zero-spend local routing",
                "type": "model_not_allowed",
            }})
            return
        payload["model"] = model
        body = json.dumps(payload).encode("utf-8")
        request = urllib.request.Request(
            UPSTREAM + "/chat/completions",
            data=body,
            headers={"Content-Type": "application/json", "Accept": "text/event-stream, application/json"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=TIMEOUT) as response:
                content_type = response.headers.get("Content-Type", "application/json")
                self.send_response(response.status)
                self.send_header("Content-Type", content_type)
                self.send_header("Cache-Control", "no-store")
                self.send_header("X-ANNE-Provider", "ollama-local")
                self.send_header("Connection", "close")
                self.end_headers()
                while True:
                    chunk = response.read(64 * 1024)
                    if not chunk:
                        break
                    self.wfile.write(chunk)
                    self.wfile.flush()
        except urllib.error.HTTPError as exc:
            error_body = exc.read(MAX_BODY)
            self.send_response(exc.code)
            self.send_header("Content-Type", exc.headers.get("Content-Type", "application/json"))
            self.send_header("Content-Length", str(len(error_body)))
            self.end_headers()
            self.wfile.write(error_body)
        except (urllib.error.URLError, TimeoutError, OSError) as exc:
            self._json(502, {"error": {
                "message": "Local Ollama endpoint unavailable; no cloud fallback is configured",
                "type": "local_upstream_unavailable",
                "detail": str(getattr(exc, "reason", exc))[:240],
            }})


if __name__ == "__main__":
    print(f"ANNE local gateway listening on http://{HOST}:{PORT}")
    print(f"Upstream: {UPSTREAM} | models: {', '.join(MODELS)} | Grok: disabled | spend cap: $0")
    ThreadingHTTPServer((HOST, PORT), Handler).serve_forever()
