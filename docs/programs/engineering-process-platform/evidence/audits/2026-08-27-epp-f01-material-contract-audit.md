# EPP-F01 Material-Contract Stop Audit

**Date:** 2026-08-27

**Mode:** bounded read-only audit plus primary-agent synthesis

**Candidate inspected:** `e98804be7fa046f18fd5cc00943e99ba80d1e402`

## Verdict

Implementation must stop before the v2 migration. Two material contract gaps were discovered after exact implementation approval. Neither may be resolved by an implicit validator exception.

## Finding 1: v1 compatibility bridge

The approved plan freezes `epp-bootstrap-v1-r1-r9`, but the governed Spec Kit planning, analysis, approval, and implementation-start sequence produced v1 state revisions 10–17 and transitions through `TR-0016`. A v2 validator cannot both reject every new v1 record after revision 9 and validate the authoritative current history.

Recommended amendment: preserve the exceptional r1–r9 bootstrap profile and add a second closed, digest-bound bridge profile for r10–r17. It must enumerate the exact revisions/transitions, accept no future v1 record, end at feature state `IMPLEMENTING`, and authorize only the single v1-to-v2 migration.

Rejected silent alternatives: accepting arbitrary later v1 records, rewriting history, pretending r10–r17 are v2, or extending the legacy profile without a material approval.

## Finding 2: dashboard identity and delivery loop

The approved CLI accepts source commit `S` but has no explicit or deterministic container `C` resolution rule. The planned report/dashboard contracts also diverge on per-gate freshness, define the validator with one blob digest even though it is a multi-module bundle, and risk requiring commit `C` to embed independent delivery evidence that can exist only later in descendant `D`.

Recommended amendment:

1. Add optional `--container <commit-ish>`; otherwise infer `HEAD` only when its first parent is `S` and its diff is dashboard-only.
2. Add per-gate `fresh` to the shared report/dashboard gate row.
3. Define validator identity as a canonical, sorted source-bundle manifest digest.
4. Keep dashboard bytes at `candidate_not_evidence`; prove committed-current delivery in the external delivery envelope at `D`, avoiding a self-referential regeneration loop.

## Preserved work

The feature owner had created only lease-scoped local drafts under `scripts/validate-engineering-process-program.py` and `scripts/program_control/`. They compile syntactically, were not executed against product or benchmark systems, add no dependency, and make no readiness claim. They are preserved as blocked work-in-progress and no task checkbox is marked complete.

## Required human action

Decide `DEC-P0-013` and `DEC-P0-014`. If the recommended amendments are accepted, the coordinator must update the affected spec/plan/research/data-model/contracts/tasks, rerun checklists and `speckit-analyze`, freeze a new exact subject, and obtain replacement `material_change` and `feature_implementation` approvals before implementation resumes.

## Planning disposition

The human accepted both recommended amendments for planning and re-analysis only in [`APR-EPP-F01-AMEND-PLANNING-001`](../approvals/APR-EPP-F01-AMEND-PLANNING-001.json). Because this stop itself created revision 18 and the amended approval freeze creates the final legacy checkpoint, the closed bridge is now precisely revisions 10–19 and transitions `TR-0009`–`TR-0018`; it ends at `IMPLEMENTATION_APPROVAL_PENDING`, accepts no later v1 record, and permits one v2 migration. ADRs [`0013`](../../decisions/0013-closed-v1-bridge.md) and [`0014`](../../decisions/0014-dashboard-provenance.md) record the decisions. This disposition does not resume implementation or make either earlier approval current.
