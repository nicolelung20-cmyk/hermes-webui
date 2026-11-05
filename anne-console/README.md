# ANNE Command Center

The original design artifact is `anne-console/index.html`. The live, authenticated Hermes-hosted page is served at:

`/static/anne-console.html`

## Connected capabilities

- Uses the existing Hermes WebUI same-origin session cookie and authentication boundary.
- Reads live agent-gateway health from `GET /api/health/agent`.
- Reads configured xAI provider/model metadata from `GET /api/providers`.
- Creates a new session with the selected Grok model through `POST /api/session/new`.
- Supports the native `x-ai` API-key provider and `xai-oauth` provider.
- Obtains the Hermes CSRF token from the authenticated app shell before session creation.
- Uses session-scoped model selection; it does not rewrite global provider defaults.
- Does not send a prompt, start a tool run, or make a billable Grok request when creating the session.

## Security and operating boundaries

- Provider credentials remain in the Hermes server's credential store / environment. The browser receives only provider metadata such as `has_key` and model IDs.
- No Supabase service key, xAI key, access token, or secret is embedded in browser assets.
- Same-origin requests use the existing Hermes session and CSRF protection.
- The page is served under Hermes' authenticated static-file route; do not publish it through an unauthenticated host.
- No API call is made to xAI until a user sends a message in the selected Grok session.
- No purchases, transfers, live trading, paid test prompts, or external tool execution are enabled by this page.
- Preserve production auth, data, secrets, scheduled jobs, and existing Hermes state.

## Verification

Focused contract tests:

```bash
./scripts/test.sh tests/test_anne_console_contract.py -v
```

JavaScript syntax check:

```bash
node --check static/anne-console.js
```

A configured provider is not proof of a successful xAI response. Do not claim end-to-end model availability until a separately approved, cost-aware staging request is performed.

## Staging and deployment

The feature is developed on `anne-web-client-foundation` and reviewed through PR #14. The available Railway `Staging` environment belongs to a different repository/service, so it is not a valid Hermes WebUI staging target. No Supabase development branch is created because branch compute may incur charges. Do not merge or deploy this change until an isolated Hermes WebUI staging target is identified and its tests pass.
