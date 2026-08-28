# Data Model: Browser Program Status

## ProgramStatusBundle

One immutable, size-bounded projection delivered atomically.

| Field | Type | Rule |
| --- | --- | --- |
| `schema_version` | string | Exact supported contract, initially `1.0.0` |
| `bundle_id` | SHA-256 | Canonical digest of `source + dashboard + supplement` |
| `generated_at` | UTC timestamp | Publisher observation only; excluded from identity |
| `source` | SourceIdentity | Exact committed and validator identities |
| `dashboard` | EPP-F01 dashboard | Embedded unchanged and valid against the EPP-F01 schema |
| `supplement` | BrowserSupplement | History, catalog, work, evidence index, publisher state only |

Validation recomputes `bundle_id`, verifies source and dashboard binding, and rejects unknown fields, unsafe paths, excessive counts, unsupported versions, or any attempt to restate/override dashboard truth in the supplement.

## SourceIdentity

Exact 40-character `commit`, `tree`, and `program_tree`; safe relative snapshot path; snapshot SHA-256; passing validation transition; and validation verdict. The snapshot digest must equal the canonical embedded `dashboard` bytes.

## Authoritative Dashboard

The `dashboard` field conforms to `specs/076-control-plane-validator/contracts/dashboard.schema.json` without translation. It therefore preserves independently:

- canonical status vocabulary (`not_started`, `in_progress`, `passed`, `blocked`, `failed`, `stale`);
- gate status, classification, reason code, evidence, and boolean freshness;
- all four readiness areas and exact gate numerators/denominators;
- every benchmark population, tier, deficit, attempt, and cutoff;
- candidate, approval, lifecycle/lease, delivery, and release fields; and
- correction profile identity/link/digest/class/authority, exact claim/finding counts, and verification subject/time.

The supplement cannot shadow these fields.

## BrowserSupplement

- `history`: bounded `MetricSeries` records.
- `customer_catalog`: exact proposed-story summary, never benchmark authority.
- `work`: current milestone, active feature, lease identity, feature-local tasks/checkpoints, blockers, structured next action, and exactly two ordered delivery lanes.
- `evidence_index`: internal browser detail records for every linked evidence identity.

## StructuredAction

Fields: stable `id`, `label`, `eligibility` (`eligible`, `blocked`, `requires_approval`, `unavailable`), `authority_state` (`authorized`, `not_authorized`, `not_required`, `stale`, `unavailable`), `requires_human_approval`, nullable blocker, and evidence references.

Rules: display text never grants authority; `requires_approval` implies `requires_human_approval=true` and cannot be rendered as executable; unavailable or stale authority stays non-executable.

## MetricSeries and CheckpointObservation

Every series has a fixed ID-to-semantics mapping:

| ID | Unit / numerator | Inclusion rule | Source class |
| --- | --- | --- | --- |
| `customer_capability` | accepted customer scenarios | Count distinct customer-facing scenarios with exact committed acceptance evidence | `product_acceptance` |
| `quality` | passing required checks / required checks | Snapshot of required candidate checks; skipped/partial do not pass | `test_evidence` |
| `process_automation` | demonstrated lifecycle capabilities | Count distinct contracted lifecycle capabilities with committed demonstrations | `automation_capability` |
| `governance` | passing program-health gates / required gates | Use the authoritative program-health gate population | `program_gate` |
| four readiness IDs | passing gates / required gates | Use the matching authoritative area population | `readiness_gate` |
| `benchmark_qualified` | qualified processes / 100 | Use governed qualification evidence only | `benchmark_qualification` |
| `feature_tasks` | completed tasks / tasks in named feature | Count exact task IDs for one feature; never whole program | `feature_task` |
| `integration_delivery` | completed integration gates / 8 | Count ordered frozen/push/PR/CI/sync/merge/deploy gates | `integration_gate` |

`MetricSeries` fields include fixed unit, counting-rule ID, source class, availability, decision use, limitation, structured next action, deterministic latest change, omission count/reason, and observations.

Each observation has exact commit, transition/parent identity, time, value and optional denominator, label, matching source class, required change explanation (nullable only for the first point), and evidence references. Append-only transition/commit-parent order is causal; timestamp is display metadata. Missing identities/times are omitted and counted, never inferred.

## CatalogSummary

Fields: `proposed_total`, source path/digest, and exactly these derived maturity counts: `fully_defined`, `ready_to_specify`, `shaped`, `candidate`, `discovery_shaped`, `discovery`, and `discovery_separate_t4_authority_required`.

Rules: counts sum to total; all labels remain proposed; no value contributes to benchmark qualification.

## Work and DeliveryLane

Work includes an optional exact lease (`id`, holder, branch/worktree, scope, expiry, state), one feature-local task population, causal checkpoints, blockers, and a structured action.

Lanes are exactly two records in order: `integration`, then `continued_development`. Common fields include exclusive branch, milestone, capability, blocker, structured action, time, and evidence. Integration adds target, frozen/pushed identity/time, PR, phase, non-empty check counts when known, CI failure, sync, merge gate, and bounded events. Continued development adds exact base and authority state.

## EvidenceDetail

Every evidence reference points to an indexed detail with stable ID, allowlisted repository-relative path, exact digest, bounded support-safe summary, freshness, recovery, and availability. The browser always links internally to this detail. Optional exact-commit GitHub URLs are allowlisted secondary links. In packaged/offline operation, absent raw content is labeled unavailable; identity and summary remain usable.

## PublisherStatus (separate operational projection)

Fields: state (`active`, `inactive`, `failed`, `unavailable`), mode (`committed_watch`, `package_install`, `manual`), observed committed identity, last attempt/success, nullable failure code, and recovery. It is read through `/api/program-status/publisher`, not included in `ProgramStatusBundle` or `bundle_id`; operational heartbeat changes therefore cannot create false committed-evidence identities. Publisher state is context, never readiness or authority.

## Runtime View State

Client-only states are `loading`, `current`, `stale`, `blocked`, `failed`, `unavailable`, and `unknown`.

```text
no bundle -> loading -> current
current + 304 -> current (same identity)
current + valid changed bundle -> current (atomic swap)
current + invalid/unavailable response -> stale or failed (retain prior bundle)
no bundle + invalid/unavailable response -> unavailable
```

Installed-invalid is an error and never silently falls back to packaged data. Packaged fallback is eligible only when installed data is absent. Client state is never written back to evidence.
