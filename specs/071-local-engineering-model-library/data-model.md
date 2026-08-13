# Data Model: Local Engineering Model Library

## Conventions

- All public identities are opaque bounded strings; database primary keys are generated UUID-like IDs.
- Every material JSON document has a supported schema version and canonical SHA-256 digest.
- Timestamps are UTC epoch milliseconds in storage and RFC 3339 in APIs.
- Secret IDs, raw host paths, bearer values, runtime commands, and mutable authority are never serialized into package, plan, operation, evidence, or export records.
- Large bytes live in the content store. SQLite contains identity, state, bounded projections, references, and evidence.

## 1. CatalogSnapshot

An immutable view of model-package metadata available from a bundled or approved remote catalog.

| Field | Type | Rules |
|-------|------|-------|
| `snapshot_id` | string | Unique opaque ID |
| `channel` | string | Bounded approved catalog channel |
| `sequence` | integer | Monotonic within channel |
| `schema_version` | string | Supported major required |
| `catalog_digest` | SHA-256 | Canonical catalog content |
| `source_kind` | enum | `bundled`, `remote`, `offline_import` |
| `source_revision` | string | Immutable for non-bundled source |
| `trust_state` | enum | `bundled`, `verified`, `candidate`, `rejected` |
| `freshness` | enum | `bundled`, `cached`, `live`, `stale` |
| `activated_at` | timestamp? | At most one active snapshot per channel |
| `metadata_json` | object | <=64 KiB, no secrets/paths |

Relationships: contains PackageRevisions; a confirmed InstallPlan points to one snapshot and digest. Refresh creates a candidate rather than mutating a snapshot.

## 2. ModelPackageRevision

A complete declaration of one upstream model revision.

| Field | Type | Rules |
|-------|------|-------|
| `model_id` | string | Stable publisher-qualified slug |
| `package_revision` | integer | Wright packaging revision >=1 |
| `display_name` | string | Bounded user-facing name |
| `publisher` | Publisher | Identity and source evidence |
| `source` | ModelSource | Kind, URI, immutable revision, access policy |
| `tasks` | TaskContract[] | At least one typed engineering task |
| `variants` | ModelVariant[] | At least one; unique IDs |
| `license` | LicenseEvidence | Expression, file/link/digest, attribution, redistribution |
| `limitations` | Limitation[] | At least one for external models |
| `remote_code_policy` | enum | Must be `forbidden` for approved packages |
| `manifest_digest` | SHA-256 | Canonical whole manifest |
| `review_state` | enum | `approved`, `needs_review`, `blocked`, `deprecated`, `withdrawn` |

Identity: `(model_id, package_revision, manifest_digest)`. One revision cannot change in place.

## 3. ModelVariant

A concrete format/precision/platform/resource choice.

| Field | Type | Rules |
|-------|------|-------|
| `variant_id` | string | Unique within package |
| `format` | enum/string | Must be allowed by policy and adapter |
| `precision` | string | Explicit, e.g. `float32` |
| `platforms` | PlatformConstraint[] | OS/architecture/instruction set |
| `accelerator` | ResourceConstraint | `none`, CPU, GPU/provider requirements |
| `runtime` | RuntimeRequirement | Exact adapter contract/range and install state |
| `resources` | ResourceEnvelope | Download, installed disk, RAM/VRAM, time/output ceilings |
| `artifacts` | ModelArtifactDeclaration[] | Non-empty, unique normalized paths |
| `test_vectors` | ModelTestVector[] | At least one mandatory vector for approval |
| `readiness` | ReadinessProjection | Computed, never publisher-authored |

Compatibility and approval never inherit from another variant.

## 4. ModelArtifactDeclaration / ContentObject

The manifest declaration and local immutable object are separate.

### Declaration

| Field | Type | Rules |
|-------|------|-------|
| `path` | relative path | Unicode-normalized, no absolute/traversal/link/duplicate |
| `role` | enum | `model_data`, `metadata`, `license`, `attribution`, `test_input`, `test_expected` |
| `media_type` | string | Must agree with format policy |
| `size` | integer | >=0 and within per-file/aggregate plan ceiling |
| `sha256` | SHA-256 | Required for all acquired files |
| `source_uri` | HTTPS/relative | Approved origin, immutable revision |
| `redistributable` | boolean | Governs export, not install eligibility alone |

### ContentObject

| Field | Type | Rules |
|-------|------|-------|
| `content_digest` | SHA-256 | Primary identity and verified filename |
| `size` | integer | Must match declaration and actual bytes |
| `state` | enum | `staging`, `verified`, `quarantined`, `missing` |
| `relative_storage_key` | string | Internal safe relative key, never API host path |
| `verified_at` | timestamp? | Only for `verified` |
| `verification_json` | object | Bounded algorithm/size/source facts |

Transitions: `staging -> verified | quarantined`; `verified -> missing` only during reconciliation; immutable verified bytes never return to staging.

## 5. RuntimeAdapterRecord

An approved separately managed runtime implementation.

| Field | Type | Rules |
|-------|------|-------|
| `adapter_id` | string | Stable provider-neutral ID |
| `adapter_version` | semver | Exact installed version recorded in evidence |
| `contract_version` | string | Supported major required |
| `supported_formats` | string[] | Explicit allowlist |
| `supported_tasks` | string[] | Typed task IDs |
| `platforms` | constraints | Independent runtime compatibility |
| `state` | enum | `absent`, `installed`, `healthy`, `unhealthy`, `blocked` |
| `evidence_digest` | SHA-256? | Health/conformance evidence |

No runtime command, endpoint, environment secret, or global install action is included in a model manifest.

## 6. ModelInstallPlan

An expiring effect preview bound to exact identities and one authenticated principal.

| Field | Type | Rules |
|-------|------|-------|
| `plan_id` | string | Unique |
| `plan_digest` | SHA-256 | Canonical full preview |
| `principal_id` | string | Confirmation scope |
| `model_id` / `package_revision` / `variant_id` | identity | Exact candidate |
| `snapshot_id` / `manifest_digest` | identity | Invalidate on change |
| `operation_kind` | enum | install/import/update/rollback/export/uninstall/purge/runtime review |
| `effects` | Effect[] | Sources, exact/maximum bytes, paths in safe terms, refs, rollback/cleanup |
| `blockers` | Blocker[] | Stable category, message, recovery; empty when confirmable |
| `runtime_requirement` | object | Existing adapter or separate-plan blocker |
| `secret_reference_id` | string? | Opaque, excluded from digest/export/logs except presence |
| `created_at` / `expires_at` | timestamp | Expiry > creation, bounded lifetime |
| `state` | enum | `preview`, `confirmable`, `blocked`, `confirmed`, `expired`, `invalidated` |

Transitions: `preview -> confirmable | blocked`; `confirmable -> confirmed | expired | invalidated`. Confirmation is one-time and digest-bound.

## 7. ModelOperation

A durable, idempotent execution state machine.

| Field | Type | Rules |
|-------|------|-------|
| `operation_id` | string | Idempotency identity |
| `plan_id` / `plan_digest` | identity | Exact confirmed authority |
| `kind` | enum | acquire/import/verify/install/test/enable/update/rollback/export/disable/uninstall/purge/cleanup |
| `state` | enum | See transitions below |
| `phase` | stable string | User-facing current phase |
| `progress` | object | Bounded bytes/items, never secrets |
| `result` | object? | Exact installation/export/evidence identities |
| `failure` | Failure? | Stable category, safe message/recovery |
| `cancellation_requested_at` | timestamp? | Late output cannot turn cancelled into success |
| `trace_id` | string | End-to-end correlation |
| `cleanup_state` | enum | `not_needed`, `pending`, `clean`, `residue`, `unknown` |

Core transitions:

```text
prepared -> running -> verifying -> testing -> activating -> succeeded
                    \-> cancelling -> cancelled
                    \-> failed -> cleaning -> failed
                    \-> blocked
```

Operation-specific phases may be skipped, but terminal states are immutable. Retry creates or resumes using explicit idempotency/recovery rules.

## 8. ModelInstallation

One locally installed exact package/variant.

| Field | Type | Rules |
|-------|------|-------|
| `installation_id` | string | Unique |
| package/variant/manifest identities | exact tuple | Immutable |
| `installation_digest` | SHA-256 | Manifest + content + adapter identity |
| `state` | enum | `installed`, `testing`, `ready`, `unhealthy`, `disabled`, `uninstalled`, `missing` |
| `runtime_adapter_id/version` | identity | Exact tested adapter |
| `active_revision` | boolean | At most one per model/variant scope |
| `predecessor_id` | string? | Update/rollback lineage |
| `standard_test_evidence_id` | string? | Required for `ready` |
| `installed_at` / `last_verified_at` | timestamp | Durable |

Transitions: `installed -> testing -> ready | unhealthy`; `ready -> disabled | unhealthy`; `disabled -> ready | uninstalled`; update activates a tested successor atomically; rollback activates a tested predecessor.

## 9. ModelTestVector / ValidationEvidence

### Vector

| Field | Type | Rules |
|-------|------|-------|
| `vector_id` / `version` | identity | Unique within package |
| `task_id` | string | Must match declared task |
| `input_schema_digest` | SHA-256 | Exact typed contract |
| `output_schema_digest` | SHA-256 | Exact typed contract |
| `deterministic_seed` | integer/string | Required even when adapter declares it unused |
| `units` / `coordinate_convention` | object/string? | Required when material to the task |
| `input` or `input_artifact` | JSON/ref | Bounded and deterministic |
| `expected` | predicate object | Exact/range/tolerance/category, no executable assertion |
| `limitations_exercised` | string[] | Non-empty links to declared limitation IDs |
| `limits` | object | Load/infer/output/resource ceilings |

### Evidence

Records package, variant, artifact set, adapter, host compatibility projection, vector, input/output digests, timing/resources, validation results, cleanup, limitations, and trace. It contains no reusable authority and is bounded to 1 MiB. Its deterministic `material_evidence_digest` excludes timestamps, trace IDs, timing, measured resources, and host diagnostics; those live in a separate observation digest.

## 10. ModelCapabilityBinding

Workspace-scoped mapping from a typed task to one installation.

| Field | Type | Rules |
|-------|------|-------|
| `binding_id` | string | Unique |
| `workspace_id` | string | Existing workspace FK |
| `installation_id` | string | Must be exact and ready |
| `task_id` | string | Declared/supported |
| `tool_name` | string | `wright_model__<model-id>__<task>` normalized |
| `binding_digest` | SHA-256 | Exact workspace/install/task/policy identity |
| `state` | enum | `enabled`, `disabled`, `stale`, `blocked` |
| `policy_snapshot_digest` | SHA-256 | Gateway decision context |

Only `enabled` + healthy + non-stale bindings are discoverable. Binding never contains a runtime endpoint.

## 11. ModelReference and Lease

| Field | Type | Rules |
|-------|------|-------|
| `reference_id` | string | Unique |
| `content_digest` / `installation_id` | target | At least one |
| `kind` | enum | package, active_revision, workspace, workflow, run, export, operation, evidence |
| `owner_id` | string | Bounded durable identity |
| `state` | enum | `active`, `detached`, `archived` |

Leases are short-lived operation/runtime holds with expiry and heartbeat. Purge requires no active durable reference and no unexpired lease. Private/gated content also carries an access scope and is never deduplicated into broader visibility.

## Stable failure categories

`source_unavailable`, `source_changed`, `source_gated`, `credential_missing`, `license_unapproved`, `license_changed`, `manifest_invalid`, `unsafe_format`, `remote_code_required`, `path_unsafe`, `undeclared_file`, `size_exceeded`, `digest_mismatch`, `insufficient_disk`, `incompatible_platform`, `insufficient_resources`, `runtime_missing`, `runtime_unhealthy`, `runtime_timeout`, `input_invalid`, `output_invalid`, `non_finite_output`, `test_failed`, `cancelled`, `cleanup_residue`, `reference_blocked`, `stale_binding`, `policy_denied`, `export_forbidden`, `internal_error`.

Unknown external failures map to `internal_error` with a bounded safe message; raw exceptions/paths/secrets remain local diagnostics.
