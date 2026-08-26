# Wright Engineering Process Platform Program

**Program ID:** `EPP-2026`

**Status:** EPP-F01 planning active on `077-control-plane-validator`; no implementation approval

**Current authority:** this directory is the approved control plane for Wright's next engineering-process platform under [`APR-EPP-2026-001`](evidence/approvals/APR-EPP-2026-001.json). That approval authorizes bounded child-feature selection and specification only. Product implementation, dependencies, external writes, benchmark generation, dev integration and release retain their own explicit gates.

## Empty-context orientation

The objective is to build an engineer-readable, inspectable, provider-neutral process platform through small, independently shippable Spec Kit features. The program must improve the Wright product, qualify a representative 100-process benchmark, establish commercial readiness, and remain operationally healthy. Those are four independent obligations; success in one never compensates for failure in another.

Start here, then read only the artifacts needed for the next action:

1. [`program-state.json`](program-state.json) — current state, blockers, open P0 questions, active lease, and next eligible action.
2. [`roadmap.json`](roadmap.json) — dependency-ordered work and feature eligibility.
3. [`program-plan.md`](program-plan.md) — objective, scope, phases, governance, and success definition.
4. [`gates.md`](gates.md) — independent product, benchmark, commercial, and program-health gates.
5. [`coordinator-state-machine.md`](coordinator-state-machine.md) — exact top-level-agent lifecycle and transition evidence.
6. [`agent-operating-contract.md`](agent-operating-contract.md) — roles, WIP, worktrees, autonomy, repair limits, and stop conditions.
7. [`benchmark-strategy.md`](benchmark-strategy.md), [`benchmark-coverage.json`](benchmark-coverage.json), and [`status-dashboard-contract.md`](status-dashboard-contract.md) — benchmark and live status rules.
8. [`decision-register.json`](decision-register.json) and [`risk-register.json`](risk-register.json) — unresolved material choices and active risks.
9. [`prototype-evidence.md`](prototype-evidence.md) and [`audits/2026-08-26-omission-audits.md`](audits/2026-08-26-omission-audits.md) — read-only prototype lessons and four independent plan audits.
10. [`approval.md`](approval.md) — the recorded approval subject, scope, and downstream limits.

Historical `docs/engineering-capability-program-*.md` files describe the completed/earlier capability program. They remain evidence, but they do not govern this successor program. The feature pointer in `.specify/feature.json` and the managed Spec Kit block in `AGENTS.md` are worktree-local coordination aids, never program authority.

## Catch-up protocol

A fresh coordinator must perform these steps before acting:

1. Confirm the worktree is a Git worktree and record `git status --short --branch`, `git rev-parse HEAD`, and `git rev-parse HEAD^{tree}`.
2. Read and schema-validate every JSON artifact listed in [`schemas/README.md`](schemas/README.md).
3. Verify `program-state.json.program_id`, roadmap IDs, decision IDs, risk IDs, and gate IDs cross-reference existing records; verify the roadmap is acyclic.
4. Resolve the current program state and recompute eligibility from dependency and evidence records. Never trust a prose status or checked task box alone.
5. Verify every referenced approval, transition, audit, and evidence artifact exists and matches its recorded digest. Unknown schema majors, digest mismatch, stale approval, impossible transition, missing evidence, or a dirty shared worktree are fail-closed conditions.
6. Check `active_mutating_lease`. Only its holder may mutate its isolated feature worktree. A missing or expired lease does not authorize takeover; audit the worktree first.
7. Read only the roadmap item selected as `next_eligible_action`, its dependencies, relevant open decisions/risks, and required gate evidence.
8. State the intended transition, required evidence, authority, repair allowance, and stop condition before executing it.

If any check fails, transition to or remain `BLOCKED`, record the reason, and request human direction. Do not reconstruct missing authority from conversation history.

## Current baseline and evidence boundary

- Clean development baseline inspected: local `dev` and `origin/dev` at `ad162cca048ad23d848673ec4f49f588dcc77aff` before planning began.
- Planning branch: `codex/engineering-process-platform-plan`, created from that baseline.
- Frozen prototype evidence: local and remote `076-engineering-workflow-prototype` at `e7bb75c1d97e70e55b943e0c94a31ff85cf9f82d`.
- Prototype relationship: read-only experimental evidence only. No merge, cherry-pick, wholesale promotion, ref rewrite, or prototype-derived production assumption is permitted.
- Uncommitted-evidence result: no prototype worktree is registered and local/remote prototype refs match. No important evidence is observably available only as uncommitted work. Git cannot prove absence of files in deleted or unregistered external directories; the referenced plans, contracts, tests, screenshots, and lessons are committed.

## Next action

`SPECIFY_EPP_F01` is the only eligible action. The isolated worktree and singleton planning lease are allocated on `077-control-plane-validator`; complete the bounded Spec Kit planning loop and stop at exact implementation approval. The lease does not authorize implementation, dependencies, push, PR, merge, benchmark generation, publication, or other external mutation.
