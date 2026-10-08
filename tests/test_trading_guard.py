from api.trading_guard import (
    OrderProposal,
    RiskLimits,
    authorize_order,
    key_status,
    paper_mode,
)


def test_default_configuration_is_paper_only():
    assert paper_mode({}) is True


def test_key_management_reports_presence_without_exposing_values():
    status = key_status({
        "ALPACA_API_KEY": "redacted",
        "ALPACA_SECRET_KEY": "redacted",
        "OPENAI_API_KEY": "redacted",
    })
    assert status.broker_ready is True
    assert status.llm_ready is True


def test_missing_keys_are_not_treated_as_ready():
    status = key_status({})
    assert status.broker_ready is False
    assert status.llm_ready is False


def test_risk_gate_approves_safe_paper_order():
    decision = authorize_order(
        OrderProposal("AAPL", "buy", 2, 100),
        RiskLimits(max_notional=500),
    )
    assert decision.approved is True


def test_risk_gate_vetoes_oversized_order():
    decision = authorize_order(
        OrderProposal("AAPL", "buy", 10, 100),
        RiskLimits(max_notional=500),
    )
    assert decision.approved is False
    assert "max notional" in decision.reason


def test_risk_gate_vetoes_daily_loss_breach():
    decision = authorize_order(
        OrderProposal("AAPL", "buy", 1, 100, daily_pnl=-251),
        RiskLimits(max_daily_loss=250),
    )
    assert decision.approved is False


def test_live_execution_cannot_be_authorized():
    decision = authorize_order(
        OrderProposal("AAPL", "buy", 1, 100),
        paper=False,
    )
    assert decision.approved is False
    assert "live execution" in decision.reason
