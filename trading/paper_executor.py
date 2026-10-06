"""Deterministic paper-trading executor for Hermes.

This module intentionally has no broker/network integration. It provides the
execution contract Hermes can use to validate strategy -> risk gate -> order
flow without submitting real orders.
"""
from __future__ import annotations

from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from decimal import Decimal
from uuid import uuid4


@dataclass(frozen=True)
class OrderRequest:
    symbol: str
    side: str
    quantity: Decimal
    limit_price: Decimal | None = None
    reason: str = ""


@dataclass(frozen=True)
class ExecutionResult:
    order_id: str
    status: str
    symbol: str
    side: str
    quantity: str
    filled_quantity: str
    fill_price: str | None
    paper: bool
    timestamp: str
    reason: str


class PaperExecutor:
    """Validate and record orders without contacting a broker."""

    paper_only = True

    def submit(self, order: OrderRequest) -> ExecutionResult:
        if not order.symbol.strip():
            raise ValueError("symbol is required")
        if order.side.upper() not in {"BUY", "SELL"}:
            raise ValueError("side must be BUY or SELL")
        if order.quantity <= 0:
            raise ValueError("quantity must be positive")
        if order.limit_price is not None and order.limit_price <= 0:
            raise ValueError("limit_price must be positive")

        now = datetime.now(timezone.utc).isoformat()
        return ExecutionResult(
            order_id=f"paper-{uuid4().hex[:16]}",
            status="SIMULATED",
            symbol=order.symbol.upper(),
            side=order.side.upper(),
            quantity=str(order.quantity),
            filled_quantity=str(order.quantity),
            fill_price=str(order.limit_price) if order.limit_price is not None else None,
            paper=True,
            timestamp=now,
            reason=order.reason,
        )


def simulate_order(symbol: str, side: str, quantity: str, limit_price: str | None = None) -> dict:
    """Small JSON-friendly entry point for smoke tests and future API wiring."""
    result = PaperExecutor().submit(
        OrderRequest(
            symbol=symbol,
            side=side,
            quantity=Decimal(quantity),
            limit_price=Decimal(limit_price) if limit_price is not None else None,
        )
    )
    return asdict(result)
