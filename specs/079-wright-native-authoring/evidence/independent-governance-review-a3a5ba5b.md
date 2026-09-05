# Independent prospective scoped-delivery review

Commit: `a3a5ba5b516b5735b2ad0da595291964757fcb2f`, compared with `544c7e63145f5cb39e68ce537879bb1c83e00cfb`.
Reviewer: independently delegated `native_candidate_review`; authored none of this amendment.

Three P2 findings prevent approval of this version.

## GOV-NATIVE-01 — Limit the no-additional-approval action to its intended feature

`lifecycle-policy.json:518–522` adds `PREPARE_NATIVE_SCOPED_PR` without a feature predicate. `validation.py` matches action policy only by program state, feature state and action. The new native checkpoint checks run only for N01/checkpoint-bearing states. Consequently EPP-F02 at `INDEPENDENTLY_VERIFIED`, with its existing exact approval and no native scoped checkpoint, can select this action with `requires_human_approval=false` and `validate_roadmap_approval_and_lease` returns no findings. This is contrary to the amendment's explicit N01-only authority.

Require N01, its standing scope authority and a valid independently reviewed scoped checkpoint when deriving/validating this action. No broad change to other feature approval semantics is needed.

## GOV-NATIVE-02 — Preserve pending acceptance when leaving scoped delivery

The new `native_delivery` mandatory-checkpoint condition excludes `DEV_DEPLOYMENT_VERIFIED`. The existing lifecycle permits `DEV_INTEGRATED` to transition there. Removing `scoped_checkpoint` while selecting `DEV_DEPLOYMENT_VERIFIED`/`SELECT_NEXT_FEATURE_PLANNING` passes the state schema and returns no roadmap/lease findings, despite T028 and other acceptance obligations still being unfinished. No new code checks this terminal step against those obligations or the preceding scoped checkpoint.

The amendment says the scoped path stops at `DEV_INTEGRATED`, final acceptance requires the remaining human evidence, and removing the checkpoint cannot evade review. Enforce that prospectively. A narrow fail-closed block on the later state until an explicit supported acceptance transition is preferable to inventing broad new completion machinery during this patch.

## GOV-NATIVE-03 — Freeze task requirements as well as product paths

The freshness exemption treats all of `tasks.md` and `work-registry.json` as metadata. Replacing the reviewed task wording with `- [x] T001 Baseline acceptance is now waived` after the candidate commit still passes exact-candidate validation. Its checkbox remains checked, so the only new content check passes. Requirements can therefore change without invalidating the review, contrary to the documented product/test/contract/policy freshness rule.

The task partition also compares only the mutable current registry; dropping T028 from both the registry and pending IDs passes this scoped validator with 31 tasks. That minimal removal probe leaves dangling dashboard references, which the separate milestone publisher can detect; it is supporting evidence for the mutable authority issue, not a claim that that inconsistent registry passes the complete pipeline. The task-wording probe needs no invalid dashboard references and demonstrates the freshness defect directly.

Permit intentional checkbox/status/evidence additions, while comparing task definitions, task population, scope and required acceptance relationships against the frozen candidate. Changes to those requirements require a new candidate/review. The current contract fixes the population at T001–T032.

## Verification and limits

Retained adverse probes: `tests/program_control_plane/test_independent_native_delivery_review.py` in this isolated review checkout. They import the amendment's existing valid tiny Git fixture, then independently mutate the specific boundaries above. Four probes fail because the validator accepts the prohibited changes. The first fixture attempt could not create the absent scratch parent; after creating `.local-run`, all four reached their intended assertions. No implementation source or parent worktree was edited; no broad suites were repeated.

Reviewed all nine amendment files, surrounding current-state validation, state-history checks, action matching and the milestone projection's population/relationship guards. Existing candidate commit/tree/ancestry checks, digest-bound review task identity, no-future review, closed lease, ordinary lifecycle edges and historical schema preservation are present. The record deliberately represents an identified independent technical attestation rather than a cryptographic signature or human study; this review does not request stronger identity claims than that contract makes.

Whole-feature completion, human usability, actual dev deployment and the required push/merge/CI gates remain pending. This report does not approve bypassing them.
