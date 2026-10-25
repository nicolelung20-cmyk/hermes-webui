#!/usr/bin/env python3
"""Read-only FOMO API research report. Never submits trades or transactions."""
from __future__ import annotations

import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from typing import Any

BASE_URL = "https://api.fomoapi.io"
TIMEOUT_SECONDS = 20


class FomoApiError(RuntimeError):
    pass


def get_json(path: str, api_key: str) -> tuple[dict[str, Any], dict[str, str]]:
    url = BASE_URL + path
    request = urllib.request.Request(
        url,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Accept": "application/json",
            "User-Agent": "ANNE-FOMO-ReadOnly-Agent/1.0",
        },
        method="GET",
    )
    try:
        with urllib.request.urlopen(request, timeout=TIMEOUT_SECONDS) as response:
            body = response.read().decode("utf-8")
            return json.loads(body), {k.lower(): v for k, v in response.headers.items()}
    except urllib.error.HTTPError as exc:
        # Do not print request headers or credentials.
        if exc.code == 401:
            raise FomoApiError("Authentication failed: check the FOMO_API_KEY secret.") from None
        if exc.code == 402:
            raise FomoApiError("FOMO API credits exhausted; agent will not upgrade or pay.") from None
        if exc.code == 429:
            raise FomoApiError("FOMO API rate limit reached; retry on the next scheduled run.") from None
        raise FomoApiError(f"FOMO API returned HTTP {exc.code}.") from None
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
        raise FomoApiError(f"FOMO API request failed ({type(exc).__name__}); no action taken.") from None


def money(value: Any) -> str:
    if not isinstance(value, (int, float)):
        return "n/a"
    return f"${value:,.0f}"


def build_report() -> str:
    api_key = os.environ.get("FOMO_API_KEY", "").strip()
    if not api_key:
        raise FomoApiError("FOMO_API_KEY is not configured. Add it as a server-side GitHub Actions secret.")

    # Two bounded read-only calls per run; ~500 credits if both are metered.
    leaderboard, lb_headers = get_json("/v2/leaderboard/24h?limit=10", api_key)
    trending, token_headers = get_json("/v2/leaderboard/tokens/trending?limit=10", api_key)

    lines = [
        "# ANNE FOMO Research Brief",
        "",
        f"Generated: {datetime.now(timezone.utc).isoformat(timespec='seconds')}",
        "",
        "> Research only. This report is not financial advice. No wallet signing, purchases, or trades are performed.",
        "",
        "## 24-hour trader leaderboard",
        "",
        "| Rank | Trader | Reported PnL | Volume | Trades | Followers |",
        "|---:|---|---:|---:|---:|---:|",
    ]
    traders = leaderboard.get("traders", [])
    if not isinstance(traders, list) or not traders:
        lines.append("| — | No trader rows returned | — | — | — | — |")
    else:
        for row in traders[:10]:
            if not isinstance(row, dict):
                continue
            handle = str(row.get("handle") or "unknown").replace("|", "\\|")
            lines.append(
                f"| {row.get('rank', '—')} | {handle} | {money(row.get('pnlUsd'))} | "
                f"{money(row.get('volumeUsd'))} | {row.get('trades', 'n/a')} | "
                f"{row.get('followers', 'n/a')} |"
            )

    lines.extend(["", "## Trending tokens", ""])
    tokens = trending.get("tokens", [])
    if trending.get("available") is False:
        lines.append("The trending-token board is currently unavailable.")
    elif not isinstance(tokens, list) or not tokens:
        lines.append("No trending-token rows returned.")
    else:
        lines.extend([
            "| Rank | Token | Network | 24h change | Market cap | Holders |",
            "|---:|---|---|---:|---:|---:|",
        ])
        for row in tokens[:10]:
            if not isinstance(row, dict):
                continue
            token = row.get("token") if isinstance(row.get("token"), dict) else {}
            name = str(token.get("symbol") or token.get("name") or "unknown").replace("|", "\\|")
            network = str(row.get("network") or "n/a").replace("|", "\\|")
            change = row.get("change24h")
            change_text = f"{change:+.2f}%" if isinstance(change, (int, float)) else "n/a"
            lines.append(
                f"| {row.get('rank', '—')} | {name} | {network} | {change_text} | "
                f"{money(row.get('marketCapUsd'))} | {row.get('holders', 'n/a')} |"
            )

    costs = []
    for label, headers in (("leaderboard", lb_headers), ("trending", token_headers)):
        costs.append(f"- {label}: {headers.get('x-credits-cost', 'not reported')} credits")
    remaining = token_headers.get("x-credits-remaining", lb_headers.get("x-credits-remaining", "not reported"))
    lines.extend([
        "",
        "## API usage",
        *costs,
        f"- Credits remaining: {remaining}",
        "",
        "## Interpretation cautions",
        "- Leaderboard PnL is reported by FOMO; its exact realized/unrealized and fee treatment may vary.",
        "- Rankings and token momentum are descriptive, not a prediction of future returns.",
        "- Verify token contract, liquidity, ownership, holder concentration, and independent market data before considering any decision.",
        "- The agent never buys tokens, connects to a wallet, signs messages, or upgrades the API plan.",
        "",
    ])
    return "\n".join(lines)


if __name__ == "__main__":
    try:
        print(build_report())
    except FomoApiError as exc:
        print(f"FOMO_AGENT_ERROR: {exc}", file=sys.stderr)
        sys.exit(2)
