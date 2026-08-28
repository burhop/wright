# Wright Engineering Process Platform Program

**Program ID:** `EPP-2026`

**Status:** EPP-F01 local closure is in progress under the user's 2026-08-28 authorization to complete the existing tasks, run delivery gates, push, and open the PR. T073–T075 are complete and T076 verification is next; no new task IDs or product scope are being added.

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
11. [`../../../specs/076-control-plane-validator/spec.md`](../../../specs/076-control-plane-validator/spec.md), [`plan.md`](../../../specs/076-control-plane-validator/plan.md), [`tasks.md`](../../../specs/076-control-plane-validator/tasks.md), completed [`requirements checklist`](../../../specs/076-control-plane-validator/checklists/requirements.md), [`program-control checklist`](../../../specs/076-control-plane-validator/checklists/program-control.md), and current [`analysis.md`](../../../specs/076-control-plane-validator/analysis.md) — the bounded 80-task EPP-F01 subject; only T077–T080 are active under lease revision 13.
12. [`decisions/0015-browser-status-surface.md`](decisions/0015-browser-status-surface.md), [`evidence/transitions/TR-0021.json`](evidence/transitions/TR-0021.json), [`TR-0022.json`](evidence/transitions/TR-0022.json), [`TR-0023.json`](evidence/transitions/TR-0023.json), and [`TR-0024.json`](evidence/transitions/TR-0024.json) — the material browser-page omission, bounded EPP-F01B split, preserved EPP-F01 WIP checkpoint, full approval-subject manifest, accepted v3 approval bundle, bounded lease recovery, and implementation start.
13. [`evidence/verification/EPP-F01-foundation.json`](evidence/verification/EPP-F01-foundation.json) — Phase 2's exact source, 29 artifact digests, 63-test result, lint/format result, current-subject verdict, original repair history, open performance gate, and rollback pointer.
14. [`evidence/verification/EPP-F01-US1.json`](evidence/verification/EPP-F01-US1.json) — immutable pre-T069 US1 evidence and its original seven committed-evidence findings; use TR-0031 through TR-0033 for their later bounded repair disposition.
15. [`evidence/corrections/COR-EPP-F01-US1-COMMITTED-IDENTITY-001.json`](evidence/corrections/COR-EPP-F01-US1-COMMITTED-IDENTITY-001.json), [`decisions/0016-closed-committed-identity-correction.md`](decisions/0016-closed-committed-identity-correction.md), [`audits/2026-08-27-epp-f01-committed-identity-repair-audits.md`](audits/2026-08-27-epp-f01-committed-identity-repair-audits.md), and [`evidence/transitions/TR-0033.json`](evidence/transitions/TR-0033.json) — the approved exact 37-claim contract and independently accepted T069 closure. DEC-P0-016 is decided.
16. [`evidence/corrections/COR-EPP-F01-US1-TR0027-INPUT-ORIGIN-001.json`](evidence/corrections/COR-EPP-F01-US1-TR0027-INPUT-ORIGIN-001.json), [`decisions/0017-closed-tr0027-input-origin-correction.md`](decisions/0017-closed-tr0027-input-origin-correction.md), [`evidence/transitions/TR-0034.json`](evidence/transitions/TR-0034.json), and the `APR-EPP-F01-*-005` approval bundle — the exact one-claim contract and V5 authority for local T024–T041 only.
17. [`evidence/verification/EPP-F01-US1-repair.json`](evidence/verification/EPP-F01-US1-repair.json) and [`evidence/verification/EPP-F01-US2.json`](evidence/verification/EPP-F01-US2.json) — the runnable T041 value checkpoint, exact commands/results, correction non-interference, dashboard digest, limitations, and rollback subject.
18. [`evidence/approvals/APR-EPP-F01-MC-006.json`](evidence/approvals/APR-EPP-F01-MC-006.json), [`evidence/approvals/APR-EPP-F01-IMPL-006.json`](evidence/approvals/APR-EPP-F01-IMPL-006.json), [`evidence/transitions/TR-0038.json`](evidence/transitions/TR-0038.json), and [`evidence/transitions/TR-0039.json`](evidence/transitions/TR-0039.json) — exact V6 authority, T041 acceptance, lease reactivation, and implementation start.
19. [`evidence/corrections/COR-EPP-F01-REPAIR-EVIDENCE-001.json`](evidence/corrections/COR-EPP-F01-REPAIR-EVIDENCE-001.json), [`decisions/0018-closed-repair-evidence-correction.md`](decisions/0018-closed-repair-evidence-correction.md), [`evidence/approvals/APR-EPP-F01-MC-007.json`](evidence/approvals/APR-EPP-F01-MC-007.json), and [`evidence/approvals/APR-EPP-F01-IMPL-007.json`](evidence/approvals/APR-EPP-F01-IMPL-007.json) — historical V7 authority for completed T070–T071 only.
20. [`evidence/verification/EPP-F01-V8-discovery.json`](evidence/verification/EPP-F01-V8-discovery.json), [`evidence/corrections/COR-EPP-F01-T072-CHECKPOINT-EVIDENCE-001.json`](evidence/corrections/COR-EPP-F01-T072-CHECKPOINT-EVIDENCE-001.json), and [`decisions/0019-closed-checkpoint-evidence-correction.md`](decisions/0019-closed-checkpoint-evidence-correction.md) — exact V8 discovery, closed profile, exclusions, and unresolved separate P0 question.
21. [`evidence/approvals/APR-EPP-F01-MC-008.json`](evidence/approvals/APR-EPP-F01-MC-008.json), [`evidence/approvals/APR-EPP-F01-IMPL-008.json`](evidence/approvals/APR-EPP-F01-IMPL-008.json), and [`evidence/transitions/TR-0052.json`](evidence/transitions/TR-0052.json) — exact V8 approval, decision acceptance, and bounded lease revision 12.
22. [`evidence/verification/EPP-F01-US3.json`](evidence/verification/EPP-F01-US3.json) — bounded failure, redaction, atomicity, immutability, and delivery-envelope verification through T049.
23. [`evidence/corrections/COR-EPP-F01-V9-PREFLIGHT-EVIDENCE-001.json`](evidence/corrections/COR-EPP-F01-V9-PREFLIGHT-EVIDENCE-001.json), [`schemas/preflight-evidence-correction.schema.json`](schemas/preflight-evidence-correction.schema.json), [`schemas/v8-discovery-evidence.schema.json`](schemas/v8-discovery-evidence.schema.json), [`decisions/0020-closed-v9-preflight-evidence-correction.md`](decisions/0020-closed-v9-preflight-evidence-correction.md), and [`audits/2026-08-28-epp-f01-v9-preflight-audits.md`](audits/2026-08-28-epp-f01-v9-preflight-audits.md) — exact V9 two-claim plan, proof boundary, exclusions, and independent review.
24. [`evidence/approvals/APR-EPP-F01-MC-009.json`](evidence/approvals/APR-EPP-F01-MC-009.json), [`evidence/approvals/APR-EPP-F01-IMPL-009.json`](evidence/approvals/APR-EPP-F01-IMPL-009.json), and [`evidence/transitions/TR-0054.json`](evidence/transitions/TR-0054.json) — exact V9 approval, DEC-P0-020 acceptance, and bounded lease revision 13.
25. [`evidence/verification/EPP-F01-V9.json`](evidence/verification/EPP-F01-V9.json) and [`evidence/transitions/TR-0055.json`](evidence/transitions/TR-0055.json) — exact terminal implementation subject, 21-test matrix, non-interference proof, known exclusions, independent verifier, and closed lease checkpoint.

Local recovery note: the preserved T073 test-only stash was applied after the user's closure authorization. The stash remains only as a local backup; the worktree and subsequent commits are authoritative.

Historical `docs/engineering-capability-program-*.md` files describe the completed/earlier capability program. They remain evidence, but they do not govern this successor program. The feature pointer in `.specify/feature.json` and the managed Spec Kit block in `AGENTS.md` are worktree-local coordination aids, never program authority.

## Catch-up protocol

A fresh coordinator must perform these steps before acting:

1. Confirm the worktree is a Git worktree and record `git status --short --branch`, `git rev-parse HEAD`, and `git rev-parse HEAD^{tree}`.
2. Read and schema-validate every JSON artifact listed in [`schemas/README.md`](schemas/README.md).
3. Verify `program-state.json.program_id`, roadmap IDs, decision IDs, risk IDs, and gate IDs cross-reference existing records; verify the roadmap is acyclic.
4. Resolve the current program state and recompute eligibility from dependency and evidence records. Never trust a prose status or checked task box alone.
5. Verify every referenced approval, transition, audit, correction, and evidence artifact exists and matches its recorded digest. Unknown schema majors, an unapproved/partial/extra correction target, digest mismatch, stale approval, impossible transition, missing evidence, or a dirty shared worktree are fail-closed conditions. Never edit historical evidence to repair a mismatch.
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

Continue EPP-F01 at T076, then complete T066–T068 without adding task IDs. The latest authorization permits local closure, required delivery checks, push, and opening the PR; it does not authorize merge/dev integration, EPP-F01B implementation, dependencies, benchmark execution, publication, or release.
