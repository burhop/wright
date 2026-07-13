# Data Model: Gateway Service and MCP 2025-11-25

## GatewaySessionContext

- `session_id`: immutable unique transport/process session identifier
- `principal_id`: authenticated identity or local STDIO process identity
- `workspace_id`: immutable explicit workspace identifier
- `workspace_path`: confined resolved path obtained from workspace service
- `transport`: `stdio` or `streamable_http`
- `protocol_version`: negotiated version after initialization
- `client_info` and `client_capabilities`: negotiated host metadata
- `created_at`, `last_seen_at`, `closed_at`

State: `created -> initialized -> active -> closing -> closed`. Workspace and principal cannot change after creation.

## GatewayRequest

- composite identity `(session_id, request_id)`
- method, correlation ID, started/deadline/maximum deadline
- cancellation token/reason and terminal outcome

State: `accepted -> running -> succeeded|failed|cancelled|timed_out`. Terminal states cannot transition.

## GatewayTool

- stable prefixed name and child server/tool identity
- descriptions, input/output schemas, annotations
- provenance and workspace enablement
- policy classification and approval hints

## GatewayResource

- stable URI, name, MIME type, description, provenance
- workspace ownership and confined artifact/catalog locator
- read authorization and optional list-change capability

## LifecycleSlot

- server ID, lock, current generation, runner, task set
- desired/observed state, last error, timestamps

Each start/restart increments generation. Only the current generation may publish tools/status or own the runner.

## CatalogEntry

- canonical server ID, aliases, name/category/transport
- setup and environment definitions
- source/repository provenance and pinned revision/version where known
- validation status/date/evidence and platform requirements
- reviewed safety metadata and known tool contracts

## AuditDecision

- timestamp, correlation/request/session/principal/workspace IDs
- server/tool/resource/operation
- allowed, reason code, policy version, duration, outcome
- redacted diagnostic metadata only

## Relationships and invariants

- One gateway session owns many requests and sees many projected tools/resources.
- A request belongs to exactly one session; foreign cancellation/access is invalid.
- One lifecycle slot owns at most one current runner generation.
- Catalog identity is canonical; aliases resolve only during migration and are never duplicated in projections.
- Audit records are append-only observations and never supply authorization state.
