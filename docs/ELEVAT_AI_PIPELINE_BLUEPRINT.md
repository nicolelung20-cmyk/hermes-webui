# Elevat AI Product Pipeline — Implementation Blueprint

Status: research/preparation only. No workflows deployed, credentials added, APIs called, customer data processed, or money spent.

## 1. Objective

Create a repeatable product pipeline that turns a verified business problem into a scoped offer, a quality-checked deliverable, and a measurable customer outcome. Automation must not confuse AI output, leads, unpaid pilots, test payments, or booked orders with collected revenue.

## 2. Initial beachhead

Start with one buyer segment: small service businesses with repetitive administrative workflows (intake, follow-up, document handling, scheduling coordination, and handoffs).

Start with one paid hypothesis: **Workflow Brief Kit**. Deliverables:
- Current-state workflow map.
- Friction and risk register.
- Prioritized improvement plan.
- One-page implementation brief.
- Acceptance checklist and handoff notes.

The previously drafted $47 price is a hypothesis only. Validate buyer urgency, willingness to pay, delivery effort, and support burden before treating it as a price or forecast. The free Revenue Leak Check is a discovery asset, not proof of demand.

Do not initially build healthcare decision tools, underwriting/credit decisioning, investment/trading systems, gambling products, or products requiring sensitive customer data.

## 3. Proposed n8n workflow topology

Use small, independently testable workflows. Keep n8n self-hosted only if an already-running host and free capacity are verified; otherwise keep the workflow export and fixtures local until hosting is available. Do not create a paid cloud account or provision infrastructure.

| Workflow | Trigger | Nodes / stages | Success condition |
|---|---|---|---|
| WF-01 Intake | Authenticated webhook or manual trigger | Validate schema → assign request ID → classify data → redact secrets → policy gate → append intake record | Valid, minimal, non-sensitive request recorded |
| WF-02 Demand validation | Manual research record | Normalize buyer/problem → evidence check → score urgency/frequency/cost → human review | Evidence is traceable; no fabricated interviews or market sizing |
| WF-03 Qualification | Approved intake | Buyer fit → workflow map → baseline/time/cost estimate → risk classification → qualification decision | Baseline and buyer confirmation recorded |
| WF-04 Offer assembly | Qualified opportunity | Select template → define deliverables/exclusions → effort estimate → price hypothesis → claims review → human approval | Versioned offer approved before being sent |
| WF-05 Product production | Approved offer | Generate draft assets → deterministic checks → independent quality review → IP/license review → privacy/security review → human acceptance | Deliverable passes checklist and has provenance |
| WF-06 Checkout simulation | Manual test trigger only | Create synthetic order → simulate checkout result → test cancellation/refund paths → write test ledger entries | Test-only lifecycle passes; no payment processor call |
| WF-07 Delivery & acceptance | Human-marked delivery | Package/version artifact → create handoff checklist → record acceptance or revision request | Customer handoff and acceptance evidence recorded |
| WF-08 Measurement | Scheduled/manual read-only run | Reconcile synthetic/test and real records separately → calculate gross/fees/refunds/tax reserve/net cash only from verified data → report | Every metric has source, period, and status |
| WF-09 Improvement | Feedback or measured outcome | Cluster feedback → propose change → regression checklist → human approval → version/change log | Change linked to evidence and approved |

No autonomous outreach, bulk messaging, scraping, ad placement, publishing, charging, refunds, transfers, or trades in this phase.

## 4. Data model (Supabase target; no schema changes in this preparation phase)

Use UUID primary keys, UTC timestamps, explicit status enums, and append-only audit events. Enforce row-level security before any production data is stored.

- `pipeline_requests`: id, created_at, source, buyer_segment, problem_statement, data_classification, status, owner, consent_basis, evidence_refs.
- `opportunities`: id, request_id, buyer_role, organization_label, urgency, frequency, current_cost_or_time, qualification_status, reviewer, reviewed_at.
- `offers`: id, opportunity_id, offer_code, version, price_hypothesis, currency, deliverables_json, exclusions_json, estimated_effort, terms_version, approval_status.
- `products`: id, offer_id, version, artifact_refs, acceptance_criteria, quality_status, ip_owner, license_manifest_ref, privacy_review_status, claims_review_status.
- `orders`: id, offer_id, mode (simulation/test/live), status, currency, gross_amount, fee_amount, refund_amount, tax_reserve_amount, net_amount, external_reference_nullable. Live mode remains disabled.
- `deliveries`: id, order_id, artifact_version, delivered_at, accepted_at, revision_count, handoff_ref.
- `feedback_events`: id, delivery_id, category, rating_nullable, text_redacted, evidence_ref, created_at.
- `audit_events`: id, actor, action, object_type, object_id, before_hash, after_hash, approval_ref, timestamp. Append-only; never store secrets or raw payment credentials.

Do not persist sensitive personal information by default. Keep contact data out of model prompts unless specifically necessary and approved. Use synthetic fixtures for tests.

## 5. Product lifecycle and status vocabulary

Use explicit states: `captured` → `evidence_pending` → `qualified` / `disqualified` → `offer_draft` → `offer_approved` → `production` → `quality_review` → `ready_for_delivery` → `delivered` → `accepted` / `revision_requested` → `measured` → `closed`.

Keep commercial states separate: `no_order`, `test_order`, `paid_order_unreconciled`, `cash_collected_reconciled`, `refunded`. A test order is never revenue. An accepted deliverable is not cash collection evidence.

## 6. Approval and security boundaries

- Default spending ceiling: $0. Disable paid model calls, paid hosting, paid connectors, API-credit purchases, ads, domains, and subscriptions.
- Model calls: local/mock only until the user explicitly approves a specific paid route and cost. Never silently fall back to a paid model.
- Human approval required before external messages, publishing, customer delivery, changing price/terms, handling personal data, or any financial action.
- No live payment, refund, banking, brokerage, or trading nodes. No credentials for those systems in n8n.
- Webhook entry points must use authentication, input validation, replay protection/idempotency, rate limiting, and minimal payloads before exposure.
- n8n credentials belong in its credential store, never workflow JSON, source control, prompts, or execution logs.
- Separate dev/test/prod credentials and databases. Do not connect this blueprint to production Supabase until schema, RLS, backups, and rollback are verified.
- Treat model output and inbound webhook content as untrusted data. Do not let generated text choose arbitrary URLs, SQL, shell commands, or tool permissions.

## 7. Initial metrics

Track counts and rates with denominators and time windows:
- Evidence-backed problems / problems captured.
- Qualified opportunities / opportunities reviewed.
- Offers approved / qualified opportunities.
- Paid orders / offers sent (only after verified live commerce is authorized).
- Delivery acceptance / deliveries.
- Median production hours per deliverable.
- Revisions per delivery and refund rate.
- Gross collected, fees, refunds, tax reserve, net collected cash.
- Support hours and contribution margin per offer.

Never infer conversion from clicks, generated leads, model confidence, or test checkout events. Do not forecast the $55,000/week aspiration without observed conversion, realized price, delivery capacity, refund/support costs, and reconciled cash history.

## 8. Acceptance tests before activation

1. Reject malformed payloads and unknown workflow states.
2. Redact API keys, passwords, payment details, and personal data from logs.
3. Duplicate webhook delivery creates one idempotent request, not duplicate orders.
4. Unapproved offers cannot proceed to production/delivery.
5. No live payment or outbound communication node exists in the initial workflow.
6. Test checkout events remain labeled simulation/test and never enter collected-cash totals.
7. Audit events are append-only and include actor, object, action, timestamp, and approval reference.
8. Missing evidence produces “unknown”, not fabricated metrics.
9. Model timeout/failure stops safely; no paid fallback.
10. RLS tests prove users cannot read or mutate another tenant's records.

## 9. Build sequence

**Phase A — specification (now):** approve beachhead, offer hypothesis, lifecycle, data contract, and safety gates. Use only this document and synthetic examples.

**Phase B — local prototype:** export/import n8n workflow JSON on an already available local instance; use mock nodes and synthetic fixtures; no secrets, external calls, or live connectors.

**Phase C — security validation:** inspect Supabase schema and RLS read-only; design migrations separately; test access policies before any writes.

**Phase D — demand validation:** conduct a small number of permission-based buyer conversations manually; record actual evidence; revise the offer.

**Phase E — controlled pilot:** only after explicit approval, define hosting, model/API, payment-test, privacy, and delivery costs. Keep live commerce off until a separate approval.

## 10. Open decisions (do not guess)

- Confirm the first buyer segment and buyer role.
- Confirm whether Workflow Brief Kit remains the first offer.
- Confirm the exact scope and delivery time after a sample is produced.
- Verify whether a free, already-running n8n host exists; otherwise no deployment.
- Verify current Supabase RLS/schema before any integration.
- Determine whether the user wants manual evidence collection or a consent-based intake form.

## Current status

This is an implementation-ready design brief, not a deployed pipeline. No n8n workflows were created or activated, no Supabase tables/policies were changed, no customer data was processed, no model APIs were called, and no money was spent.
