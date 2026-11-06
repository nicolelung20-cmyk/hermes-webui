# ANNE Claude Model Gateway — Zero-Spend Readiness

Status: **Prepared specification only**. No provider credentials, paid calls, hosting, deployment, or live workflows were created.

## Decision

Use a provider-neutral model gateway with a dedicated Anthropic Claude adapter. Keep the gateway API-compatible with ANNE and n8n. Hermes remains the local execution agent and approval boundary. Do not use browser-cookie/session scraping, reverse-engineered consumer-app endpoints, or an assumed Claude app subscription as API authentication.

Recommended logical path:

`iPhone PWA → ANNE API/auth → policy + task queue → model gateway → approved provider adapter`
`ANNE task queue → n8n webhook/workflow → Hermes (only when connected and explicitly approved)`

Claude is a reasoning provider, not the workflow executor. It returns structured proposals. ANNE validates schema, permissions, and risk before n8n/Hermes can perform any action.

## Important billing finding

Anthropic's official API documentation requires a Claude Console account and API key (or configured workload identity) for direct API access. API usage is metered. The Help Center states that API usage is normally paid with prepaid usage credits; certain eligible Max, Ultra, and Team plans may include monthly API credits after linking a Console organization. A Claude consumer-app subscription must not be assumed to provide free API access.

References:
- https://platform.claude.com/docs/en/api/overview
- https://support.claude.com/en/articles/8977456-how-do-i-pay-for-my-claude-api-usage
- https://platform.claude.com/docs/en/about-claude/pricing

**Zero-spend gate:** Claude adapter remains disabled unless the owner verifies that the account has available included credits with no auto-reload and no paid-credit balance requirement. Do not send even a test request until that condition is explicitly approved. No API key should be pasted into chat, committed to Git, embedded in the PWA, or placed in n8n workflow JSON.

## Gateway choice

Preferred candidate: LiteLLM Proxy, subject to deployment/security review. It provides a unified interface to multiple model providers, routing, usage tracking, and budget/rate controls:
- https://docs.litellm.ai/
- https://docs.litellm.ai/docs/proxy/users
- https://docs.anthropic.com/en/docs/claude-code/llm-gateway

Caution: LiteLLM's budget documentation states that spend budgets require a database and that a DB-less deployment can fail open for global budget enforcement. Therefore a numeric budget of $0 is NOT the sole safety control. Implement a separate fail-closed allowlist: with the current policy, no billable provider model is routable. Reject requests before provider dispatch unless a future explicit authorization changes the policy. Keep the gateway's provider allowlist empty by default.

## n8n role

n8n is the integration/orchestration layer, not the public model gateway. It should receive authenticated ANNE task events and invoke only approved workflows. Secure it with TLS, authentication, least-privilege credentials, restricted nodes, execution-data redaction, and disabled public API where not needed. See https://github.com/n8n-io/n8n-docs/blob/main/docs/deploy/host-n8n/configure-n8n/security.md.

Do not expose an unauthenticated webhook as the mobile command endpoint. Use short-lived signed requests or authenticated sessions, replay protection, rate limiting, and server-side authorization. Do not put provider keys in mobile JavaScript.

## Proposed API contract (mock-only until approved)

- `POST /api/agent/tasks`: authenticated user submits a task; create a queued task record.
- `GET /api/agent/tasks/:id`: return status and sanitized progress.
- `POST /api/agent/tasks/:id/approve`: explicit approval for a named, scoped action.
- `POST /api/agent/tasks/:id/cancel`: cancel queued/running work where supported.
- `POST /internal/model/complete`: internal-only model request; accepts task class, sanitized prompt, allowed model alias, token ceiling, and request ID.
- `POST /internal/workflows/dispatch`: internal-only n8n dispatch after policy approval.

Never accept a model name, tool list, callback URL, or arbitrary workflow identifier directly from an untrusted mobile client without server-side allowlist validation.

## Claude adapter design

- Provider alias: `claude_reasoning` (disabled by default).
- Protocol: Anthropic Messages API through LiteLLM or a narrowly scoped direct adapter.
- Secrets: server-side secret manager/environment only; never in client bundle, logs, repo, database plaintext, or task payload.
- Request controls: fixed model allowlist, bounded max output tokens, bounded input size, timeout, request ID, no automatic retry on billable failures, no background calls.
- Data minimization: no bank records, medical data, credentials, customer PII, or local filesystem contents by default.
- Tool policy: do not pass Hermes tool schemas to Claude. Claude may return a typed proposal; ANNE policy engine validates it; user approval is required for consequential operations.
- Logging: record provider alias, task ID, timestamp, model, token counts/cost when returned, policy decision, and sanitized error. Never log secrets or full sensitive prompts.

## Fail-closed policy (current)

- Max spend: **$0**.
- Billable providers: **blocked**.
- Claude API requests: **blocked** until separately authorized and a verified no-charge credit source exists.
- Poe API requests: **blocked** under the same rule; prior Poe bridge remains dry-run by default.
- Live checkout, charges, subscriptions, transfers, trades, ads, and credit purchases: **blocked**.
- Research, local drafts, mock responses, schema tests, and dry-run workflow simulations: allowed.
- If billing state, provider price, authentication, policy service, or budget state is unknown: reject the call.

## Implementation sequence

1. Inspect current ANNE web app, auth, task queue, Supabase schema/RLS, Hermes provider configuration, and existing deployment targets.
2. Add a mock model adapter and typed response schema; test routing and error handling without network calls.
3. Add policy service with provider allowlist empty and hard-deny paid routes.
4. Add Claude adapter behind a feature flag, but keep flag off and credentials absent.
5. Add n8n authenticated dispatch with test-only workflows and execution-data redaction.
6. Add mobile task queue, status, approval, cancel, and audit views.
7. Run static checks, unit tests, security checks, and mocked end-to-end tests.
8. Only after separate authorization and verified $0 funding, consider a single low-token live test. This is not authorized by this document.

## Deployment and cost reality

A cloud endpoint requires an actual hosting environment, domain/network access, secrets management, and ongoing operational controls. No free hosting entitlement has been verified. Do not deploy to a paid service, enable billing, add a card, or create usage-based infrastructure. Until a $0 host is verified, use this specification and local/mock tests only. The Mac being offline prevents local Hermes/n8n integration verification.

## Acceptance criteria

- Mobile client contains no provider secrets.
- Provider allowlist is empty by default.
- Paid routes are rejected before any outbound request.
- $0 budget policy is enforced independently of gateway spend accounting.
- Claude output cannot directly invoke shell, database writes, payments, trades, or arbitrary n8n workflows.
- Approval records are bound to exact action payloads and expire.
- Every task has an auditable state transition and sanitized event log.
- Mock end-to-end test passes with zero outbound provider requests.
- No production data, auth, secrets, or scheduled jobs are altered during staging work.
