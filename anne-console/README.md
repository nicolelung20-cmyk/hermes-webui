# ANNE Command Center — Web Client Foundation

This directory contains the first responsive browser UI shell for ANNE, intended to sit above the existing Hermes WebUI/runtime.

## Current scope

- Responsive navigation for Overview, Agents, Activity, Permissions, and Connections.
- Explicit separation of orchestrator (ANNE), reasoning provider (Grok), and executor (Hermes).
- Honest unverified/offline states; no fake connection indicators.
- Visible $0-spend default and approval gates for financial, production, and external actions.
- No credentials, API keys, or private endpoints embedded in the client.

## Important: UI foundation, not connected runtime

`index.html` is currently a static UI-only scaffold. It does not call Hermes, Grok, Tailscale, or Supabase; it does not execute tools or change settings. Do not treat the status labels as live health checks.

## Integration sequence

1. Serve this UI only through the authenticated local Hermes/ANNE backend.
2. Add a backend-owned agent registry and health-check endpoints; the browser must never receive provider secrets.
3. Route model selection through Hermes' supported provider configuration, with Grok as the intended primary reasoning provider and an explicitly configured local fallback.
4. Add approval middleware and append-only audit records before enabling any mutating tool.
5. Use Tailscale/private ingress for remote access. Do not expose an unauthenticated public endpoint.
6. Verify with isolated staging state and tests before considering production integration.

## Safety constraints

- Preserve existing Hermes state, Supabase authentication/data, production functions, secrets, and scheduled jobs.
- Do not print or commit credentials.
- Do not enable purchases, transfers, live trading, paid API usage, or other real-money actions without explicit approval.
- Keep spending disabled by default.
