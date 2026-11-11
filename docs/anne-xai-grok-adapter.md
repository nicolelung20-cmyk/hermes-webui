# ANNE xAI Grok adapter

This repository includes an opt-in server-side adapter for the xAI Responses
API. It is deliberately disabled by default and makes no request during import
or startup.

## Defaults

- API base: `https://api.x.ai/v1`
- Endpoint: `POST /responses`
- Default model: `grok-4.7`
- API key environment variable: `XAI_API_KEY`
- Explicit enable switch: `ANNE_XAI_ENABLED=1`
- Response storage: `store: false`
- No SDK or new runtime dependency is required.

The Responses API is used rather than legacy Chat Completions because xAI
recommends Responses for new integrations, including reasoning and agentic
tool workflows. This adapter currently sends an input and returns the raw
response object; it does not execute returned tool calls or grant Grok access
to repository, shell, database, or deployment tools.

## Safe configuration

1. Store the xAI key in the server's approved secret store or local Keychain-
   backed environment injection. Never commit it, put it in browser JavaScript,
   add it to a YAML/JSON config file in the repository, or paste it into chat.
2. Keep `ANNE_XAI_ENABLED` unset until a separately approved live API test.
3. Set `XAI_API_KEY` only in the server process environment after confirming
   the secret storage and access scope.
4. Optionally set `ANNE_XAI_MODEL`; otherwise the adapter uses `grok-4.7`.
5. Call `api.xai_grok.create_response(...)` only from a trusted server-side
   integration after application-level authorization and spending checks.

An xAI API request may incur usage charges. This branch does not create an API
key, purchase credits, enable the adapter in a running environment, or make a
live API request. Do not set the enable switch as part of deployment without
separate approval.

## Example (server-side only)

```python
from api.xai_grok import create_response

result = create_response("Summarize the approved task.")
```

## Verification

Run the focused tests with the repository's supported test runner:

```bash
./scripts/test.sh tests/test_xai_grok_adapter.py
```

Tests mock the HTTP transport. They prove local request construction and
fail-closed behavior, not xAI service availability or account billing status.
