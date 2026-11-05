# Hermes Proof-of-Alpha: Exit Decision Matrix

Status: Specification created; not yet connected to or executed by the Hermes runtime.
Safety invariant: PAPER TRADING ONLY. This matrix must never submit live orders.

## Decision order (highest priority wins)

| Priority | Condition | Decision | Required action |
|---:|---|---|---|
| 1 | Broker/account state unknown, stale prices, data gap, order/position mismatch, or risk engine unavailable | HALT / NO NEW ORDERS | Freeze entries; reconcile positions and open orders; alert operator. Do not blindly market-sell an unknown position. |
| 2 | Hard risk limit breached (daily loss, exposure, max position, drawdown, or configured stop) | RISK EXIT | Cancel eligible entry orders; reduce/close paper positions through the verified broker adapter; persist reason and fills. |
| 3 | Strategy invalidation / thesis-break rule fires | EXIT POSITION | Submit paper exit for the affected position; confirm fill or manage partial/rejected order. |
| 4 | Take-profit / trailing-stop / time-stop condition fires | EXIT POSITION | Apply the configured exit rule, account for fees/slippage, and verify final position quantity is zero or explicitly tracked. |
| 5 | Alpha evidence degrades below the pre-registered threshold or benchmark-adjusted performance fails its test | DISABLE STRATEGY | Stop new entries; retain logs; conduct a frozen-parameter review. Do not optimize on the test set and call it out-of-sample. |
| 6 | No exit condition; data fresh; risk checks pass | HOLD | Continue monitoring; do not add to a position unless the entry policy independently authorizes it. |

## Mandatory guardrails

- Fail closed for new entries whenever required data or risk state is unknown.
- Never treat a missing stop price, missing fill, or API timeout as a successful exit.
- Use idempotent client order IDs; check existing orders before retrying.
- Track requested quantity, filled quantity, remaining quantity, average fill price, fees, timestamps, and rejection reason.
- A cancel request is not a confirmed cancellation; query the broker until terminal state or escalate.
- Keep HERMES_LIVE=0; use the paper broker adapter only.
- Never place credentials, API keys, or database passwords in this document or logs.

## Proof required before declaring alpha

1. Reproducible backtest with dated, versioned data and no look-ahead leakage.
2. Net returns after fees, spread, slippage, and turnover.
3. Benchmark-adjusted alpha plus confidence interval / statistical test.
4. Out-of-sample results using parameters frozen before evaluation.
5. Forward paper trading with signal → order → fill → ledger reconciliation.
6. Fault tests: stale feed, rejected order, partial fill, timeout, duplicate signal, and risk-limit breach.
7. Independently verified daily loss and exposure limits.

## Explicit exit / promotion gates

- PASS — continue paper validation: all safety/fault tests pass; results are reproducible; no unexplained ledger differences.
- HOLD — insufficient evidence: sample size or confidence is insufficient, or performance is not robust.
- DISABLE — failed strategy: net benchmark-adjusted performance fails the pre-registered test or drawdown/risk limits fail.
- NO LIVE PROMOTION: this matrix does not authorize live trading. Any live-trading change requires a separate explicit review and approval.

## Runtime integration contract

The executor should accept a normalized snapshot of market-data freshness, position, open orders, risk metrics, and strategy exit signals. It should return one of: HALT, RISK_EXIT, EXIT_POSITION, DISABLE_STRATEGY, or HOLD, with a machine-readable reason and audit timestamp. Unknown or contradictory state resolves to HALT for new orders.

Verification note: publishing this specification does not prove it is wired into agent_jobs, that any order executed, or that alpha exists. Those claims require runtime logs and broker-paper reconciliation.
