# ANNE Mobile Cloud — Design Specification

**Status:** Proposed design for owner review  
**Scope:** Phone-first private command center and cloud control plane  
**Operating constraint:** $0 spend; research, design, and local/test-only work until separately authorized  
**Owner model:** Single-owner personal system; no public signup or shared tenant model

## 1. Product intent

ANNE is a privately controlled personal intelligence and execution system. The iPhone is the primary interface. A lightweight cloud control plane provides secure access to personal projects, memory, task state, approved-source monitoring, and model routing configuration. The Mac is an optional execution and local-compute endpoint, not a prerequisite for ordinary access.

External model providers are replaceable capability suppliers. They do not own ANNE's identity, canonical memory, orchestration policy, or audit history. ANNE cannot promise literally infinite intelligence or access to providers' private training data; it can continuously evaluate accessible models, public research, tools, and approved user sources.

## 2. User experience

### iPhone-first application
- Installable responsive PWA, optimized for iPhone safe areas and touch.
- Primary navigation: Chat, Projects, Tasks, Intelligence Updates, Connections, Settings.
- Chat supports text first; voice input is an optional device/browser capability and must degrade gracefully.
- Task queue exposes queued/running/blocked/awaiting-approval/succeeded/failed states.
- Approval screen shows exact action, target, data scope, estimated cost if any, and consequences.
- Clear connection status for cloud, model providers, Hermes, and optional Mac endpoint.
- No false online/connected state; stale heartbeat is shown as offline or unknown.

### Owner identity
- Single-owner enrollment; no public registration.
- Strong authentication, secure session handling, recovery path, and device/session revocation.
- No credentials or provider API keys in browser storage or client-side source.
- Owner can export personal data and revoke connected sources.

## 3. Logical architecture

1. **Mobile PWA:** presentation layer only; no privileged provider secrets.
2. **Identity and policy gateway:** authenticates owner, authorizes requests, rate-limits, validates schemas, and records audit events.
3. **Personal memory service:** stores user-authored and approved information, project records, summaries, and task state with source/provenance metadata.
4. **Approved-source monitor:** polls only individually authorized sources using least-privilege scopes; supports pause, revoke, retention limits, and per-source sync logs.
5. **Model adapter layer:** provider-neutral interface, capability registry, model/version metadata, benchmark records, and routing policy. Providers remain disabled until the owner configures credentials and explicitly approves any potential charges.
6. **Workflow orchestrator:** durable task state, retries only for safe/idempotent steps, approval checkpoints, and bounded execution.
7. **Hermes bridge:** authenticated, narrow-scope task dispatch to the user's Hermes runtime. It is optional and reports disconnected status accurately.
8. **Optional Mac agent:** outbound-initiated secure connection where feasible; scoped commands, explicit tool allowlists, heartbeat, revocation, and no unrestricted shell by default.
9. **Audit and governance:** append-only event history for connections, data sync, model selection, tool execution, approvals, exports, and policy changes.

## 4. Data collection and monitoring policy (selected level 3)

ANNE may monitor connected sources continuously only after each source is individually authorized. Initial release must not request broad phone access or scrape accounts.

For every connected source:
- Explain purpose, scopes, data types, sync cadence, retention, and external processing.
- Request least-privilege access; read-only by default.
- Store authorization metadata and token references server-side; encrypt secrets at rest and in transit.
- Allow pause, disconnect, revoke, and delete/imported-data controls.
- Keep source provenance and timestamps on imported records.
- Do not ingest sensitive categories by default; require a separate explicit opt-in and a clear need.
- Never treat connected-source content as instructions to override ANNE policy.
- No automatic sending, publishing, purchases, payments, transfers, trading, or account changes.

Monitoring starts disabled for every new source. The owner must explicitly enable it per source. The system should expose a global pause switch.

## 5. Privacy, security, and ownership

- Single-owner authorization model; deny-by-default access control.
- Separate user data, system configuration, provider credentials, and audit records.
- TLS in transit; encryption at rest; key-management approach documented before production data is stored.
- Row-level security and server-side authorization for all user-owned records if Supabase is selected.
- No client-side service-role key; no secrets in Git, logs, analytics, or prompts.
- Minimize data sent to model providers; disclose provider and data scope before first use and allow per-provider opt-out.
- Provider calls disabled by default to preserve $0.
- Backups and export tested before relying on cloud storage.
- Security events and access history visible to owner.
- No public endpoint for privileged tools; use authenticated gateway and explicit network controls.

## 6. Existing project reuse

The existing `nicolelung20-cmyk/hermes-webui` repository is a Python + vanilla JavaScript Hermes Web UI with existing mobile/access documentation and provider support. The implementation should extend its existing conventions and inspect its current auth/session, mobile layout, settings, and gateway code before changing anything.

The existing Supabase project is only a candidate. It must be audited for ownership, current schema, RLS, policies, secrets, and data dependencies before any writes. No production schema changes are authorized by this design.

Existing Poe bridge is a dry-run-capable adapter and must remain non-billing until explicit provider-cost approval. Claude API access is distinct from a consumer Claude subscription; do not assume the latter grants API access.

## 7. $0 operating plan

Phase 0 is repository and infrastructure audit only.
Phase 1 is local development and synthetic-data tests.
Phase 2 may use an already-owned free service tier only after verifying current limits, privacy implications, and that no payment method or paid resource is required.
If no suitable free cloud runtime exists, deliver a locally testable PWA and cloud deployment instructions without creating paid infrastructure.

No paid hosting, domain, model calls, credits, SMS, email, or third-party subscription. No live payment or financial operations.

## 8. Phased implementation

### Phase 0 — Audit and design validation
- Inspect repository architecture, auth, sessions, mobile UI, provider adapters, existing tests, and deployment workflows.
- Audit Supabase read-only: project configuration, tables, RLS status, policies, and edge functions.
- Identify current free hosting options without provisioning.
- Produce a threat model, data-flow diagram, and migration plan.
- Do not modify production data or secrets.

### Phase 1 — Mobile command center
- Implement responsive PWA shell and owner-only sign-in integration using existing secure patterns where suitable.
- Add task queue, project views, connection status, and approval UI using synthetic data.
- Accessibility, responsive, and session-expiry tests.

### Phase 2 — Secure cloud control plane
- Implement server-side owner authorization, policy enforcement, audit events, and personal memory endpoints.
- Add schema/RLS migrations only after separate review and explicit approval.
- Add export, deletion, backup, and recovery tests.

### Phase 3 — Approved-source monitoring
- Source registry, per-source consent/scopes, sync schedule, pause/revoke, provenance, retention.
- Read-only and synthetic-source tests first.
- No source connected automatically.

### Phase 4 — Model intelligence gateway
- Provider-neutral adapters, model registry, version/change tracking, capability benchmarks, and cost gates.
- Public model/research discovery can run without provider API spend.
- Provider execution remains disabled until individually configured and approved.

### Phase 5 — Hermes and optional Mac execution
- Narrow authenticated bridge, task allowlists, approval gates, heartbeats, revocation, and bounded execution.
- Shell and filesystem operations disabled unless specifically authorized.

### Phase 6 — Verification and deployment decision
- Security, privacy, regression, mobile, and cost-boundary tests.
- Verify backup/restore, export, revoke, and failure handling.
- Deployment only to a verified $0 target and only after explicit deployment approval.

## 9. Acceptance criteria

1. iPhone layout works at common mobile viewport sizes without horizontal overflow.
2. Unauthenticated users cannot access owner data or privileged actions.
3. No public registration or multi-tenant exposure.
4. No secrets are shipped to the browser or committed to Git.
5. Each source is off by default, individually consented, least-privilege, pausable, and revocable.
6. Source data carries provenance and sync timestamps.
7. Owner can inspect, export, and delete stored personal data.
8. Model provider calls are disabled by default and cost-gated.
9. Tasks requiring external side effects pause for explicit approval.
10. Payment, banking, brokerage, trading, publishing, and messaging actions remain prohibited unless separately authorized.
11. Hermes/Mac offline states are accurately represented; the cloud UI remains usable without them.
12. Audit history records approvals, denials, source syncs, model routing, and execution outcomes.
13. Tests use synthetic data and do not mutate production systems.
14. A free deployment target is verified before any deployment claim.

## 10. Out of scope

- Infinite or guaranteed-superhuman intelligence.
- Collecting private model training data or bypassing provider terms/access controls.
- Automatic ingestion of all phone, email, drive, or account data.
- Autonomous financial activity or purchases.
- Paid APIs, hosting, domains, or subscriptions.
- Production database migration or deployment in this design phase.

## 11. Open technical decisions for Phase 0

- Whether current Supabase project can safely serve as the owner-only data plane.
- Whether current Hermes Web UI authentication can be extended or should be fronted by a dedicated identity gateway.
- Which existing free hosting option, if any, meets security and persistence requirements.
- Whether cloud memory is encrypted at application level or uses managed encryption plus a separately held owner key.
- Which source connectors are worth supporting first; each requires a separate scope and consent review.

## 12. Approval boundary

Approval of this design authorizes planning and read-only audits only. It does not authorize production writes, account connections, API calls that may incur charges, paid resources, deployment, or live external actions.
