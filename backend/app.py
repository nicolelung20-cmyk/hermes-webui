import os
from fastapi import FastAPI, HTTPException, Header
from alpaca.trading.client import TradingClient
from alpaca.trading.requests import MarketOrderRequest
from alpaca.trading.enums import OrderSide, TimeInForce

app = FastAPI(title="Hermes Paper Trading Runtime", version="1.0.0")

def client():
    key = os.getenv("HERMES_ALPACA_API_KEY")
    secret = os.getenv("HERMES_ALPACA_SECRET_KEY")
    paper = os.getenv("HERMES_ALPACA_PAPER", "true").lower() == "true"
    if not key or not secret:
        raise HTTPException(503, "Alpaca paper credentials are not configured")
    if not paper:
        raise HTTPException(403, "Live trading is disabled by Hermes runtime policy")
    return TradingClient(key, secret, paper=True)

def guard(token: str | None):
    expected = os.getenv("HERMES_RUNTIME_TOKEN")
    if expected and token != expected:
        raise HTTPException(401, "Invalid runtime token")

@app.get("/health")
def health():
    return {
        "ok": True,
        "service": "hermes-paper-runtime",
        "paper_only": True,
        "alpaca_credentials_configured": bool(os.getenv("HERMES_ALPACA_API_KEY") and os.getenv("HERMES_ALPACA_SECRET_KEY"))
    }

@app.get("/account")
def account(x_hermes_token: str | None = Header(default=None)):
    guard(x_hermes_token)
    a = client().get_account()
    return {"id": a.id, "status": a.status, "cash": str(a.cash), "equity": str(a.equity), "buying_power": str(a.buying_power)}

@app.get("/positions")
def positions(x_hermes_token: str | None = Header(default=None)):
    guard(x_hermes_token)
    return [
        {"symbol": p.symbol, "qty": str(p.qty), "market_value": str(p.market_value), "unrealized_pl": str(p.unrealized_pl)}
        for p in client().get_all_positions()
    ]

@app.get("/clock")
def clock(x_hermes_token: str | None = Header(default=None)):
    guard(x_hermes_token)
    c = client().get_clock()
    return {"timestamp": c.timestamp.isoformat(), "is_open": c.is_open, "next_open": c.next_open.isoformat(), "next_close": c.next_close.isoformat()}

@app.post("/orders")
def order(payload: dict, x_hermes_token: str | None = Header(default=None)):
    guard(x_hermes_token)
    symbol = str(payload.get("symbol", "")).upper()
    qty = payload.get("qty")
    side = str(payload.get("side", "")).lower()
    if not symbol or not qty or side not in {"buy", "sell"}:
        raise HTTPException(400, "symbol, qty and side are required")
    req = MarketOrderRequest(
        symbol=symbol,
        qty=qty,
        side=OrderSide.BUY if side == "buy" else OrderSide.SELL,
        time_in_force=TimeInForce.DAY,
    )
    o = client().submit_order(req)
    return {"id": str(o.id), "status": str(o.status), "symbol": o.symbol, "qty": str(o.qty), "side": str(o.side), "paper": True}
