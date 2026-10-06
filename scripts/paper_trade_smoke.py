#!/usr/bin/env python3
"""Smoke-test the Hermes paper execution contract."""
from trading.paper_executor import simulate_order

result = simulate_order("BTC-USD", "BUY", "0.001", "100000")
assert result["status"] == "SIMULATED"
assert result["paper"] is True
assert result["filled_quantity"] == "0.001"
print("PAPER_EXECUTION_OK")
print(result["order_id"])
