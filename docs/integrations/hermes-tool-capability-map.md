# Hermes Tool Capability Map (Proposal)

Status: proposal only. This document does not connect accounts, enable tools, deploy code, or grant permissions.

## Operating rule

Hermes should select a tool only when it directly advances the current task, the relevant account is connected, the tool contract is understood, and the action is within the approved scope. A tag or mention is not blanket authorization to read sensitive records, move assets, spend money, send messages, change production, or deploy.

## Tool lanes

| Tool lane | Appropriate use | Default boundary |
|---|---|---|
| Quicknode | Read-only blockchain RPC, endpoint health and usage checks | Never create, change, expose, or delete endpoints without explicit task-level approval; never initiate transactions by inference |
| Health | User-requested review of the user's own connected health records or wellness data | Do not access health data just because Health is mentioned; no diagnosis or treatment changes without explicit instruction |
| Study / Deep research | Research, evidence review, learning plans, source comparison | Label facts, inferences, and hypotheses; cite evidence; no fabricated access or findings |
| Image creation | Brand assets and product visuals | Check tool availability/credits first; don't claim an image exists if generation fails |
| RealOpen | Crypto-backed property readiness information and user-directed purchase preparation | Never infer intent to buy, initiate identity checks, submit wallets, or create proof-of-funds documents without explicit intent |
| Open Design | UI concepts, design systems, prototypes | Treat output as design/proposal until implementation and visual checks are verified |
| NightVision | Authorized application-security scans and finding triage | Require a defined target and authorization; preserve scope; don't scan third-party systems without permission |
| YCloud Developer Kit | Contract-aware messaging/contact integrations | No customer outreach, message sends, unsubscribe changes, or production mutations without explicit approval |
| Platform engineering | Repository contracts, CI, deploy safety, logs, rollback plans | Inspect before changing; test in isolation; don't claim deployment or passing checks without evidence |

## Safe execution loop

1. **Clarify the deliverable from context.** Prefer the active Hermes feature or repository task; don't interpret a list of tagged tools as permission to perform every possible action.
2. **Inspect before acting.** Read repository contracts, tool schemas, account connection state, and existing configuration only as needed.
3. **Plan a minimal change.** Prefer free/read-only discovery and reversible edits. Keep secrets server-side and never commit credentials.
4. **Gate side effects.** Require task-specific approval for purchases, paid usage, external messages, identity verification, wallet operations, production database changes, security scans against live targets, or deployment.
5. **Verify.** Run the repository-prescribed tests in an isolated checkout; report exact commands and outcomes. A missing CI status is not a pass.
6. **Report honestly.** Separate completed, verified, blocked, and proposed work. Never claim revenue without a verified sale.

## Current known blockers

- Image generation was attempted for an Elevat AI / Hermes hero visual but failed because the connected image service reported its credit quota was exceeded. No image was created.
- A Desktop Commander host was previously reported as not connected; local runtime tests cannot be claimed without a verified runner.
- The existing `grok-x-revenue-builder` change is in draft PR #4. Its tests have been authored but not executed, and the skill's live discovery path has not yet been verified.

## Acceptance criteria before any live integration

- [ ] Exact use case and data scope documented
- [ ] Correct connected account and least-privilege access confirmed
- [ ] Free/read-only path preferred where sufficient
- [ ] Approval boundary and rollback documented for side effects
- [ ] Secrets excluded from prompts, logs, and repository
- [ ] Automated and manual verification evidence recorded
- [ ] Deployment status stated only after observing deployment evidence
