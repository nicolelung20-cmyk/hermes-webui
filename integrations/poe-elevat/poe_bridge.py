#!/usr/bin/env python3
"""Explicit opt-in bridge from a local Hermes workflow to Poe's Chat Completions API.

No network request is made unless --execute is supplied. Poe API calls can consume
the account's points; this tool never runs automatically and never exposes local
Hermes tools to a remote model.
"""
from __future__ import annotations
import argparse
import json
import os
import sys
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

API_URL = "https://api.poe.com/v1/chat/completions"

def build_payload(model: str, prompt: str, max_tokens: int = 700) -> dict:
    if not model.strip():
        raise ValueError("A Poe model/bot name is required.")
    if not prompt.strip():
        raise ValueError("Prompt cannot be empty.")
    if not 1 <= max_tokens <= 4096:
        raise ValueError("max_tokens must be between 1 and 4096.")
    return {"model": model, "messages": [{"role": "user", "content": prompt}],
            "max_tokens": max_tokens, "stream": False}

def call_poe(payload: dict, api_key: str, timeout: int = 45) -> dict:
    if not api_key:
        raise ValueError("POE_API_KEY is not set.")
    request = Request(API_URL, data=json.dumps(payload).encode("utf-8"),
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json",
                 "Accept": "application/json"}, method="POST")
    try:
        with urlopen(request, timeout=timeout) as response:
            result = json.loads(response.read().decode("utf-8"))
    except HTTPError as exc:
        raise RuntimeError(f"Poe API returned HTTP {exc.code}.") from None
    except URLError as exc:
        raise RuntimeError(f"Could not reach Poe API: {exc.reason}") from None
    if not result.get("choices"):
        raise RuntimeError("Poe API returned no completion choices.")
    return result

def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model", required=True, help="Poe bot/model name")
    parser.add_argument("--prompt", required=True, help="Text to send")
    parser.add_argument("--max-tokens", type=int, default=700)
    parser.add_argument("--execute", action="store_true",
        help="Actually call Poe. This can consume points from your Poe account.")
    args = parser.parse_args(argv)
    try:
        payload = build_payload(args.model, args.prompt, args.max_tokens)
        if not args.execute:
            print(json.dumps({"mode": "dry_run", "endpoint": API_URL, "payload": payload,
                "network_request_made": False,
                "notice": "Poe calls may consume account points. Re-run with --execute to opt in."}, indent=2))
            return 0
        result = call_poe(payload, os.environ.get("POE_API_KEY", ""))
        message = result["choices"][0].get("message", {}).get("content", "")
        print(message if isinstance(message, str) else json.dumps(message))
        return 0
    except (ValueError, RuntimeError) as exc:
        print(f"poe_bridge: {exc}", file=sys.stderr)
        return 2

if __name__ == "__main__":
    raise SystemExit(main())
