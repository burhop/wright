# EPP-F01 Data Model

## Identity Rules

- All committed identities are lowercase SHA-1 Git object IDs or lowercase SHA-256 digests of exact committed blob bytes.
- `wright-json-c14n-v1-sha256` remains the canonical semantic digest for state objects: reject duplicate keys, recursively sort object names by Unicode code point, preserve array order, emit UTF-8 RFC 8259 JSON without BOM/insignificant whitespace/trailing newline, then SHA-256.
- Checkout bytes, line endings, worktree cleanliness, and platform are observations, never substitutes for committed identity.
- Repository-relative paths use `/`, reject absolute/drive/UNC paths, `.`/`..` escape, NUL, and unsafe symlink traversal.

## ValidationSubject

| Field | Type | Rule |
|---|---|---|
| `source_commit` | 40-hex Git commit | Authoritative input commit `S` |
| `source_tree` | 40-hex Git tree | Tree of `S` |
| `program_tree` | 40-hex Git tree | Program subtree at `S` |
| `container_commit` | null or 40-hex | Commit `C` containing generated dashboard; inferred, never embedded as self-identity |
| `release_candidate` | null or exact subject object | Independent candidate `R` shared by all release gates |
| `worktree_clean` | boolean | Observation only |
| `checkout_representation` | object | Platform, autocrlf mode, dirty paths/count; bounded and non-authoritative |
| `validator` | object | Version plus exact committed generator blob digest |
| `observed_at` | date-time | Declared nondeterministic observation field |
| `input_manifest_digest` | SHA-256 | Canonical digest of sorted complete authoritative input manifest |

## SourceArtifact

| Field | Type | Rule |
|---|---|---|
| `path` | normalized relative path | Unique in manifest; allowlisted by lifecycle policy |
| `role` | enum | `immutable_policy`, `operational_state`, `append_only_evidence`, `generated_projection`, `feature_contract` |
| `git_blob` | 40-hex | Blob at `S` |
| `sha256` | 64-hex | Exact blob-byte SHA-256 |
| `schema_id` | string/null | Expected schema identity |
| `schema_version` | string/null | Explicitly compatible version |

Generated outputs are excluded from the authoritative input manifest. Feature artifacts outside the program root must be explicitly declared in lifecycle policy.

## ProgramState v2 proposal

Existing program-state fields remain except as migrated below.

| New/changed field | Rule |
|---|---|
| `schema_version` | `2.0`; v1 accepted only under bootstrap compatibility profile |
| `state` | Program-state domain only |
| `feature_state` | null when no current feature, otherwise one child state from the lifecycle policy |
| `active_mutating_lease` | `FeatureLeaseV2` or null |
| `last_transition` | Points to the most recent lifecycle/checkpoint event |
| `policy_version` | Exact compatible lifecycle-policy version |

Cross-field invariant: current feature, feature state, active roadmap row, pointer, and lease are either consistently absent or identify the same feature.

## TransitionEvidence v2 proposal

| Field | Rule |
|---|---|
| `state_domain` | `program`, `feature`, `attempt`, or `repair` |
| `event_kind` | `lifecycle_transition`, `failed_attempt`, `repair_checkpoint`, `verification`, or `approval_checkpoint` |
| `from_state` / `to_state` | Legal in the selected domain; non-lifecycle events may preserve state only when policy expressly permits |
| revisions/digests | New revision equals prior plus one; prior and resulting canonical state digests match |
| Git source/container | Record source parent; containing commit is inferred; complete changed-path manifest excludes the transition record itself |
| inputs/outputs | Normalized paths, exact Git-blob SHA-256, compatible schema versions |
| checks | Stable check ID/result/evidence, bounded environment label |
| authority | Exact approval reference when boundary requires it |

### Bootstrap compatibility profile

`epp-bootstrap-v1-r1-r9` is a closed profile anchored to the approved program subject and the verified revision-9 checkpoint. It recognizes legacy program/feature state mapping, the documented TR-0006 repair checkpoint, legacy `head_after=head_before`, normalized historical path forms, and incomplete containing-commit manifests for TR-0001 through TR-0005. No new v1 transition may be accepted after the checkpoint.

## LifecyclePolicy

| Field | Rule |
|---|---|
| `schema_version` / `policy_id` | Closed compatible identifiers |
| `program_edges` | Unique directed program-state edges |
| `feature_edges` | Unique directed child-feature edges |
| `event_rules` | Permitted self-state attempt/repair/verification events and required evidence |
| `approval_boundaries` | State/event to required approval scope |
| `action_rules` | State and evidence predicate to allowed next action(s) |
| `wip_limits` | One mutating lease, one implementing/repairing feature, max three read-only auditors |
| `path_roles` | Artifact patterns, role, mutability, allowed state/actions |
| `compatibility_profiles` | Explicit historical profiles and terminal checkpoint |

Unknown lifecycle policy versions fail closed.

## FeatureLeaseV2

| Field | Rule |
|---|---|
| `feature_id`, `branch` | Agree with state, roadmap, pointer, and actual branch |
| `worktree_id` | Stable non-private identifier, not an absolute path |
| `dev_baseline_commit/tree` | Exact selected `dev` baseline |
| `worktree_start_commit/tree` | Actual commit/tree used to create the isolated worktree |
| `holder_role` | `feature_owner` |
| `lease_mode` | `planning` or `implementation`; implementation requires exact approval |
| `lease_revision` | Monotonic per feature |
| `acquired_at`, `expires_at` | Valid times; observation after expiry fails closed |
| `allowed_paths` | Normalized allowlist patterns |
| `allowed_actions` | Closed local action vocabulary |
| `recovery` | `status`, last audit event, rollback state, remaining repair allowance |

## GateCatalog

| Field | Rule |
|---|---|
| `catalog_id`, `schema_version` | Closed identifiers |
| `candidate_policy` | Defines exact subject shape shared by all gates |
| `areas` | Exactly product, benchmark, commercial, program health in fixed order |
| `gates` | Every approved `PROD-*`, `BENCH-*`, `COMM-*`, `PROG-*` exactly once |
| gate `area` / `required` | Determines denominator; never taken from dashboard |
| `evaluator` | Stable evaluator ID and required assertions |
| `freshness` | Maximum age and invalidation triggers |
| `evidence_policy` | Required evidence classes and independence constraints |

## GateEvidenceSet

| Field | Rule |
|---|---|
| `subject` | Exact release candidate `R` |
| `catalog_digest` | Exact committed gate-catalog blob digest |
| `data_cutoff` | Latest included evidence time |
| `assertions` | At most one current row per gate and candidate |

Each assertion contains gate ID, status, evidence classification, reason code, observed/expires times, stale triggers, verifier identity/independence, and exact evidence artifact identities. Non-passing classifications never map to `passed`.

## ReadinessArea

| Field | Rule |
|---|---|
| `status` | Derived with fixed precedence; never hand-set |
| `passed_gates` | Count of passed required rows |
| `required_gates` | Count of required catalog members |
| `gates` | Every required area gate exactly once, catalog order |
| `blockers`, `evidence`, `fresh` | Derived, deterministic, bounded |
| `last_success_at` | Latest time the same exact candidate had every area gate passed; null otherwise |

Four areas are evaluated independently. No area consumes another area's counts or status.

## DashboardSnapshot v2 proposal

| Field | Rule |
|---|---|
| `generation_status` | `contract_seed_not_evidence`, `candidate_not_evidence`, `committed_valid`, `stale`, or `failed` |
| `source` | `S` identity, input manifest/digest, generator blob/version |
| `container_relation` | Expected first-parent and generated-output allowlist; actual `C` is inferred |
| `release_candidate` | Exact candidate `R` or null |
| `areas` | Four independent `ReadinessArea` objects in contract order |
| `benchmark_summary` | Derived counts and deficits; no implied product/commercial/program result |
| `release_approval` | Exact current approval identity/status for `R` |
| `release_eligible` | True only if all four areas passed and approval current for `R` |
| `next_action` | Derived allowed action or explicit blocker; never authority itself |

## ValidationFinding

| Field | Rule |
|---|---|
| `code` | Stable uppercase identifier |
| `severity` | `fatal`, `error`, `warning`, `info` |
| `artifact` | Repository-relative allowlisted path or stable artifact ID |
| `invariant` | Stable invariant ID |
| `evidence` | Bounded IDs/digests only |
| `consequence` | Bounded approved phrase |
| `recovery` | Smallest safe next step; cannot grant authority |

Sort by severity rank, code, artifact, invariant. Unknown internal exceptions map to a bounded stable failure without raw exception text.

## ValidationReport

The report contains schema version, validation subject, overall verdict, ordered checks/findings, derived eligibility, four readiness areas, delivery result, and one next action or blocker. Observation time is explicitly nondeterministic; all other semantic fields are deterministic for one subject and validator version.

## State Transitions

```text
program state + feature state + event
             │
             ├─ policy edge/event allowed
             ├─ prior revision/digest exact
             ├─ required artifacts/checks/authority exact
             ├─ roadmap/WIP/lease/stop predicates pass
             ▼
       next program/feature state
```

Validation failures never authorize or synthesize a transition. A failed attempt is append-only evidence governed by its own event rule.

## Migration and Rollback

1. Freeze and test the v1 revision-9 integrity checkpoint.
2. Add v2 schemas/policy/catalog/evidence plus append-only material-change approval.
3. Emit one explicit v1-to-v2 migration transition; do not rewrite v1 files.
4. Generate v2 dashboard only after v2 sources validate.
5. On rollback/removal, retain all source evidence and v1 manual validation instructions; v2 dashboards become stale/unsupported and cannot be approval evidence.
