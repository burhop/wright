# T058 benchmark and independent-oracle preflight

**Date**: 2026-09-01

**Exact preflight subject**: commit `433cc4a3ff975db4694ac8326c6cdd61c19fbe89` / tree `a060f68c4d9fd85265976bd03d28e1158a41ae26`

**Task status**: **OPEN / BLOCKED AT GOVERNANCE BOUNDARY**. No benchmark case was generated, viewed, executed, scored, or qualified. The governed result remains exactly `0/100`.

## Repeatable preflight

`scripts/recovery/benchmark_preflight.py` now validates the current decision
register, roadmap dependencies, coverage denominator, benchmark schemas, case
manifest count, and illegal early-count conditions. It emits deterministic
evidence at `test-results/dataset-evaluation/benchmark-preflight.json` and exits
nonzero only for a state violation; an honestly blocked preflight is a valid
guardrail result, not a qualification pass.

```text
status: BLOCKED
score: 0/100
case manifests: 0
safe_to_generate_cases: false
safe_to_count_cases: false
schema findings: 0
state violations: 0
focused benchmark + adjacent recovery conformance: 26 passed
Ruff: passed
```

## Exact blockers

| Authority or dependency | Current fact | Why work stops here |
|---|---|---|
| `DEC-P0-007` | open | A human benchmark/domain approver has not named independent oracle authority or disagreement/quarantine policy. |
| `DEC-P0-009` | open | A human benchmark custodian and access-separated blind-holdout store do not exist. Committing holdout content would destroy blindness. |
| `DEC-P0-010` | open | The customer/process population, claims, exclusions, and per-family contribution limit are not approved. |
| `DEC-P0-011` | status says decided, but `decision_record` is null | There is no digest-bound threshold/profile/repeat/freshness artifact to enforce. |
| `DEC-P0-012` | open | License, provenance, redistribution, and commercial-use policy is not approved; no case may be counted. |
| `EPP-F03` | proposed | Durable run evidence is not yet a completed governed roadmap dependency. |
| `EPP-F05` | proposed | Governed UI/headless execution is not complete. |
| `EPP-F06` | proposed | Reviewed text/LLM authoring is not complete. |
| `EPP-B01` | proposed | The benchmark registry/oracle/holdout/qualification harness is not an approved implemented feature. |

The benchmark coverage policy and release-threshold proposal also remain
unapproved. These are material human/legal/domain choices outside the user's
product/visual-direction approval. Inventing reviewers, selecting a target
population, creating a fake holdout, or treating a self-authored oracle as
independent would fabricate evidence and violate the benchmark strategy.

## Safe checkpoint

- `benchmarks/README.md` makes the repository boundary explicit and contains no
  case, fixture, oracle, or holdout content.
- The preflight detects any nonzero counted status while decisions or
  dependencies remain blocked as `BENCHMARK_COUNT_WITH_BLOCKED_PRECONDITIONS`.
- It also detects denominator drift, counted rows without manifests, and schema
  failures before generation or execution.
- T058 remains unchecked. T059 can proceed with locally independent packaging
  and lifecycle hardening while this external-authority boundary is unresolved.

## Dashboard verification

The recovery dashboard was refreshed to this exact blocked boundary and
verified at `2026-09-01T05:15:03.908Z`. Desktop and mobile checks both found the
approved subject, tree, manifest, `56/60` recovery ledger, governed freeze,
approval, truthful `T058` blocked-at-`0/100` boundary, and customer-readiness
false. All eight gallery images loaded, both viewports had zero horizontal
overflow, the evidence routes returned HTTP 200, both traversal probes returned
HTTP 403, and browser diagnostics were empty. The machine-readable verifier
result is retained under `artifacts/dashboard-recovery-verification/`.
