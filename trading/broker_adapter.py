"""Broker adapter seam for promoting Hermes from paper to live execution.

No broker is selected or connected here. The adapter is disabled by default and
requires an explicit live_enabled=True at construction time. Production code
can provide a broker-specific transport without changing Hermes order logic.
"""
from __future__ import annotations

import json
from abc import ABC, abstractmethod
from datetime import datetime, timezone
from typing import Any
from urllib import request

from .paper_executor import ExecutionResult, OrderRequest


class BrokerTransport(ABC):
    """Minimal broker boundary used by the live executor."""

    @abstractmethod
    def post_order(self, payload: dict[str, str]) -> dict[str, Any]:
        raise NotImplementedError


class HttpBrokerTransport(BrokerTransport):
    """Generic JSON REST transport for a future broker implementation."""

    def __init__(self, endpoint: str, api_key: str, timeout: float = 10.0):
        if not endpoint:
            raise ValueError("broker endpoint is required")
        if not api_key:
            raise ValueError("broker API key is required")
        self.endpoint = endpoint.rstrip("/")
        self.api_key = api_key
        self.timeout = timeout

    def post_order(self, payload: dict[str, str]) -> dict[str, Any]:
        body = json.dumps(payload).encode("utf-8")
        req = request.Request(
            f"{self.endpoint}/orders",
            data=body,
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
                "Accept": "application/json",
            },
            method="POST",
        )
        with request.urlopen(req, timeout=self.timeout) as response:
            return json.loads(response.read().decode("utf-8"))


class LiveBrokerExecutor:
    """Translate Hermes orders to a broker transport.

    This class never enables live execution implicitly. Keeping the gate here
    means paper mode and live mode share one order contract and one risk seam.
    """

    paper_only = False

    def __init__(self, transport: BrokerTransport, *, live_enabled: bool = False):
        self.transport = transport
        self.live_enabled = live_enabled

    def submit(self, order: OrderRequest) -> ExecutionResult:
        if not self.live_enabled:
            raise RuntimeError("live trading is disabled")
        self._validate(order)

        payload = {
            "symbol": order.symbol.upper(),
            "side": order.side.upper(),
            "quantity": str(order.quantity),
            "limit_price": str(order.limit_price) if order.limit_price is not None else "",
            "reason": order.reason,
        }
        response = self.transport.post_order(payload)

        order_id = str(response.get("id") or response.get("order_id") or "")
        if not order_id:
            raise RuntimeError("broker response did not include an order id")

        status = str(response.get("status", "accepted")).upper()
        filled_quantity = str(response.get("filled_quantity", "0"))
        fill_price_value = response.get("fill_price")
        fill_price = None if fill_price_value is None else str(fill_price_value)

        return ExecutionResult(
            order_id=order_id,
            status=status,
            symbol=order.symbol.upper(),
            side=order.side.upper(),
            quantity=str(order.quantity),
            filled_quantity=filled_quantity,
            fill_price=fill_price,
            paper=False,
            timestamp=datetime.now(timezone.utc).isoformat(),
            reason=order.reason,
        )

    @staticmethod
    def _validate(order: OrderRequest) -> None:
        if not order.symbol.strip():
            raise ValueError("symbol is required")
        if order.side.upper() not in {"BUY", "SELL"}:
            raise ValueError("side must be BUY or SELL")
        if order.quantity <= 0:
            raise ValueError("quantity must be positive")
        if order.limit_price is not None and order.limit_price <= 0:
            raise ValueError("limit_price must be positive")
