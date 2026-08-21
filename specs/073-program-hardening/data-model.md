# Data Model: Engineering Capability Program Hardening

## SupportDiagnosticSnapshot

An immutable, bounded, local-only projection of safe support facts.

| Field | Type | Rules |
|---|---|---|
| `schema_version` | literal `1.0` | Required. |
| `snapshot_id` | opaque string | Random, not derived from user data. |
| `created_at` | UTC timestamp | Required. |
| `expires_at` | UTC timestamp | Later than creation; bounded lifetime. |
| `workspace_id` | safe identifier | Exact caller scope; no filesystem path. |
| `principal_digest` | SHA-256 digest | Irreversible correlation only. |
| `scope` | object | Optional run/session/time bounds, all safe identifiers. |
| `summary` | object | Status, stable reason, safe next action. |
| `providers` | bounded list | Provider kind, safe ID, status, schema/version digest. |
| `state_inventory` | `StateInventory` | Counts/digests only. |
| `failures` | bounded list | Stage, provider kind, stable reason, cleanup truth, recovery. |
| `categories` | bounded list | Included/omitted/redacted/truncated truth. |
| `snapshot_digest` | SHA-256 | Canonical snapshot digest excluding itself. |

Validation forbids raw commands, environment values, credentials, paths,
prompts, tool arguments/results, model tensors/features, artifact bodies, log
bodies, or authority tokens. Lists, strings, and final JSON bytes are capped.

## DiagnosticCategory

| Field | Type | Rules |
|---|---|---|
| `name` | enum | Known allowlisted category. |
| `disposition` | enum | `included`, `omitted`, `redacted`, or `truncated`. |
| `item_count` | non-negative integer | Count after projection. |
| `reason` | stable code | Required unless fully included. |

## DiagnosticExportGrant

Process-local authority proving explicit preview and confirmation.

| Field | Type | Rules |
|---|---|---|
| `token_digest` | SHA-256 | Store only digest; raw token returned once. |
| `snapshot_digest` | SHA-256 | Must match preview exactly. |
| `workspace_id` | safe identifier | Exact match on export. |
| `principal_digest` | SHA-256 | Exact match on export. |
| `scope_digest` | SHA-256 | Prevents scope substitution. |
| `created_at` / `expires_at` | timestamps | Short bounded lifetime. |
| `state` | enum | `previewed`, `consumed`, `expired`, `invalidated`. |

Transitions:

```text
previewed -> consumed
previewed -> expired
previewed -> invalidated (restart, replacement, explicit cancellation)
```

Every non-previewed state is terminal. Export is idempotently denied after the
first successful consume.

## StateInventory

A safe inventory of retained program state without names or content.

| Field | Type | Rules |
|---|---|---|
| `schema_version` | literal `1.0` | Contract version. |
| `data_schema` | integer | Actual SQLite user/schema version. |
| `catalog_snapshot` | safe identity object | Channel, sequence, digest, activation state. |
| `counts` | object | Workspaces, enablements, bindings, runs, reports, model packages, installations, cache entries. |
| `digests` | object | Canonical digests over safe identities only. |
| `storage` | bounded list | Logical state root, persistence kind, writable/available status; no host path. |

## CompatibilityEvidence

| Field | Type | Rules |
|---|---|---|
| `schema_version` | literal `1.0` | Contract version. |
| `evidence_id` | string | Opaque stable record ID. |
| `runtime_version` | string | Exact version. |
| `artifact_digest` | SHA-256 | Exact tested artifact. |
| `platform` | enum | Exact OS. |
| `architecture` | enum | Exact architecture. |
| `storage_profile` | enum | `native` or named Docker profile. |
| `data_schema_before/after` | integers | Required for lifecycle evidence. |
| `checks` | bounded list | Install/start/upgrade/persist/rollback/uninstall/offline results. |
| `evidence_level` | enum | `fixture`, `contract`, `artifact`, `host`. |
| `status` | enum | `passed`, `failed`, `blocked`, `skipped`. |
| `supporting` | boolean | True only for passed exact artifact/host evidence. |

Invariant: `supporting=true` requires `status=passed`, an exact artifact digest,
and evidence level `artifact` or `host`; skipped/inferred evidence is never
supporting.

## EngineeringJourneyEvidence

| Field | Type | Rules |
|---|---|---|
| `journey_id` | enum | MCP-only or MCP-plus-local-model first use. |
| `fixture_profile` | string | Deterministic and offline. |
| `started_at` / `completed_at` | timestamps | Used for deterministic duration bound. |
| `steps` | ordered list | Discover, inspect, plan, enable, preflight, run, inspect, recover/export. |
| `recovery_events` | list | Stable cause/action/result. |
| `accessibility_checks` | object | Keyboard, focus, status, reflow, zoom, reduced motion. |
| `result` | enum | `passed`, `failed`, `blocked`. |
| `evidence_level` | enum | Component, mocked UI, live system, human-repeatable. |

## Relationships

- One preview creates exactly one `SupportDiagnosticSnapshot` and one
  `DiagnosticExportGrant`.
- A snapshot contains one `StateInventory` and bounded safe summaries of
  provider failures and recovery.
- Compatibility evidence validates a state inventory across one exact lifecycle
  transition; it never embeds the underlying data.
- Journey evidence may reference a diagnostic snapshot digest, scenario report
  digest, catalog snapshot digest, and model package digest, but never their
  private bodies.

