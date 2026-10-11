# Portable instructions — actual input and review continuation

These are newly created isolated digital subjects under the 7 October goal.
Configured user model: `openai-codex/gpt-5.6-sol`; implementation agent choice
does not change that setting. Predetermined answers and decisions retain
`integration_test=true`, actor `integration_test:instruction-portability`.
They do not establish human engineering acceptance or external action authority.

| Saved workflow | Actual run | Observed outcome |
|---|---|---|
| `input-proof-first-question.workflow.wflow` | `1b838484159443a48ce32693d3cf75df` | First step waited, then resumed the same run after service recreation. |
| `input-proof-after-comparison.workflow.wflow` | `025d0c5f3d4449c7bc9acd9919e20a56` | Real model mass comparison preceded the declared wait; same-run continuation completed. |
| `frozen-first-question-portable.workflow.wflow` | `d2381e55fb9946b39bfca8df47275774` | Modern frozen model routing survived restart; answer continued the same run. |
| `declared-question-needed-portable.workflow.wflow` | `c996ca8b361d4e2b8ceab30a3ba05ce9` | Actual upstream typed unresolved-selection evidence caused one declared question. Restart and answer continued the same run. |
| `declared-question-already-resolved-portable.workflow.wflow` | `79aeae6e30eb4b7bbbb36aa57b759be0` | Actual upstream `selection=b` caused a recorded skip; no input checkpoint was created. |
| `declared-artifact-review-portable.workflow.wflow` | `3135921d92ae4fe3929054d4f2c72890` | Actual model document waited for exact artifact review; labelled test decision completed the same run. |
| `declared-local-approval-portable.workflow.wflow` | `f2dc03d38ff148af836efd46f478279f` | Actual model document waited for approval, then a separate explicit local review-only continuation completed the run. No external dispatch. |

## Checks and retained evidence

- Invalid input values and stale subject digests left pending checkpoints untouched.
  Duplicate answers during continuation and after completion retained the same receipt.
- Input-only scope was denied review authority. Stale review subjects were rejected;
  duplicate review requests retained exactly one durable decision event.
- Modern model requests created fresh private Hermes sessions and verified the exact
  frozen provider/model lock. Failed pre-dispatch attempts are retained separately.
- The mass-only comparison preserved 50 × 30 × 2 mm, 7850/2700 kg/m³, and returned
  3000 mm³, 23.55/8.10 g. No strength, fit or manufacturing qualification is claimed.
- Isolated defaults A→B→A portability proof preserved accepted source A and pending
  run identity; import under B retained exact source without executing it.
- The conditional waiting UI was observed before answering, in ordinary diagram and
  exact-run working workspace tabs, and after browser reload. Walkthrough:
  `artifacts/ui-walkthrough/instruction-portability/20261007-conditional-wait-02`.
  Four steps passed; report structure and screenshot visual inspection passed.

Receipts under `.local-run/process-interfaces-083/instruction-portability`:
`interaction-proofs/synthetic-responses-01.json`,
`conditional-proofs-01/synthetic-responses-01.json`,
`review-proofs-01/synthetic-decisions-01.json`, and
`interaction-live-readback-01.json`. The last receipt independently reads the
existing durable files, checks completion and condition/decision events, and
records file digests. It does not execute a process or grant authority.

## Limits

Earlier request records were affected by the mutable invocation-evidence defect:
response enrichment could alter the retained submission phase. History is preserved
and is not reconstructed. The correction deep-copies publication boundaries; fresh
post-correction actual model runs remain necessary for final provenance acceptance.
Final production build, broader live portfolio and two final exploratory passes
remain pending. These results are software verification, not user acceptance.
