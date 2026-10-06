from __future__ import annotations

import json
import os
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from decimal import Decimal, InvalidOperation
from trading.paper_executor import OrderRequest, PaperExecutor

EXECUTOR = PaperExecutor()

class Handler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"
    def _send(self, status: int, payload: dict) -> None:
        raw = json.dumps(payload).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(raw)))
        self.send_header("Connection", "close")
        self.end_headers()
        self.wfile.write(raw)

    def do_GET(self):
        if self.path == "/health":
            self._send(200, {"ok": True, "paper": True, "broker_connected": False})
            return
        self._send(404, {"error": "not found"})

    def do_POST(self):
        if self.path != "/paper/order":
            self._send(404, {"error": "not found"})
            return
        try:
            length = int(self.headers.get("Content-Length", "0"))
            if length > 16384:
                raise ValueError("request too large")
            body = json.loads(self.rfile.read(length) or b"{}")
            quantity = Decimal(str(body.get("quantity", "")))
            limit_price = body.get("limit_price")
            order = OrderRequest(
                symbol=str(body.get("symbol", "")),
                side=str(body.get("side", "")),
                quantity=quantity,
                limit_price=Decimal(str(limit_price)) if limit_price is not None else None,
                reason=str(body.get("reason", "")),
            )
            result = EXECUTOR.submit(order)
            from dataclasses import asdict
            self._send(200, asdict(result))
        except (ValueError, InvalidOperation, json.JSONDecodeError) as exc:
            self._send(400, {"error": str(exc)})
        except Exception as exc:
            self._send(500, {"error": str(exc)})

    def log_message(self, *_):
        return

port = int(os.getenv("PORT", "8787"))
server = ThreadingHTTPServer(("0.0.0.0", port), Handler)
print(f"paper execution service listening on 0.0.0.0:{port}", flush=True)
server.serve_forever()
