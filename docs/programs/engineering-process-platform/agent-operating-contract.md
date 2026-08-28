# Agent Operating Contract

## Roles

- **Human program approver:** approves the exact control plane, P0 decisions/exceptions, material changes, feature implementation subjects, dev integration, and release.
- **Top-level coordinator:** owns program state, eligibility, leases, transition evidence, audit synthesis, change control, and stop/escalation. It does not implement two features concurrently.
- **Feature owner/writer:** sole mutating owner of one isolated feature worktree and final feature artifacts/code during its lease.
- **Read-only researcher/auditor:** performs a bounded question or omission audit and may not mutate files, refs, worktrees, index, external systems, or final artifacts.
- **Independent verifier:** did not write the candidate being verified; works read-only or in a clean verification checkout and binds findings to the exact unchanged tree.
- **Release operator:** separately authorized human/operator who follows Wright's release runbook and exact-subject evidence order.

One person/agent may hold multiple roles at different times, but the implementing writer cannot be the independent verifier for the same candidate, and no role separation may be claimed without an identity record.

## WIP and lease limits

- Program-wide mutating Spec Kit lease: **1**.
- Features in `IMPLEMENTING` or `REPAIRING`: **1** total.
- Additional feature in local planning before implementation approval: **1** maximum, in a different read-only or isolated context and never allowed to change the singleton feature pointer used by the mutating lease.
- Concurrent read-only research/audit agents: **3** maximum, each bounded to one deliverable and explicit stop condition.
- Independent verification may overlap no author mutation. Candidate tree is frozen until verdict.

Increasing a limit is a material P0 program decision. The state file, not human memory, owns the lease.

Each lease records program/feature ID, branch, worktree identity, base commit/tree, holder role, revision, acquisition/expiry, allowed paths/actions, and recovery procedure. An expired/interrupted lease requires status/diff/process/secret audit before reuse.

## Worktree and branch rules

1. Every child feature begins in a clean isolated worktree from an exact current `dev`/`origin/dev` baseline recorded in transition evidence.
2. The coordinator never mutates a shared `dev` worktree and never uses the frozen `076-engineering-workflow-prototype` branch as a code source.
3. `speckit-git-feature` is executed **exactly once through the mandatory `before_specify` hook of `speckit-specify`**. Do not invoke it independently in the same feature loop. Capture `{BRANCH_NAME, FEATURE_NUM}` as branch-allocation evidence.
4. `.specify/feature.json` and the managed Spec Kit `AGENTS.md` pointer are worktree-local singletons. Verify both after every Spec Kit command. Only one mutating Spec Kit loop may own them.
5. Before integration, restore the managed `AGENTS.md` pointer to this program's catch-up entrypoint through the approved agent-context process, or record an approved alternate ownership protocol. Never infer program state from the singleton pointer on `dev`.
6. No direct push to `dev`; no prototype merge/cherry-pick; no force push/ref rewrite; no broad cleanup/reset.

## Autonomy boundary

After exact program and feature approval, the feature owner may autonomously perform only the local actions enumerated in its charter: inspect, edit allowlisted paths, run deterministic checks, create local artifacts, and create explicit local commits. It may not add a dependency, change durable/public contracts, contact paid/proprietary/credentialed systems, mutate external/production data, push/open/merge a PR, publish, or release unless the charter or a later approval explicitly grants that action.

Read-only research is allowed within the stated scope. External writes, material scope changes, security/privacy/telemetry changes, license acceptance, migrations with loss risk, hardware/physical actuation, and destructive actions always require new authority.

## Spec Kit child-feature contract

The coordinator drives exactly this governed sequence:

1. `speckit-specify`, including the single mandatory `speckit-git-feature` pre-hook.
2. `speckit-clarify` until no critical ambiguity remains; accepted answers are persisted.
3. `speckit-plan` to produce plan/research/data model/contracts/quickstart and constitution checks.
4. `speckit-checklist` for requirements-writing quality, including UX, failures, I/O, tests, compatibility, benchmark, security, and rollback coverage.
5. `speckit-tasks` with strict dependencies, file paths, independently testable stories, and verification tasks.
6. `speckit-analyze` read-only; persist a digest-bound report. Critical/high findings block; medium findings require disposition.
7. Human implementation approval bound to exact spec/plan/checklist/tasks/analysis/tree.
8. `speckit-implement` within the approved lease and task scope.
9. Author verification, candidate freeze, independent verification, bounded repair, Wright Git gates, PR/CI/dev integration, and dev deployment verification.

Optional Spec Kit commit hooks are not execution authority. Automatic bulk commits are forbidden. In particular, no workflow may run a hook that performs `git add .`. Stage only a reviewed allowlist after status, diff, secret/private-output, and generated-artifact inspection.

Task checkboxes are progress markers. An incomplete-checklist override is prohibited. Passing tasks or tests never creates a lifecycle transition without its evidence record.

## Bounded repair policy

- Stable failure cause ID: normalized failing gate/test, first actionable error, subject tree, and environment class.
- Local candidate repair limit: **2 repair cycles per stable cause** after the original failure. Each cycle records the failed evidence before editing, smallest causal change, and full required rerun.
- Same-cause PR push limit: after **2 failed pushes**, stop pushing, build a deterministic reproducer, collect all terminal CI results, and request consolidated human review as required by the dev-push runbook.
- Environment/transient retries: at most **1 evidence-backed retry** when an explicit transient criterion is met; the original failure remains recorded.
- Never broaden timeouts, skip checks, dilute requirements, alter fixtures/oracles, or rerun until green without a cause record.

When a limit is reached, enter `BLOCKED` or `STOPPED`. A new cause ID must be evidence-based, not a counter reset.

## Stop conditions

Stop immediately on:

- missing/stale approval, digest mismatch, unknown schema major, impossible transition, roadmap cycle, dependency/WIP/lease violation, or dirty shared worktree;
- unapproved scope/dependency/architecture/public-schema/security/privacy/licensing/external mutation;
- secret, proprietary payload, reusable authority, or unexpected generated/binary artifact in the diff;
- fixture/live confusion, fabricated causality, unsupported engineering/commercial/platform claim, or benchmark-case-specific runtime behavior;
- ambiguous/destructive target, physical actuation, paid/proprietary/credential requirement, or insufficient rollback;
- verifier tree change, author/verifier identity conflict, skipped mandatory evidence, or repair bound exhaustion;
- any red Wright gate, incomplete CI terminal set, or two failed pushes for the same cause.

Record the stop, preserve evidence, state the smallest decision/authority needed, and do not continue by assumption.

## Independent verification

The verifier receives the approved acceptance envelope, exact commit/tree/artifact digests, and commands—but not an instruction to make the result pass. It reruns critical deterministic checks, inspects original failures/skips, performs the required user journey/artifact/oracle/compatibility checks, and emits pass/fail/blocked findings. A later author change invalidates the verdict.

Independent verification is never replaced by the implementing agent, CI alone, checked boxes, screenshots alone, or a summary without raw/digest-bound evidence.

## Token and context efficiency

- Use the README catch-up order and machine state instead of rereading the repository.
- Load only the active roadmap item, its dependencies, affected gates, open P0s, and directly linked contracts.
- Prefer stable IDs, JSON summaries, digests, and focused command output over transcript copying.
- Give subagents one bounded read-only question and require paths/commits/finding IDs.
- Run focused checks first; run broader gates only at declared transitions.
- Do not ask agents to rediscover settled evidence; update the decision/risk/prototype disposition once.
- Summaries never replace the linked evidence required by a gate.

## Change control and handoff

At every pause, the feature owner records exact state, clean/dirty status, completed and failed evidence, remaining repair allowance, next permitted transition, blockers, and rollback pointer. Material changes return to the earliest affected Spec Kit state and invalidate all downstream approvals and verification.

No conversational handoff can expand authority. A fresh agent must be able to continue from committed state and evidence alone.
