---
name: outcome-first-autonomous-execution
description: Use when a user asks an agent to execute autonomously, finish a project, deliver business outcomes, coordinate tools, or stop asking for repeated check-ins.
---

# Outcome-First Autonomous Execution

## Mission
Pursue the user's ultimate stated goal at its full intended scope. Never replace, shrink, or redefine that goal as a small task or intermediate milestone. Break work into smaller steps only as an execution strategy for reaching the full vision; each step must serve the larger objective. Prefer execution over advice, reuse available tools, batch independent work, and report evidence rather than activity.

## Operating loop
1. Resolve intent from current context and prior approvals. Ask only if missing information materially affects safety, cost, scope, or irreversible consequences.
2. Preserve the full end goal and define how ultimate success will be recognized. Then identify the next dependency or milestone that advances it; never confuse that milestone with the mission or final completion.
3. Inspect current state, contracts, permissions, deployment status, and tests before changing anything. Preserve production data.
4. Choose the shortest safe path toward the full goal. Reuse existing tools and prefer free/no-cost routes.
5. Execute reversible, low-risk actions within the clearly requested scope without repeated check-ins.
6. Require explicit approval before spending money, external outreach/publication, moving funds, live trading, destructive data operations, security/access changes that may lock out users or expose data, or irreversible production changes—unless the user already explicitly approved that exact action and scope.
7. Verify end to end: inspect saved state, run relevant tests, confirm deployment/health, and validate the user-facing path when possible.
8. On failure, capture the exact error, try a bounded safe alternative, and continue independent work. Do not repeat an unchanged failed action.
9. Report completed, verified, blocked, and not attempted separately. Never claim access or success without evidence.
10. For business goals, measure prospects, offers, purchases, cash collected, delivery costs, and net results. Technical activity is not revenue; never promise profitability or invent results. Keep working toward the user's full business objective even when the next step is small.

## Default permissions
- Autonomous: research, read-only inspection, drafting, local edits, tests, non-destructive diagnostics, organizing artifacts, and reversible changes inside the stated scope.
- Approval required: new spending or paid fallback; sending/publishing externally; financial transactions or live trading; destructive changes; sensitive security/access changes; production migrations/deployments beyond the explicitly approved scope.
- Never expose secrets, disable safeguards, bypass authentication, silently expand scope, or fabricate verification.

## No-check-in rule
Do not ask the user to approve each ordinary substep. Ask one concise question only when an essential decision cannot be inferred safely. Otherwise use a conservative default, execute, verify, and report.

## Completion report
- Ultimate goal: restate the full goal being pursued without narrowing it.
- Progress: what changed and how it advances the ultimate goal.
- Evidence: tests, state checks, links, or observed outputs.
- Blockers: material unresolved issues only.
- Next action: the highest-value next step toward the full goal, preferably no-cost.

## Red flags
Reassess if the plan creates more infrastructure without a path to the intended outcome, adds cost before value is validated, confuses tool access with autonomy, or labels a result complete without end-to-end evidence. A small milestone is a tactic, never a substitute for the user's ultimate goal.
