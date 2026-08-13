# Data Model: Capability Library and MCP Onboarding

## Ownership rule

Catalog snapshots own descriptive, source, compatibility-claim, and validation-reference metadata. Users and runtime services own installation, process state, credentials, explicit disablement, custom servers, workspace grants, and invocation approvals. Reconciliation may update only catalog-owned fields.

## CatalogSnapshot

Immutable validated catalog payload.

| Field | Type | Rules |
|-------|------|-------|
| `snapshot_id` | UUID/string | Primary key; derived independently of server identities |
| `channel` | string | Approved channel identifier; non-empty |
| `sequence` | integer | Positive and strictly greater than the highest accepted sequence for the channel |
| `schema_version` | integer | Supported catalog format; currently `1` |
| `issued_at` | timestamp | UTC, timezone-aware |
| `expires_at` | timestamp | UTC, greater than issued time and current verification time |
| `payload_sha256` | 64-character hex | Digest of exact canonical payload bytes |
| `payload_json` | JSON text | Schema-valid canonical catalog document |
| `envelope_json` | JSON text | Exact signed metadata without any private key material |
| `signer_key_id` | string | Must resolve to an approved public key |
| `signature` | base64url string | Ed25519 signature over canonical signed metadata |
| `verification_state` | enum | `bundled`, `candidate`, `verified`, `rejected`, `active`, `previous`, `superseded` |
| `verified_at` | timestamp | Set only after signature, freshness, digest, schema, identity, and evidence checks pass |
| `rejection_code` | string/null | Stable code; diagnostics contain no sensitive material |

Uniqueness: `(channel, sequence)` and `(channel, payload_sha256)` are unique.

## CatalogTrustRoot

Public verification policy supplied by a Wright release or explicit administrator configuration.

| Field | Type | Rules |
|-------|------|-------|
| `root_version` | integer | Monotonic software/configuration version |
| `channel` | string | Exact channel scope |
| `key_id` | string | SHA-256-derived public-key identity |
| `algorithm` | enum | `ed25519` only in version 1 |
| `public_key` | base64url string | 32-byte public key; never secret |
| `not_before` / `not_after` | timestamp/null | Optional acceptance window |
| `source` | enum | `bundled` or `administrator_configured` |

No root-update message is accepted from catalog data in version 1.

## CatalogState

Singleton pointer state updated in the same transaction as reconciliation.

| Field | Type | Rules |
|-------|------|-------|
| `state_id` | integer | Always `1` |
| `active_snapshot_id` | FK | Required after bootstrap |
| `previous_snapshot_id` | FK/null | Last known-good active snapshot, distinct from active |
| `active_generation` | integer | Increments on activation and rollback |
| `updated_at` | timestamp | UTC |
| `updated_by` | string | Authenticated local actor identity |

## CatalogActivation

Append-only redacted audit event.

| Field | Type | Rules |
|-------|------|-------|
| `activation_id` | UUID/string | Primary key |
| `from_snapshot_id` | FK/null | Prior active snapshot |
| `to_snapshot_id` | FK | New active snapshot |
| `kind` | enum | `bootstrap`, `activate`, `rollback`, `recovery` |
| `preview_digest` | hex/null | Must match approved preview for administrator activation |
| `actor` | string | Authenticated local identity |
| `trace_id` | string | Correlates API, DB, and UI evidence |
| `occurred_at` | timestamp | UTC |
| `result` | enum | `succeeded`, `rejected`, `recovered` |
| `reason_code` | string/null | Stable machine-readable outcome |

## CatalogUpdatePreview

Time-bounded review binding between an active and candidate snapshot.

| Field | Type | Rules |
|-------|------|-------|
| `preview_id` | UUID/string | Primary key |
| `active_snapshot_id` | FK | Snapshot compared at creation time |
| `candidate_snapshot_id` | FK | Fully verified candidate |
| `diff_json` | JSON | Sorted added, removed, and field-changed identities; contains no secrets |
| `preview_digest` | hex | Digest of active id, candidate id, diff, actor, and expiry |
| `actor` | string | Administrator who requested preview |
| `created_at` / `expires_at` | timestamp | Short-lived review window |
| `state` | enum | `open`, `activated`, `expired`, `superseded`, `rejected` |

Activation fails if the active snapshot, candidate snapshot, actor, digest, or expiry differs.

## CapabilityRecord

Immutable catalog-owned engineering capability metadata.

Key fields from the existing `CatalogEntry` remain. New or clarified fields:

| Field | Type | Rules |
|-------|------|-------|
| `id` | string | Stable canonical identity; unique across ids and aliases |
| `aliases` | string[] | Each alias maps to exactly one identity |
| `kind` | enum | `mcp_server` in this loop; future model/template values reserved but not emitted |
| `evidence_class` | enum | One of the nine classes in research Decision 4 |
| `source_records` | EvidenceSource[] | At least one for official classes; authoritative vendor record required for official status |
| `data_touched` | string[] | Data categories the capability may read or change; empty means the available evidence does not specify them |
| `examples` | string[] | Reviewed engineering examples when available |
| `transport` | enum | `stdio`, `streamable_http`, `sse`, `webmcp`, `none` |
| `install_method` | existing enum | `remote-http`, `uvx`, `pip`, `npm`, `source`, etc. |
| `command` | string[] or URL | Literal data; never executed directly from snapshot activation |
| `license` | string/null | SPDX expression when known; otherwise explicit unknown |
| `auth_model` | existing enum | A requirement fact, not a credential value |
| `platform_support` | map | Evidence about platforms, not a current-machine result |
| `validation_result` | summary | Historic catalog evidence, separate from local ValidationEvidence |
| `default_enabled` | boolean | Advisory default; never applied by catalog activation |

## CapabilityView

Read-only projection returned to the UI.

| Field group | Source |
|-------------|--------|
| identity, description, evidence, requirements, sources, data touched, examples, field provenance | Active CatalogSnapshot |
| compatibility status/reasons/observation age | MachineCompatibilityObservation |
| installed version/state, process status, explicit disablement | Existing `mcp_servers` row |
| credential configured flags | Existing secret-boundary status service; booleans only |
| enabled workspaces | Existing workspace service; identifiers/labels only |
| custom flag | Registry row whose identity is not catalog-owned |
| available actions | Policy projection from all of the above |

The projection must not contain raw credentials, hidden environment values, private paths beyond those already authorized to the user, or approval tokens.

## ImportedMcpDraft and ImportPreview

Non-executing normalization of pasted data.

### ImportedMcpDraft

- `draft_id`
- `name`
- `source_format`: `claude_mcp_servers`, `vscode_servers`, `plain_server`
- `transport`: `stdio`, `streamable_http`, `sse`, or `webmcp`
- `command`: literal executable token or null
- `arguments`: literal ordered strings
- `endpoint`: parsed HTTP(S) URL or null
- `environment_requirements`: names and whether value was supplied, never supplied values
- `header_requirements`: header names and credential-reference requirements, never supplied values
- `warnings`: field path plus stable code/message
- `errors`: field path plus stable code/message
- `redacted_preview`: normalized display-safe object
- `draft_digest`: canonical digest over safe fields

### ImportPreview

- `preview_id`
- `detected_format`
- `drafts[]`
- `document_errors[]`
- `created_at`, `expires_at`
- `source_discarded=true` once response construction finishes

Raw source text is held only for the request lifetime and is neither logged nor persisted.

## MachineCompatibilityObservation

Read-only, time-bounded environment facts.

| Field | Type |
|-------|------|
| `observation_id` | UUID/string |
| `observed_at`, `expires_at` | timestamp |
| `platform_key` | canonical Wright platform |
| `os_name`, `os_version`, `architecture` | strings |
| `distribution_mode` | native/Docker/test |
| `runtimes` | name -> resolved path, version, availability |
| `package_managers` | name -> resolved path, version, availability |
| `container_runtime` | optional availability/version |
| `network_policy` | offline/allowed/unknown, without probing a vendor by default |
| `host_observations` | application/add-on/handshake facts from an approved detector |
| `digest` | canonical SHA-256 |

Derived result per capability:

- `compatible`: every mandatory fact is satisfied.
- `incompatible`: at least one authoritative mandatory fact is false.
- `uncertain`: a mandatory fact is unknown or unverified.
- `blocked`: catalog/policy prohibits onboarding regardless of machine facts.

Each result contains sorted reason codes, human recovery text, and evidence sources.

## InstallPlan

Immutable exact preflight. JSON Schema is in `contracts/install-plan.schema.json`.

Material fields covered by `plan_digest`:

- plan and capability identity
- snapshot id and capability-record digest
- import draft id/digest when applicable
- machine observation id/digest and expiry
- requested scope and workspace id when known
- backend kind
- pinned source/package/container/endpoint and literal arguments
- runtime, host, platform, credential, network, and storage requirements
- license/terms state (`known`, `unknown`, `not_applicable`, or `external_acceptance_required`) plus an optional user-recorded independent-completion timestamp/reference; never an acceptance action by Wright
- planned effects and exact ordered lifecycle steps
- approval gates and blocking reasons
- validation steps and rollback/remove steps
- actor, creation time, expiry

State transitions:

```text
draft -> reviewable -> approved -> applying -> validating -> completed
  |          |            |          |          |
  |          |            |          |          `-> failed -> rolling_back -> rolled_back|rollback_failed
  |          |            |          `-> failed
  |          |            `-> invalidated|expired
  |          `-> blocked|expired
  `-> blocked
```

Approval does not survive a digest, snapshot, observation, actor, scope, or expiry change.

## InstallerEffect and OnboardingRun

### InstallerEffect

- `kind`: `create_isolated_environment`, `download`, `write_config`, `register_endpoint`, `detect_host`, `verify_addon`, `start_child`, `network_request`, `remove`
- `target`: redacted stable locator
- `expected_digest`/`expected_size` where applicable
- `reversible`: boolean
- `rollback_step_id`
- `status`: `planned`, `started`, `succeeded`, `failed`, `rolled_back`

### OnboardingRun

- `run_id`, `plan_id`, `plan_digest`
- `state`: mirrors applying/validating/completed/failure transitions
- `started_at`, `completed_at`
- `adapter_kind`, `adapter_version`
- `effects[]`
- `validation_evidence_id`
- `trace_id`
- `failure_code`, `rollback_state`

## ValidationEvidence

Append-only result for a local installed/connected revision.

- `evidence_id`
- capability and server identities
- snapshot id, capability digest, installed/server revision
- machine observation id and platform/architecture
- state: `not_checked`, `queued`, `running`, `passed`, `partially_passed`, `failed`, `blocked`, `stale`, `unavailable`
- protocol steps: initialize, initialized notification, tools/list
- discovered schema digest and tool count; no credential values or excessive tool output
- optional read-only probe name, argument digest, result digest, and limitation
- timestamps, trace id, reason codes, missing requirements

Only a completed required step set can transition to `passed`. A capability revision, schema digest, credential binding, endpoint, executable, or machine-observation change transitions existing evidence to `stale`.

## MissingCapabilityReport

User-owned and never part of a trusted snapshot without publisher review.

- `report_id`
- requested name and vendor
- source URL
- engineering domain and expected task
- required platform/host application
- notes
- originating search/filter context
- reporter identity and timestamps
- state: `submitted`, `exported`, `under_review`, `matched`, `closed`
- matched capability id when reviewed

## Database migration

Migration 13 adds:

- `catalog_snapshots`
- `catalog_state`
- `catalog_update_previews`
- `catalog_activations`
- `machine_compatibility_observations`
- `mcp_install_plans`
- `mcp_onboarding_runs`
- `mcp_validation_evidence`
- `missing_capability_reports`
- additive `mcp_servers.transport_variant` metadata so `streamable_http` and legacy `sse` remain distinguishable while both continue to use the existing network runner

All tables are additive. Foreign keys use restrictive deletion for audit/snapshot records. Snapshot retention marks rows superseded but does not delete active, previous, referenced, or bundled rows. Existing `mcp_servers` and secret formats are unchanged.

## Invariants

1. Exactly one active snapshot pointer exists after bootstrap.
2. Active and previous never reference the same snapshot.
3. A network snapshot cannot be active unless its verification state is verified.
4. Sequence never decreases for an accepted channel.
5. Catalog activation changes no user-owned state column.
6. Raw secret values appear in none of these entities.
7. Import preview and machine preflight have no installer effects.
8. Apply requires a current approved plan digest.
9. Workspace enablement is not an invocation approval.
10. Catalog rollback never deletes custom entries or validation history.
