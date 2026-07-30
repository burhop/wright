# Workspace Surfaces Data Model

**Version**: planning draft 1  
**Persistence**: SQLite/WAL metadata plus content-addressed file-vault payloads  
**Rule**: persisted intent is authoritative only after current workspace, source, runtime, target, and policy reconciliation

## Identity and Scoping

All public identifiers are opaque UUID/ULID values. Every query that can confer authority includes `user_id`, `workspace_id`, and the applicable session or surface identity in its repository predicate. Friendly names, URIs, paths, PIDs, ports, and URLs are never authorization keys.

| Identifier | Scope | Stable across restart | Notes |
|---|---|---:|---|
| `surface_id` | workspace + logical source/output | Yes | Durable intent and revisions |
| `instance_id` | surface + runtime generation | No | One live execution/isolated instance |
| `runtime_id` | workspace + managed launch | Reconciled | Never trust without generation/ownership proof |
| `presentation_id` | instance + panel/browser view | No | Opaque preview route identity |
| `source_id` | workspace + source kind/version | Yes | Preference/grant key component |
| `display_id` | workspace execution + producer logical output | Yes within output policy | Maps updates to revisions |
| `grant_id` | user + workspace + source/version + operation | Policy-dependent | Revocable and risk-tiered |
| `message_id` | surface protocol exchange | No | Replay/idempotency window only |

## Core Aggregate

### SurfaceDescriptor

The client-facing discriminated projection. It contains no raw target URL, command secret, durable credential, filesystem escape, or PID authority.

| Field | Type | Rules |
|---|---|---|
| `schema_version` | literal `1` | Unknown major versions rejected |
| `surface_id` | opaque ID | Stable logical identity |
| `workspace_id` | opaque ID | Exact owner; never inferred from client route alone |
| `source` | `SurfaceSource` | Discriminated source and provenance |
| `title` | bounded string | Sanitized display text |
| `lifecycle` | enum | `declared`, `starting`, `ready`, `unhealthy`, `stopping`, `stopped`, `failed` |
| `instance` | optional summary | Present only for a reconciled current instance |
| `presentations` | list | Eligible panel/browser actions and current presentation IDs |
| `capabilities` | list | Declared plus policy-projected availability, never raw grants |
| `diagnostic_summary` | summary | Redacted state, correlation ID, recoverable actions |
| `revision` | integer | Optimistic concurrency/version projection |
| `created_at`, `updated_at` | timestamps | UTC |

### SurfaceSource

Discriminated by `kind`:

- `file`: canonical workspace-relative path, file identity, media metadata, viewer provider compatibility ID.
- `display`: producer execution, logical `display_id`, current revision, durability, media representations.
- `live_app`: manifest ID/version/hash, launcher or approved attachment provenance, sharing mode.
- `mcp_app`: MCP server connection identity, tool/result association, server-scoped `ui://` URI, content hash, protocol version.
- `external_url`: normalized display URL, explicit approval identity, `view_only=true`; never has managed/bridge capabilities.

Source version is immutable for grants. A manifest hash, MCP resource hash/server generation, file revision, or normalized external origin change creates a new source version when authority could change.

## Runtime and Presentation

### SurfaceInstance

| Field | Type | Rules |
|---|---|---|
| `instance_id` | opaque ID | Unique generation |
| `surface_id`, `workspace_id` | IDs | Required ownership tuple |
| `generation` | monotonic integer | Prevent stale runtime/message reuse |
| `state` | lifecycle enum | State machine below |
| `sharing_mode` | `shared` or `isolated` | Controls reuse across presentations |
| `runtime_id` | optional ID | Only live apps require a process/attachment runtime |
| `started_at`, `ready_at`, `ended_at` | timestamps | Nullable by state |
| `last_health` | status summary | Bounded/redacted |
| `failure` | optional stable error | Code, safe message, trace ID, retryability |

State transitions:

```text
declared -> starting -> ready <-> unhealthy -> stopping -> stopped
    |          |          |          |             |
    |          +--------> failed <---+-------------+
    +-------------------------------> stopped
stopped/failed -> starting creates a new generation
```

Illegal transitions return a stable conflict and never mutate the row. Every transition uses optimistic version checks, writes one structured audit event, and performs external work through an idempotency key/outbox boundary.

### RuntimeRecord

| Field | Type | Rules |
|---|---|---|
| `runtime_id`, `instance_id`, `workspace_id` | IDs | Exact binding |
| `ownership` | `launched`, `attached_verified`, `external` | `external` cannot be managed/proxied |
| `platform` | `posix`, `windows_job`, `container`, `remote_adapter` | Adapter selection |
| `pid` + `process_created_at` | optional | Reconciled together; never authority alone |
| `job_or_group_id` | optional opaque/ref | Local adapter detail, encrypted/redacted as needed |
| `manifest_hash`, `generation` | immutable values | Detect drift/replay |
| `lifetime` | policy | App-declared; default `workspace` |
| `limits` | bounded policy | CPU/memory/process/log/restart/time |
| `lease_expires_at` | optional | Used by lease lifetime |
| `idle_timeout_seconds`, `last_activity_at` | optional | Idle policy uses only defined app/presentation activity; unrelated workspace traffic never refreshes it |
| `stop_deadline` | optional | Cleanup/recovery evidence |

### TargetPin

Internal-only immutable record created after policy validation.

| Field | Rules |
|---|---|
| `target_pin_id`, `instance_id`, `workspace_id`, `generation` | Exact tuple |
| `scheme` | `http` or `https`; WebSocket is derived transport |
| `numeric_address`, `address_family`, `port` | Normalized and policy-checked |
| `host_header` | Derived from declared target, never request input |
| `base_path` | Normalized absolute path without traversal |
| `resolved_names` / `resolution_evidence` | Bounded audit evidence; no secrets |
| `ownership_proof` | Launcher socket/process association or approved attachment attestation |
| `allowed_preview_origin` | Exact origin for HTTP/WS policy |
| `created_at`, `expires_at` | Revalidate on expiry/restart |

The public API never serializes this record.

### Presentation

| Field | Type | Rules |
|---|---|---|
| `presentation_id` | opaque ID | Public routing identity |
| `instance_id`, `surface_id`, `workspace_id`, `user_id` | binding tuple | Checked on every bootstrap/control request |
| `kind` | `panel` or `browser` | Same instance unless isolated mode |
| `state` | `issued`, `active`, `inactive`, `closed`, `expired` | Separate from runtime state |
| `effective_origin` | origin | Per-instance isolation; never Wright control origin |
| `bootstrap_nonce_hash` | optional hash | Single use; raw token not stored |
| `cookie_audience` | value | Exact presentation/origin binding |
| `created_at`, `last_seen_at`, `expires_at`, `closed_at` | timestamps | Bounded lifetime |

`panel_url`/`browser_url` are derived short-lived absolute links and are not durable fields. The raw token is carried only in the URL fragment, POSTed in a bootstrap request body, exchanged for a presentation cookie, and removed from the visible URL before app navigation.

### PresentationPreference

Primary key: `(user_id, workspace_id, source_id)`.

Fields: preferred `panel|browser`, source version observed, revision, timestamps. It is a hint only. On open/restore, Wright rechecks source policy, panel isolation/framing eligibility, host adapter support, runtime identity, and current grant state. Invalid choices produce a safe fallback plus reason.

## Managed App Declaration

### LiveAppManifest

Immutable versioned declaration validated by `contracts/live-app-manifest.schema.json`.

- Identity/title/version/source provenance.
- Launch mode: `command` with argv array or `attach` with declared URL. Shell strings are forbidden.
- Working directory restricted to workspace policy.
- Environment uses literal safe values or named secret references; resolved secrets are never serialized back.
- Injected port/address/base-path variables and framework adapter hint.
- Readiness and health probes with timeouts/intervals/status bounds.
- Sharing, presentation, framing, live transport and navigation declarations.
- Permissions Policy/browser capabilities and Wright bridge capabilities.
- Lifetime and resource/log/restart/transport limits; optional values inherit the versioned safe baseline in `policy-defaults.md`, never infinity.
- Explicit ownership policy (`wright_owned` for launched commands or `approved_attach`) and mutually consistent launch mode.
- Redaction patterns and documentation links.

Manifest validation does not authorize launch. RBAC, workspace policy, source trust, grant and platform capability checks follow validation.

## Display Data

### DisplayArtifact

| Field | Rules |
|---|---|
| `artifact_id`, `surface_id`, `workspace_id` | Exact ownership |
| `display_id` | Bounded producer logical identity |
| `revision` | Monotonic per display; idempotency key prevents duplicates |
| `producer_execution_id` | Execution/source provenance |
| `generation_provenance` | Required generated-artifact verification record described below |
| `representations` | Ordered MIME metadata; payloads stored by vault digest |
| `title`, `accessibility_description`, `dimensions` | Validated bounded metadata |
| `durability` | `durable`, `session`, `ephemeral`; beginner defaults durable |
| `created_at`, `supersedes_artifact_id` | Immutable history link |

### DisplayRepresentation

- `mime_type`: allowlisted type; producer label does not grant active behavior.
- `vault_digest`, `byte_length`, `content_hash`.
- `metadata`: validated per MIME schema; depth/items/strings bounded.
- `renderer_id`, `renderer_contract_version` selected by host policy.
- `trust`: `safe_data`, `sanitized_html`, or `isolated_active_html`.
- `fallback_rank` and `accessibility_fallback`.

Revision update transaction: validate execution token and workspace; enforce producer/display binding; serialize within resource limits; write payloads content-addressed; insert immutable revision; compare-and-set current pointer; emit update event. Late lower revisions never replace the current pointer.

### GenerationProvenance

Required for every generated display artifact and visible only through authorized workspace verification UI:

- `mode`: `agent_generated` or `direct_execution`.
- `prompt`: exact originating prompt stored in the vault for agent-generated output; direct execution stores an explicit no-prompt marker rather than inventing one.
- `effective_constraints`: immutable, versioned constraints snapshot used for generation/execution.
- `script_vault_digest`, `script_content_hash`, `script_revision`, and interpreter/environment summary needed to identify the exact Python script.
- `task_id`, `execution_id`, `trace_id`, and creation timestamp.

The artifact retains these references under normal workspace authorization and retention. General logs, traces, errors, and audit attributes contain only IDs/hashes and never the prompt, full constraints, or script content.

## Capability and Messaging

### CapabilityGrant

| Field | Rules |
|---|---|
| `grant_id`, `user_id`, `workspace_id` | Owner tuple |
| `source_id`, `source_version` | Exact immutable source scope |
| `instance_id` | Required for instance-scoped/high-risk grants |
| `capability`, `operation`, `constraints` | Small enumerated operation plus validated bounds |
| `risk_tier` | `low`, `high`, `mutating` |
| `persistence` | `remembered_exact`, `instance`, `operation` |
| `decision` | `allow` or `deny` with policy/user provenance |
| `expires_at`, `revoked_at`, `used_at` | Enforced transactionally |

Low-risk declared capabilities may be remembered only for exact user/workspace/source/version. High-risk or mutating authority defaults to one operation or instance. Policy may narrow or deny any request but cannot be broadened by a remembered user choice.

### SurfaceMessage

Validated against `contracts/surface-message.schema.json`:

- Protocol version, message/correlation/trace IDs and request/result/event kind.
- Exact workspace/session/surface/instance/document-origin/server binding.
- Operation and bounded JSON payload.
- Creation/deadline timestamp and monotonic surface sequence.
- Idempotency/reply-to identifiers.

Processing verifies authenticated control session, active presentation, generation, origin, browser window source (client side), nonce/replay window, schema, payload size, capability/grant, MCP same-server rules, deadline, and rate. Outcomes are stable success/error envelopes and redacted audit events.

### McpUiBinding

Primary identity: `(gateway_session_id, server_connection_id, upstream_resource_uri, content_hash)`.

Stores canonical UI metadata, accepted deprecated-source indicator, media type, visibility, tool association, resource-content metadata, subscription state, cache expiry, source version, and fallback content pointer. App requests carry this binding so a `ui://` URI cannot resolve against another child server.

## Diagnostics and Audit

### SurfaceDiagnosticEvent

Append-only structured event with timestamp, severity, stable event code, user/workspace/surface/instance/presentation/runtime IDs as applicable, state transition, redacted attributes, trace/span/correlation IDs, retryability, and retention class. It never includes bearer/cookie values, raw Authorization, query secrets, full user content, environment secrets, or unredacted target logs.

Health history and log tails are separately bounded. UI projections expose safe codes/details and correlation IDs, not internal target pins or credentials.

## Persistence and Recovery Invariants

1. SQLite records and vault payloads commit through an application-level transaction/outbox so a current pointer never references missing content.
2. Deleting a workspace revokes presentations/grants first, stops owned runtimes, then schedules payload retention cleanup under existing workspace policy.
3. At startup, all nonterminal runtimes enter reconciliation. PID+creation time, job/group/container identity, target pin, generation and ownership must agree before reuse.
4. A valid process with invalid authority is stopped if Wright owns it; an unowned process is reported and never killed or adopted automatically.
5. Presentation cookies and raw bootstrap/display tokens are not recoverable and therefore expire on server restart unless the deployment's key/lifetime policy deliberately supports reissuance.
6. Schema migrations are forward-only with a tested downgrade/read compatibility path defined in `migration.md`; legacy file tabs migrate to `file` sources.
