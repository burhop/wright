# Top-Level Coordinator State Machine

## Transition rule

A transition is valid only if:

```text
allowed(from, to)
AND prior_state_revision_and_digest_match
AND roadmap_dependencies_pass
AND required_artifacts_exist_and_digest_match
AND required_checks_are_terminal_and_passing
AND required_approval_is_current_for_exact_subject
AND lease_and_WIP_rules_pass
AND no_blocking_P0_or_stop_condition_applies
```

Every transition emits a record conforming to [`schemas/transition-evidence.schema.json`](schemas/transition-evidence.schema.json) before the state snapshot advances. Evidence is append-only. A failed attempt is also evidence; it never disappears when a later attempt passes.

Schema-v1 history is closed: `epp-bootstrap-v1-r1-r9` and `epp-bridge-v1-r10-r19` are the only accepted profiles, and `TR-0019` / revision 20 is their sole v2 migration successor. No revision 20 or later v1 record is legal. V2 records identify `state_domain` (`program`, `feature`, `attempt`, or `repair`) and `event_kind`; feature progress no longer overloads the program lifecycle state, and failed-attempt or repair evidence cannot masquerade as a lifecycle advance.

The exact-subject approval bootstrap is administrative and atomic. After the two append-only approval records are committed, the coordinator may promote only the already approved v2 policy/schema contracts, archive revision 20, emit `TR-0019`, activate the bounded implementation lease, and stop at `IMPLEMENTATION_AUTHORIZED`. No Spec Kit task checkbox or feature-owner source mutation is permitted before that migration commit. `IMPLEMENTATION_AUTHORIZED` to `IMPLEMENTING` is a separate transition after prerequisites, lease, diff, process, and secret audits pass.

V2 transition Git evidence records source-parent identities and a complete changed-path manifest excluding the transition record itself. The containing commit is resolved from the transition blob's Git container, rather than embedded self-referentially. Dashboard delivery uses the independent `S` (source), `C` (dashboard-only container), and explicit `D` (delivery evidence) history defined by the dashboard contract; those subjects never replace state-transition authority.

`wright-json-c14n-v1-sha256` is the state-digest algorithm: parse JSON while rejecting duplicate keys; recursively sort object member names by Unicode code point; preserve array order; emit UTF-8 RFC 8259 JSON with no BOM, no insignificant whitespace and no trailing newline; then record the lowercase SHA-256 hex digest. A transition is invalid unless `new_revision = prior_revision + 1`, `prior_state_digest` matches the accepted prior snapshot, `new_state_digest` matches the resulting snapshot, and that resulting state snapshot is present in `outputs` with its raw-file SHA-256. The genesis revision is an archived `PLAN_DRAFT` snapshot with `last_transition: null`; all later revisions name their transition.

## Program states

| State | Meaning | Only normal successor |
|---|---|---|
| `PLAN_DRAFT` | Control plane is being written. | `PLAN_AUDITED` |
| `PLAN_AUDITED` | Four omission audits are synthesized and machine artifacts validate. | `AWAITING_PROGRAM_APPROVAL` |
| `AWAITING_PROGRAM_APPROVAL` | No child work is authorized. | `PROGRAM_APPROVED`, `PLAN_DRAFT`, or `STOPPED` |
| `PROGRAM_APPROVED` | Exact plan subject has current human approval. | `SELECTING_FEATURE` |
| `SELECTING_FEATURE` | Coordinator derives an eligible roadmap item. | child `ELIGIBLE` or `BLOCKED` |
| `PROGRAM_ACTIVE` | One governed child loop may proceed. | `SELECTING_FEATURE`, `PROGRAM_RELEASE_REVIEW`, `BLOCKED`, or `STOPPED` |
| `PROGRAM_RELEASE_REVIEW` | All four independent areas pass at one exact candidate. | `RELEASE_AUTHORIZED`, `PROGRAM_ACTIVE`, or `STOPPED` |
| `RELEASE_AUTHORIZED` | Human authorized the exact release subject. | release runbook states |
| `PROGRAM_COMPLETE` | Public release and final evidence are complete. | terminal |
| `BLOCKED` | Required evidence/decision/authority/environment is absent. | prior safe state after new evidence/approval, or `STOPPED` |
| `STOPPED` | Human or safety/repair policy ended work. | terminal unless explicit restart decision |

The current state is authoritative only in [`program-state.json`](program-state.json); prose must not duplicate it. Before plan approval the only valid progression is `PLAN_DRAFT` → `PLAN_AUDITED` → `AWAITING_PROGRAM_APPROVAL`, with one accepted snapshot and transition record per edge.

## Child feature states and exact actions

| State | Coordinator action | Evidence required for successor |
|---|---|---|
| `PROPOSED` | Read roadmap item only. | Complete dependencies and declared gates/decisions. |
| `ELIGIBLE` | Confirm one outcome, no active lease, authority, exact current `dev` baseline. | Eligibility derivation, clean baseline commit/tree, no blocker. |
| `WORKTREE_ALLOCATED` | Create isolated worktree; acquire lease. | Branch/worktree/base/lease record and clean status. |
| `SPECIFIED` | Invoke `speckit-specify`; allow its mandatory `speckit-git-feature` pre-hook exactly once. | Hook JSON, matching `.specify/feature.json`, spec/checklist digests and validation. |
| `CLARIFIED` | Invoke `speckit-clarify`; integrate accepted answers. | No critical ambiguity/marker, clarification session, updated spec/checklist digests. |
| `PLANNED` | Invoke `speckit-plan`. | Plan, research, data model, contracts, quickstart as applicable; constitution pre/post checks; no unresolved technical clarification; verified `AGENTS.md` feature pointer. |
| `CHECKLISTED` | Invoke domain-focused `speckit-checklist`. | All requirements-writing items complete without override; feature readiness envelope explicit. |
| `TASKED` | Invoke `speckit-tasks`. | Strict task format, acyclic dependencies, independent story tests, verification/compatibility/rollback/docs/benchmark tasks. |
| `ANALYZED` | Invoke read-only `speckit-analyze`; persist report. | Zero critical/high; medium dispositions; full requirement/task coverage; exact artifact digests. |
| `IMPLEMENTATION_APPROVAL_PENDING` | Freeze planning artifacts and request human approval. | Digest-bound approval naming scope and allowed external/local actions. |
| `IMPLEMENTATION_AUTHORIZED` | Revalidate exact subjects and lease. | Approval current, unchanged tree/artifacts, no new blocker. |
| `IMPLEMENTING` | Invoke `speckit-implement`; own all mutations in one worktree. | Tasks complete; allowlisted diff/commits; focused evidence; no scope escape. |
| `AUTHOR_VERIFIED` | Run exact feature verification, compatibility/rollback, artifact/oracle, docs, and benchmark-delta checks. | Terminal current evidence with no unexplained skip. |
| `CANDIDATE_FROZEN` | Freeze exact commit/tree/artifacts and hand to separate verifier. | Candidate manifest and no further author mutation. |
| `INDEPENDENTLY_VERIFIED` | Separate verifier reruns critical evidence and user journey on unchanged tree. | Independent identity/verdict, exact subjects, findings closed or none. |
| `REPAIRING` | Return to owner for one bounded cause-specific repair. | Attempt record and remaining allowance; then return to earliest affected state and re-freeze. |
| `PUSH_AUTHORIZATION_PENDING` | Read dev-push runbook; inspect exact diff and request external-write authority unless charter already grants it. | Approval and clean expected diff. |
| `PR_READY` | Run `scripts/check-dev-push.ps1`/`.sh` on exact HEAD, then push/open/update PR if authorized. | Gate record, pushed SHA, all prior CI terminal before next push. |
| `DEV_MERGE_READY` | Reconcile latest `origin/dev`, rerun full `scripts/check-dev-merge.ps1`/`.sh`, collect required CI/review. | Current full gate, approvals, no red/skipped mandatory check, merge authorization. |
| `DEV_INTEGRATED` | Merge through PR; never direct-push `dev`. | Exact merged `dev` commit/tree and PR identity. |
| `DEV_DEPLOYMENT_VERIFIED` | Build/deploy exact merged dev image, health-check, changed-journey browser smoke, record digest/rollback. Restore program context pointer and regenerate state/dashboard. | Deployment evidence and roadmap/gate updates. This is feature completion. |
| `SUPERSEDED` | Record replacement item/decision. | terminal |
| `ROLLED_BACK` | Restore recorded prior exact subject and verify health/state. | terminal or new proposed repair feature |
| `BLOCKED` / `STOPPED` | Preserve evidence and request exact missing authority/decision. | explicit recovery/restart transition only |

For EPP-F01, planning-only repair evidence uses `BLOCKED` → `BLOCKED` with `state_domain=repair`, `event_kind=repair_checkpoint`, no lease, and a closed planning/re-analysis approval bound to the exact discovery checkpoint. It may amend and audit the future approval subject but cannot classify the committed-identity cause resolved or mutate implementation files.

After exact V4 approval, the feature recovery edge is `BLOCKED` → `IMPLEMENTATION_AUTHORIZED`. It is legal only when separate same-subject material-change and feature-implementation records accept DEC-P0-016, bind the frozen 69-task subject and exact correction-profile digest, all manifest digests match, and the bounded lease is reactivated atomically. The sole action is `START_EPP_F01_IMPLEMENTATION`. The coordinator then passes the existing preflight edge `IMPLEMENTATION_AUTHORIZED` → `IMPLEMENTING` and, before any correction mutation, records `IMPLEMENTING` → `REPAIRING` for stable cause `EPP-F01-US1-COMMITTED-IDENTITY-001`. Recovery never jumps directly from `BLOCKED` to `IMPLEMENTING`, never consumes a repair attempt during planning, and never expands the approved task/path envelope.

## Analyze remediation routing

- requirement/user-value/scope gap → `SPECIFIED` then rerun all downstream stages;
- ambiguity/edge/security/privacy question → `CLARIFIED` then rerun downstream;
- architecture/data/contract/compatibility gap → `PLANNED` then rerun downstream;
- missing/misordered/unmapped work → `TASKED`, rerun analysis;
- constitution conflict or material program change → `BLOCKED` pending human decision.

All prior implementation approvals are invalidated.

## Repair routing

Failures are classified `product`, `test_contract`, `test_isolation`, `platform_profile`, `packaging`, `infrastructure`, `benchmark_oracle`, `security_policy`, or `unknown`. The coordinator assigns a stable cause ID and returns to the earliest state that can correct it. Two local repair cycles per cause are allowed; a third requires human change approval. After two failed pushes for the same cause, no further push is allowed without deterministic reproduction and consolidated review.

## Release states

Feature completion never jumps directly to release. When the roadmap's release milestone is reached:

1. recompute four readiness areas for one exact candidate;
2. if all pass, enter `PROGRAM_RELEASE_REVIEW` and request exact human authorization;
3. run `scripts/check-prod-merge.sh` before `dev` to `main`;
4. follow [`docs/release/release-runbook.md`](../../release/release-runbook.md) exactly: build once, verify/promote identical subjects, public verification with bounded retry, versioned docs, GitHub Release last;
5. compare `dev`/`main` Git tree hashes for content synchronization after merge;
6. enter `PROGRAM_COMPLETE` only after public evidence and rollback subjects validate.
