---
name: supergrok
description: Use SuperGrok/Grok as a research and reasoning lane for Elevat AI and Hermes: investigate current public information, analyze X conversations when access is available, challenge assumptions, and produce source-backed decisions. Do not assume subscription, API, X account, or tool access is connected.
version: 1.1.0
updated: 2026-10-10
---

# SuperGrok Research Skill

## Mission

Use SuperGrok/Grok as an optional, high-signal research and reasoning capability inside the Elevat AI/Hermes workflow. Keep the experience fast, low-noise, privacy-first, and evidence-led. The goal is a verified decision or useful deliverable—not more activity, tool sprawl, or a dependency on one vendor.

## Access and truthfulness

- Before using SuperGrok, verify that a working authorized interface is actually available in the current runtime.
- A user's SuperGrok subscription, browser session, X account, API key, or MCP server is not implied by the name of this skill.
- Never claim to have queried Grok, X, live posts, or private account data unless the relevant call succeeded and returned evidence.
- If direct access is unavailable, use already-available approved tools or free public sources. Clearly label this as an alternate research path, not a SuperGrok result.
- Never ask for passwords, session cookies, recovery codes, or private keys. Keep tokens in approved secret storage, never in prompts, source code, logs, or skill files.
- Do not bypass paywalls, access controls, rate limits, or platform rules.

## Best uses

1. **Current research:** identify recent developments, compare claims, and trace them to primary sources.
2. **X signal review:** summarize public conversations, recurring pain points, objections, and possible demand only when authorized access or accessible public evidence exists.
3. **Red-team reasoning:** generate counterarguments, alternative explanations, disconfirming evidence, and uncertainty checks.
4. **Opportunity discovery:** pass supported audience/problem signals to `grok-x-revenue-builder`; interest is not proof of willingness to pay.
5. **Build support:** turn validated requirements into concise implementation briefs, test cases, or acceptance criteria for Hermes.
6. **Synthesis:** combine multiple research lanes into one recommendation, with source provenance and next action.

## Supermind reasoning engine

Use the existing `mind-power` skill as the decision discipline beneath Grok research; Grok is an evidence source and reasoning partner, not an unquestioned authority.

1. **Clarify the target:** express the desired result as an observable outcome, with constraints and a review point.
2. **Explore bounded worlds:** generate at most three plausible paths, including a counterfactual or “what would change my mind?” case. Treat these as planning scenarios, not literal parallel universes or quantum computation.
3. **Score and prune:** compare evidence quality, expected impact, effort, cost, risk, reversibility, and time-to-feedback. Reject paths that require unapproved spend, data exposure, unsafe access, or unverified production changes.
4. **Choose a cheap test:** select the smallest reversible experiment that can distinguish the leading hypothesis from its strongest alternative.
5. **Execute within gates:** use the existing authorized tools; draft rather than publish or send when explicit action approval is missing.
6. **Verify and learn:** compare the observed result with the baseline, record uncertainty and provenance, and update the next decision. Stop when the question is answered or the available evidence is exhausted.

For revenue work, hand qualified evidence to `grok-x-revenue-builder`. Do not treat attention, engagement, or a plausible idea as revenue proof.

## Standard workflow

### 1. Define the decision

Write the question to answer, decision deadline if known, constraints, and what evidence would change the recommendation. Prefer one clear question over a broad, open-ended research sweep.

### 2. Check capability before relying on it

Confirm available tools and permissions. If SuperGrok is not connected, proceed with the shortest available fallback when safe and useful; do not block the whole workflow or imply connectivity.

### 3. Gather evidence

- Prefer primary sources, original posts, official documentation, datasets, and direct statements.
- Record links and publication/access dates when available.
- Separate **Observed**, **Inferred**, and **Hypothesis**.
- Verify material or disputed claims with an independent source when practical.
- Seek contrary evidence and note missing, stale, or conflicting information.
- Do not fabricate citations, quotes, metrics, market size, sentiment, or access.

### 4. Reason and prune

Generate a small set of plausible explanations or options. Compare evidence, impact, effort, cost, reversibility, and downside. Select one best next step; mention alternatives only if they could change the decision. Do not describe this process as literal quantum computation or guaranteed prediction.

### 5. Produce an actionable output

Return:
- **Answer / recommendation**
- **Evidence and links**
- **Confidence and unknowns**
- **Counterargument or failure mode**
- **Next action**
- **Verification method**

Keep it concise unless the user asks for a deep dive.

### 6. Verify execution

Distinguish advice, a prepared draft, an attempted action, and a confirmed result. Never report a deployment, post, message, purchase, database write, trade, or sale as completed without direct confirmation from the relevant tool or system.

## Privacy, cost, and approval gates

- Default to no new spend and existing approved tools.
- Do not silently fall back to a paid model, API, subscription, or metered service. Stop and request approval before incurring a new cost.
- Send only the minimum information needed to each model or service. Do not route vault contents, credentials, financial secrets, or sensitive personal data to Grok/X or another external service without explicit, informed authorization.
- Keep private vault data local or in the user's approved storage path by default. Summarize or redact sensitive content before external research when possible.
- Public posting, outreach, purchases, account changes, live financial actions, and irreversible production changes require explicit approval of the exact action. Research and private drafting may proceed within existing permissions.
- Trading integrations remain paper-only unless a separate, explicit authorization and independent verification process changes that policy.

## Hermes routing guidance

1. Treat SuperGrok as one optional research provider, not the system's root of trust or sole brain.
2. Route current/public research to it only when access is confirmed and it materially improves the answer.
3. Route code changes to the authorized development tools; route repository facts to the repository connector; route deployment checks to the deployment provider.
4. If a provider fails, retry at most once when safe, then use an available fallback or report the blocker.
5. Keep a short provenance note of which provider actually supplied the evidence.
6. Avoid duplicated searches, redundant agents, and unbounded loops. Every research run must have a question, a stopping rule, and a deliverable.

## Completion checklist

- [ ] Actual access checked; no assumed connectivity
- [ ] Claims trace to accessible evidence
- [ ] Observed facts separated from inference and hypotheses
- [ ] Counterevidence and uncertainty considered
- [ ] Sensitive data and cost gates respected
- [ ] One actionable next step selected
- [ ] Completion claims verified
