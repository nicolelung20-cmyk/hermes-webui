"""Tests for the future live-broker adapter contract.

The adapter is deliberately tested against a fake transport so no real broker
credentials or network calls are ever required by the test suite.
"""
from decimal import Decimal

from trading.broker_adapter import BrokerAdapter, BrokerTransport, LiveBrokerExecutor
from trading.paper_executor import OrderRequest


class FakeTransport(BrokerTransport):
    def __init__(self):
        self.requests = []

    def post_order(self, payload):
        self.requests.append(payload)
        return {
            "id": "broker-123",
            "status": "accepted",
            "filled_quantity": "0",
            "fill_price": None,
        }


def test_live_broker_executor_translates_order_and_marks_result_live():
    transport = FakeTransport()
    executor = LiveBrokerExecutor(transport)

    result = executor.submit(
        OrderRequest("BTC-USD", "BUY", Decimal("0.001"), Decimal("100000"), "test")
    )

    assert transport.requests == [{
        "symbol": "BTC-USD",
        "side": "BUY",
        "quantity": "0.001",
        "limit_price": "100000",
        "reason": "test",
    }]
    assert result.order_id == "broker-123"
    assert result.status == "ACCEPTED"
    assert result.paper is False
    assert result.filled_quantity == "0"


def test_live_broker_executor_rejects_when_live_trading_is_not_explicitly_enabled():
    transport = FakeTransport()
    executor = LiveBrokerExecutor(transport, live_enabled=False)

    try:
        executor.submit(OrderRequest("BTC-USD", "BUY", Decimal("0.001")))
    except RuntimeError as exc:
        assert str(exc) == "live trading is disabled"
    else:
        raise AssertionError("expected live trading to be disabled")
