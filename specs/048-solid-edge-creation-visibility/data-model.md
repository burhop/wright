# Data Model: Solid Edge Creation Visibility

## CreationProfile

- `profile_id`: immutable identifier; `solid_edge_creation_v1` for this feature
- `provider_id`: `solid_edge`
- `server_ids`: authoritative configured SolidEdgeMCP server identities to which the profile applies
- `allowed_tool_names`: exact allowlist grouped as service status, validation, creation, and created-artifact follow-up
- `denied_tool_classes`: document inspection, geometry inspection, measurement, capability inventory, semantic inventory/resolution, repair, active-document mutation, open/close, and unknown
- `required_arguments`: provider, explicit output path, visible/open behavior, recipe mode, and new-document intent
- `maximum_simple_creation_calls`: `1`
- `maximum_simple_validation_calls`: `1`
- `policy_version`: stable value recorded in diagnostics

Invariants:

- The profile is immutable after a gateway session opens.
- Solid Edge tools not explicitly classified and allowed are hidden and denied.
- A client approval hint or prompt instruction cannot expand the profile.
- Follow-up rebuild/export operations require a `CreatedArtifactBinding` owned by the same session.

## CreationRequest

- `turn_id`: agent turn identity
- `request_id`: MCP request identity
- `correlation_id`: end-to-end diagnostic identity
- `session_id`, `principal_id`, `workspace_id`: immutable authorization binding
- `provider_id`: `solid_edge`
- `artifact_kind`: part, assembly, or sheet metal
- `output_path`: explicit resolved path within the bound workspace and provider allowed roots
- `recipe`: validated design-intent recipe
- `document_mode`: `new`
- `visible`: required true for this workflow
- `close_after_save`: required false unless explicit user intent authorizes closure
- `overwrite`: false by default
- `overwrite_authorized_path`: optional exact path authorized by the user
- `success_criterion`: concise user-facing completion statement

State:

`accepted -> validating -> creating -> saving -> verified -> succeeded`

Any non-terminal state may transition to `failed`, `timed_out`, or `cancelled`. Terminal states cannot transition. Failure ends the workflow; it does not transition into inspection or unrelated recovery.

Invariants:

- Validation completes before provider mutation begins.
- A simple-part smoke contains one `cad.create_part_from_recipe` call and zero inspection calls.
- An existing file cannot be replaced unless its exact path is explicitly authorized.
- The result document remains open and visible at successful completion.

## CreatedArtifactBinding

- `session_id`: owning gateway session
- `turn_id`: creating turn
- `provider_id`: `solid_edge`
- `document_id`: provider-returned identity when available
- `output_path`: confined canonical path
- `artifact_kind`: part, assembly, or sheet metal
- `visible`: observed/returned visibility state
- `open`: observed/returned open state
- `created_at`: monotonic-relative and wall-clock evidence timestamps
- `creation_request_id`: originating request

Invariants:

- The binding is created only from a successful creation result.
- It never binds a document that predated the creation request.
- Rebuild/export authorization matches this binding by provider document identity or canonical output path.
- The binding supplies authorization only within the same gateway session.

## ProgressUpdate

- `event_index`: monotonically increasing replay cursor within one turn
- `turn_id`, `session_id`, `correlation_id`
- `phase`: `planning`, `capability_discovery`, `solid_edge_creation`, `saving`, `verification`, `result_transfer`, or `final_response`
- `status`: `started`, `running`, `completed`, `failed`, `cancelled`, or `timed_out`
- `label`: short human-readable phase label
- `message`: actionable user-facing update without raw internal identifiers
- `elapsed_seconds`: monotonic duration since turn start
- `phase_elapsed_seconds`: monotonic duration since phase start when available
- `operation_request_id`: optional child operation identity
- `heartbeat`: whether the event exists to prove liveness
- `occurred_at`: display timestamp

Invariants:

- The first planning event is available immediately when the turn job starts.
- While a job is running, consecutive progress updates are at most 10 seconds apart.
- Event indices are stable for reconnect replay.
- Messages and labels are redacted and do not contain credentials or raw arguments/results.

## ChatTurnProgressBuffer

- `turn_id`, `session_id`
- `events`: ordered bounded list of `ProgressUpdate`, content/result, error, and completion events
- `first_retained_index`, `next_index`
- `state`: active, completed, failed, cancelled, expired
- `created_at`, `completed_at`, `expires_at`
- `maximum_events`, `maximum_bytes`

State:

`active -> completed|failed|cancelled -> expired`

Invariants:

- Active and recently completed events are replayable from an index.
- Buffer limits never discard terminal state without an explicit reset/expired response.
- Expiration deletes only replay state, not persisted redacted diagnostic evidence.

## DiagnosticRecord

- `event_id`
- `occurred_at`
- `turn_id`, `correlation_id`, `request_id`
- `session_id`, `principal_id`, `workspace_id`
- `phase`
- `operation`: planning, discovery, tool call, result transfer, or final response
- `server_id`, `tool_name`
- `outcome`: started, succeeded, failed, timed_out, cancelled, denied, hidden
- `allowed`, `reason_code`, `policy_version`
- `duration_ms`
- `argument_count`
- `timeout_ms`
- `request_bytes`, `response_bytes`
- `error_type`: redacted classification only

Invariants:

- Every started tool call has exactly one terminal record.
- Payload bodies, environment values, credentials, file contents, and raw protocol messages are never persisted.
- Size and count values are non-negative and bounded.
- Records are append-only observations and never become authorization inputs.

## DiagnosticSummary

- `session_id` and optional `turn_id`
- `active_calls`, `completed_calls`
- `outcome_counts`
- `total_duration_ms`, `average_duration_ms`, `maximum_duration_ms`
- `slowest_calls`: bounded ordered terminal records
- `phase_totals_ms`
- `attributed_duration_ms`, `turn_duration_ms`, `attribution_ratio`

Invariants:

- Active calls have a started record without a terminal record.
- Completion and duration calculations use terminal tool-call records only.
- Attribution ratio never exceeds 1.0 and must reach 0.95 for completed live evidence.

## RuntimeOwner

- `mode`: `api` or `external`
- `component_id`: API process, Hermes gateway process, or another explicit owner
- `server_id`: owned SolidEdgeMCP server
- `process_id`: optional observed child process identity
- `configured_at`

State:

`configured -> active -> stopping -> inactive`

Invariants:

- At most one owner may start/stop/reconcile a given local server.
- External mode makes API startup, workspace reconciliation, and status polling passive.
- A change of owner requires the previous owner to become inactive first.
- Ownership does not bypass authentication or workspace binding.

## Relationships

- One `GatewaySessionContext` has exactly one immutable creation profile or the standard non-Solid-Edge profile.
- One session owns many creation requests, progress buffers, diagnostic records, and created-artifact bindings.
- One creation request produces at most one primary created-artifact binding.
- Progress updates and diagnostic records share turn/correlation identity but have different retention: replay is bounded in memory, diagnostics are append-only in SQLite.
- One runtime owner manages the SolidEdgeMCP child lifecycle; many authenticated clients may perform passive reads.
