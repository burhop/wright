# EPP-F01 Data Model

## Identity Rules

- All committed identities are lowercase SHA-1 Git object IDs or lowercase SHA-256 digests of exact committed blob bytes.
- `wright-json-c14n-v1-sha256` remains the canonical semantic digest for state objects: reject duplicate keys, recursively sort object names by Unicode code point, preserve array order, emit UTF-8 RFC 8259 JSON without BOM/insignificant whitespace/trailing newline, then SHA-256.
- Checkout bytes, line endings, worktree cleanliness, and platform are observations, never substitutes for committed identity.
- Repository-relative paths use `/`, reject absolute/drive/UNC paths, `.`/`..` escape, NUL, and unsafe symlink traversal.

## ValidationSubject

| Field | Type | Rule |
|---|---|---|
| `resolution_status` | enum | `resolved` or `unresolved`; a passing report requires resolved exact Git identities |
| `source_commit` | 40-hex Git commit/null | Authoritative input commit `S`; null only when resolution failed |
| `source_tree` | 40-hex Git tree/null | Tree of `S`; null only when resolution failed |
| `program_tree` | 40-hex Git tree/null | Program subtree at `S`; null only when resolution failed |
| `container_resolution` | enum | `absent`, `explicit`, `inferred_head`, or `unresolved`; inference is allowed only for `HEAD` whose first parent is `S` and whose diff is dashboard-only |
| `container_commit` | null or 40-hex | Commit `C` containing generated dashboard; resolved from explicit CLI input or the constrained `HEAD` rule, never embedded in dashboard bytes |
| `delivery_resolution` | enum | `absent`, `explicit`, or `unresolved`; only `--delivery` may resolve `D`, and it requires resolved `C` |
| `delivery_commit` | null or 40-hex | Explicit descendant `D`; first parent must be `C` and `C..D` must contain only the fixed delivery-evidence path |
| `release_candidate` | null or exact subject object | Independent candidate `R` shared by all release gates |
| `worktree_clean` | boolean | Observation only |
| `checkout_representation` | object | Platform, autocrlf mode, dirty paths/count; bounded and non-authoritative |
| `validator` | object | Version and canonical digest/entries for the tracked regular entrypoint plus all tracked regular `*.py` blobs recursively under `scripts/program_control/` at `S`; normalized paths are unique/sorted, capped at 100 files/2 MiB total, local imports outside the bundle fail closed, and any add/delete/change changes identity |
| `observed_at` | date-time | Declared nondeterministic observation field |
| `input_manifest_digest` | SHA-256/null | Canonical digest of sorted complete authoritative input manifest; null only when subject resolution failed and verdict cannot pass |

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

`epp-bridge-v1-r10-r19` is a second, independent closed profile. The r1–r9 profile names it as the single closed-profile successor beginning at `TR-0009`; the bridge then enumerates revisions 10–19 and transitions `TR-0009`–`TR-0018` with unique normalized paths, exact prior/new canonical state digests, exact raw SHA-256 for every state and transitions through `TR-0017`, and one terminal `checkpoint_commit_blob` identity for `TR-0018`. The terminal hash remains null to avoid a mutual hash with the profile; the validator resolves and hashes that blob from the later exact approval subject containing both artifacts. The bridge ends at feature state `IMPLEMENTATION_APPROVAL_PENDING`, accepts no later v1 record, and permits one v1-to-v2 migration successor. Its immutable fixture leaves `checkpoint_commit` null under rule `exact_material_change_approval_subject`; the validator resolves the effective commit from the approval record and verifies every profile path/blob at that subject without modifying the fixture. Exactly the two named profiles, contiguous enumerations, terminal states, and sole successor link are accepted.

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
| `compatibility_profiles` | Explicit closed historical profiles with enumerated state and transition digests, terminal program/feature state, approval-bound checkpoint, no-new-record rule, and at most one declared successor |

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
| `assertions` | Exactly one current row per catalog gate and candidate; each row contains exactly one result per catalog assertion ID |

Each gate row contains the evaluator identity plus a complete set of assertion results. The catalog's closed class registry maps each `evidence_class` to an expected source schema ID and role. Each result contains assertion ID, status, evidence classification, reason code, explicit freshness, observed/expires times, stale triggers, verifier identity/independence, and exact non-empty evidence identities with class/schema/role. The validator requires those fields to match both the registry and resolved SourceArtifact manifest entry, and requires their union to cover every catalog `required_class`; relabeling an arbitrary artifact cannot satisfy a class. The aggregate gate status is derived: `passed` requires every required assertion to be `passed`, `supporting`, fresh, exact-candidate-bound, evaluator-matched, evidence-backed, required-class-complete, and independent when the catalog requires it. Missing/extra/duplicate assertion IDs, missing/unknown/mismatched class/schema/role, hand-set aggregate status, and non-passing classifications fail closed.

## Benchmark summary algebra

- The target population is exactly 100 governed slots. `counted` is the number of distinct, current, non-superseded case manifests admitted by sampling/qualification policy; one equivalence family contributes only its approved maximum.
- Every target slot is assigned exactly once, in fixed precedence, to `eventual_passed`, `failed`, `blocked`, `stale`, `contaminated`, or `not_tested`; absent target slots and counted cases without terminal evidence are `not_tested`. These six values sum to `target`.
- `first_attempt_passed` is a subset of `eventual_passed`; both are calculated from append-only attempt history for the same exact candidate and frozen policy. A later pass never erases the first failure.
- `t0`–`t3` count current, fresh, passing tier qualifications among counted cases. Every T1/T2/T3 case also passes T0, and every T2/T3 claim also passes T1; T2 and T3 may overlap without either containing the other. No tier count exceeds `counted`.
- Coverage, oracle, artifact, partition, and freshness deficit arrays are independently derived from governed source records and remain non-empty until their exact obligations pass. Counter consistency never substitutes for those deficits.

## ReadinessArea

| Field | Rule |
|---|---|
| `status` | Derived with fixed precedence; never hand-set |
| `passed_gates` | Count of passed required rows |
| `required_gates` | Count of required catalog members |
| `gates` | Every required area gate exactly once, catalog order |
| gate row | Shared report/dashboard object with `id`, `status`, `classification`, `reason_code`, exact `evidence`, and required boolean `fresh` |
| `blockers`, `evidence`, `fresh` | Derived, deterministic, bounded area aggregates; area freshness never substitutes for a gate's own `fresh` field |
| `last_success_at` | Latest time the same exact candidate had every area gate passed; null otherwise |

Four areas are evaluated independently. No area consumes another area's counts or status.

## DashboardSnapshot v2 proposal

| Field | Rule |
|---|---|
| `generation_status` | Only `contract_seed_not_evidence` or `candidate_not_evidence`; dashboard bytes never claim their own committed validity |
| `source` | `S` identity, input manifest/digest, generator version, source-bundle manifest/digest |
| `container_relation` | Expected first-parent and generated-output allowlist only; neither actual `C` nor descendant `D` evidence is embedded |
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
| `json_pointer` | Exact affected pointer when the invariant is field-specific; null otherwise |
| `invariant` | Stable invariant ID |
| `evidence` | Bounded IDs/digests only |
| `consequence` | Bounded approved phrase |
| `recovery` | Smallest safe next step; cannot grant authority |
| `resolution_status` | `unresolved`, `resolved`, or `not_applicable`; derived, never hand-set authority |
| `correction_ref` | Exact approved correction path/ID when resolved; null otherwise |

Sort by severity rank, code, artifact, invariant. Unknown internal exceptions map to a bounded stable failure without raw exception text.

## CommittedIdentityCorrection

This is not an open-ended entity family. Version 1 recognizes exactly one profile ID: `COR-EPP-F01-US1-COMMITTED-IDENTITY-001`.

| Field | Rule |
|---|---|
| `correction_id`, `stable_cause_id` | Exact closed identifiers |
| `source_checkpoint` | Exact revision-27 discovery commit/tree/program tree |
| `accept_new_records` | Always `false` |
| `expected_claim_count` | Exactly `37` |
| `transition_digest_claims` | Exactly six ordered claims, each binding target transition path/raw digest/introducing commit/tree/blob, JSON pointer, recorded digest, authoritative artifact blob and recomputed SHA-256 |
| `historical_state_tree_claims` | Exactly 26 ordered rows for revisions 1–26 and 31 exact pointers; each binds path/raw digest/introducing commit/tree/blob plus canonical state digest |
| `tree_resolution` | Wrong recorded commit ID, authoritative commit, and tree obtained from that commit object |
| `forbidden_target_classes` | Closed list covering state/lifecycle identity, manifests, authority, readiness, gates, benchmark/release evidence, candidate/freshness, and correction records |
| `resolution_semantics` | Original bytes/findings retained, recomputation mandatory, all claims required, old readers fail closed, correction cannot be corrected, readiness non-interference |
| `authority` | Exact proposed V4 material-change and implementation approvals plus frozen planning transition |

The profile becomes effective only when both exact V4 approvals bind its frozen digest. All target containers must be strict ancestors of the correction-containing commit. A partial match is failure, never partial resolution. Resolution changes finding disposition only; source values remain the immutable bytes actually present in Git.

## TransitionInputOriginCorrection

This is a separate closed entity, not an extension of `CommittedIdentityCorrection`. Version 1 recognizes exactly `COR-EPP-F01-US1-TR0027-INPUT-ORIGIN-001` and one claim.

| Field | Rule |
|---|---|
| `correction_id`, `stable_cause_id` | Exact closed identifiers; no aliases |
| `expected_claim_count` | Exactly `1` |
| `claim` | Exact TR-0027 path/raw SHA/blob, `/inputs/3`, declared source, unique container/tree, and exact approval path/raw SHA/blob |
| `verification` | Approval absent at source; exact blob present and first introduced at container; both paths in unchanged manifest |
| `forbidden_target_classes` | Any other transition/pointer plus manifests, outputs, authority content, state/lifecycle, readiness, benchmark/release, candidate/freshness, and corrections |
| `resolution_semantics` | Original bytes/finding retained; historical input-origin disposition only; old readers fail closed; zero readiness/authority effect |
| `authority` | Separate same-subject V5 material-change and implementation approvals plus TR-0034 |

The record cannot legitimize arbitrary container-added inputs. If any exact identity differs, the approval exists at the source, the container is not the unique introducing commit, either manifest path is absent, or the profile changes another result, validation fails closed.

## ValidationReport

The report contains schema version, validation subject, overall verdict, ordered checks/findings, derived eligibility, four readiness areas with complete gate rows and last-success data, benchmark summary, exact release-approval result, release eligibility, delivery result, and one next action or blocker. Observation time is explicitly nondeterministic; all other semantic fields are deterministic for one subject and validator version.

## VerificationEvidence

Every durable author, story, rollback, diff-audit, candidate, independent-candidate, and dashboard-delivery record contains a versioned evidence ID/kind, exact subject commit/tree/artifact manifest, actor identity/role/independence, bounded check records, original failure/skip references, findings, verdict, created time, and rollback pointer. It records command IDs or bounded methods, never secrets or unredacted command arguments. Candidate-freeze and independent-verifier evidence must use distinct actor identities. Delivery-only evidence in explicit descendant `D` has a required relation binding source `S`, container `C`, exact dashboard bytes, the dashboard-only `S..C` diff, and the delivery-only `C..D` diff; its actor is an independent verifier and its verdict is passed. `D` is never inferred or an input to the snapshot generated from `S`.

## DeliveryEnvelope

The validation report, not the dashboard, contains delivery status. It records the container-resolution method, exact `C` when resolved, explicit delivery-resolution method, exact `D`, and artifact identity of independent passing delivery evidence in `D`, prior-snapshot preservation, and status `not_requested`, `candidate_not_evidence`, `committed_valid`, `stale`, or `failed`. `committed_valid` requires all external `S`/`C`/`D` checks; absent or ambiguous proof fails closed without changing dashboard bytes.

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

1. Freeze and test `epp-bootstrap-v1-r1-r9` and the separately closed `epp-bridge-v1-r10-r19`; reject every later v1 record.
2. Bind the bridge checkpoint to the newly approved exact material-change subject, then add v2 schemas/policy/catalog/evidence without altering any enumerated legacy digest.
3. Emit the sole explicit v1-to-v2 migration transition; do not rewrite v1 files and reject a second migration.
4. Freeze implementation candidate `R`; commit independent-candidate evidence as source `S`; generate v2 dashboard only as dashboard-only successor `C`; then persist independent delivery-only verification in descendant `D` without treating `D` as a source input for the snapshot at `S`.
5. On rollback/removal, retain all source evidence and v1 manual validation instructions; v2 dashboards become stale/unsupported and cannot be approval evidence.
6. The closed correction record is append-only and remains inspectable on rollback. Removing or downgrading to a validator that cannot interpret it returns the six digest findings and 31 tree-pointer findings to unresolved/fail-closed status; it never rewrites history or preserves a virtual corrected view.
