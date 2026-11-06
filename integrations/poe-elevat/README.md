# Poe ↔ Hermes bridge (local, opt-in)

This adapter lets a local Hermes workflow call a Poe bot/model through Poe's
OpenAI-compatible Chat Completions API. It is a one-way model-provider bridge:
it does not expose Hermes shell, files, browser, database, payment, or trading
tools to Poe. A remote Poe model receives only the prompt you explicitly send.

## Cost and safety defaults

- Dry-run is the default; it prints the request without making a network call.
- A real call requires the explicit `--execute` flag and `POE_API_KEY`.
- Poe API requests can consume points from the Poe account. This adapter does
  not promise free inference and has no automatic retry or background mode.
- Never put the key in source control, chat, command history, or logs.
- Never send secrets, customer data, private records, or unrestricted tool
  output to a third-party model.
- No live purchases, subscriptions, trades, transfers, or checkout actions.

## Run a dry-run

```bash
python3 integrations/poe-elevat/poe_bridge.py --model "Claude-Sonnet-4.6" \
  --prompt "Draft a one-page workflow brief for a small business"
```

No network request is made above.

## Opt in to a Poe request

Only after reviewing the prompt and accepting that Poe points may be consumed:

```bash
export POE_API_KEY="(set privately in your shell; do not paste it into chat)"
python3 integrations/poe-elevat/poe_bridge.py --model "Claude-Sonnet-4.6" \
  --prompt "Draft a one-page workflow brief for a small business" --execute
```

Use a private shell secret manager or temporary environment injection rather
than saving the key in a project `.env` file. Unset it after use.

## Hermes integration

Configure a dedicated Hermes provider/profile to invoke this adapter only as
an explicit model call. Keep it separate from the default local model. Do not
register the adapter as a tool executor and do not forward Hermes tool schemas.
The precise provider registration depends on the installed Hermes version and
profile configuration; verify the local Hermes provider contract before
changing a live profile. Until then, run the CLI manually from a Hermes task.

## Tests

From this directory: `python3 -m unittest -v`. Tests mock HTTP; they do not
call Poe or spend points.
