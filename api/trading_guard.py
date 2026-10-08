"""Paper-first trading control plane for Hermes.

This module is deliberately broker-agnostic. LLMs may propose an order, but
only this deterministic gate can authorize it for the execution adapter.
Live execution remains disabled until a separate, explicit policy is added.
"""

from __future__ import annotations

from dataclasses import dataclass
import os
from typing import Literal


Side = Literal["buy", "sell"]


@dataclass(frozen=True)
class RiskLimits:
    max_notional: float = 1_000.0
    max_position_notional: float = 2_500.0
    max_daily_loss: float = 250.0
    max_leverage: float = 1.0


@dataclass(frozen=True)
class OrderProposal:
    symbol: str
    side: Side
    quantity: float
    price: float
    current_position_notional: float = 0.0
    daily_pnl: float = 0.0
    leverage: float = 1.0

    @property
    def notional(self) -> float:
        return abs(self.quantity * self.price)


@dataclass(frozen=True)
class GateDecision:
    approved: bool
    reason: str
    paper_only: bool = True


@dataclass(frozen=True)
class KeyStatus:
    alpaca_key_present: bool
    alpaca_secret_present: bool
    openai_key_present: bool
    anthropic_key_present: bool

    @property
    def broker_ready(self) -> bool:
        return self.alpaca_key_present and self.alpaca_secret_present

    @property
    def llm_ready(self) -> bool:
        return self.openai_key_present or self.anthropic_key_present


def key_status(env: dict[str, str] | None = None) -> KeyStatus:
    values = env if env is not None else os.environ
    return KeyStatus(
        alpaca_key_present=bool(values.get("ALPACA_API_KEY")),
        alpaca_secret_present=bool(values.get("ALPACA_SECRET_KEY")),
        openai_key_present=bool(values.get("OPENAI_API_KEY")),
        anthropic_key_present=bool(values.get("ANTHROPIC_API_KEY")),
    )


def paper_mode(env: dict[str, str] | None = None) -> bool:
    values = env if env is not None else os.environ
    return values.get("ALPACA_PAPER", "true").strip().lower() in {
        "1", "true", "yes", "on"
    }


def authorize_order(
    proposal: OrderProposal,
    limits: RiskLimits = RiskLimits(),
    *,
    paper: bool = True,
) -> GateDecision:
    """Apply deterministic risk checks before any execution adapter is called."""

    if not paper:
        return GateDecision(False, "live execution is disabled by policy", True)

    if proposal.quantity <= 0 or proposal.price <= 0:
        return GateDecision(False, "quantity and price must be positive")

    if proposal.notional > limits.max_notional:
        return GateDecision(False, "order exceeds max notional")

    projected = abs(proposal.current_position_notional) + proposal.notional
    if projected > limits.max_position_notional:
        return GateDecision(False, "projected position exceeds max notional")

    if proposal.daily_pnl < -abs(limits.max_daily_loss):
        return GateDecision(False, "daily loss limit reached")

    if proposal.leverage > limits.max_leverage:
        return GateDecision(False, "leverage exceeds configured cap")

    return GateDecision(True, "risk checks passed")
