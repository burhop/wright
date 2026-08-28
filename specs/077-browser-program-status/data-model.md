# Data Model: Browser Program Status

## ProgramStatusBundle

One immutable, size-bounded projection delivered atomically.

| Field | Type | Rules |
| --- | --- | --- |
| `schema_version` | string | Exact supported version, initially `1.0.0` |
| `bundle_id` | SHA-256 hex | Digest of canonical `source` plus canonical `projection` bytes |
| `generated_at` | UTC timestamp | Publisher observation time, never evidence time |
| `source` | SourceIdentity | Exact committed subject and validator result |
| `projection` | ProgramProjection | Complete view for one identity |

Validation canonicalizes `source` and `projection`, recomputes `bundle_id` over both (excluding only the non-semantic `generated_at` observation), verifies committed identities and passing EPP-F01 evidence, and rejects unknown fields, unsafe paths, excessive counts, or unsupported versions.

## SourceIdentity

Fields: exact 40-character `commit`, `tree`, and `program_tree`; safe relative `snapshot_path`; exact `snapshot_sha256`; `validation_transition`; and `validation_verdict=passed`.

## ProgramProjection

- `readiness`: exactly four `ReadinessArea` objects in product, benchmark, commercial, program-health order.
- `benchmark`: `BenchmarkProgress` with governed target 100.
- `customer_catalog`: `CatalogSummary`, independent of benchmark counts.
- `work`: active feature, bounded task summary, checkpoints, blockers, next action, and two delivery lanes.
- `history`: bounded `MetricSeries` collection.
- `findings` and `corrections`: bounded, inspectable summaries.
- `freshness`: bundle and evidence observations.
- `release`: exact non-compensating eligibility and approval facts.

## ReadinessArea

Fields: `id`, `label`, `status`, `required_gate_count`, `passed_gate_count`, `gates`, `blockers`, `freshness`, `last_qualified_at`.

Rules: ID is one of the four canonical areas; counts derive from the included gate set; status is copied from validated evidence; every non-passing classification is preserved.

## BenchmarkProgress

Fields: `qualified`, `target`, `phase`, `hold_reason`, `blocking_dependencies`, `authorization_state`, `next_action`, tier/outcome/deficit/completeness/contamination summaries, and `evidence_cutoff`.

Rules: target equals 100; `0 <= qualified <= target`; proposed stories cannot contribute to qualified; absent detail is unavailable, not zero or passing.

## CatalogSummary

Fields: `proposed_total`, `source_path`, `source_digest`, and `maturity_counts` keyed by governed catalog maturity.

Rules: values derive from the catalog at the exact source commit; counts sum to total; labels include `proposed`; no field maps to benchmark qualification.

## DeliveryLane

Common fields: `kind`, `branch`, `milestone`, `latest_capability`, `blocker`, `next_action`, `observed_at`.

Integration adds target branch, frozen/last-pushed identity and time, PR, phase, check counts, CI start/failure, dev-sync, merge-gate, and bounded events. Continued development adds exact base/candidate and planning/implementation authority state.

Rules: zero or one lane per kind; branch ownership is exclusive; absent GitHub data is null; links use allowlisted HTTPS GitHub origins.

## MetricSeries and CheckpointObservation

`MetricSeries`: ID, label, unit, decision use, current limitation, next action, optional feature ID, omission count, observations.

`CheckpointObservation`: commit, observed-at time, numeric value, label, evidence references, optional change reason.

Rules: series IDs are allowlisted; every point has an exact commit and trustworthy timestamp; missing points are omitted with a count; task series identify their feature; each series is bounded to 250 points.

## Findings and Corrections

Findings preserve ID, severity, state, assertion/evidence references, recovery, opened/resolved identities, and times. Corrections preserve profile, authority, expected/verified claim counts, original findings, and result. Disposed records remain visible and cannot mutate unrelated values.

## Runtime View State

Client-only states are `loading`, `current`, `stale`, `blocked`, `failed`, `unavailable`, and `unknown`.

```text
no bundle -> loading -> current
current + 304 -> current (same identity)
current + valid changed bundle -> current (atomic swap)
current + invalid/unavailable response -> stale or failed (retain prior bundle)
no bundle + invalid/unavailable response -> unavailable
```

Client state is never written back to evidence.
