# Data Model: Package Boundaries and Workspace Use Cases

This feature changes ownership and contracts, not persisted schema. The entities below are code and policy concepts; all existing SQLite tables and workspace files remain unchanged.

## Package Rule

- `owner`: stable source-surface name
- `roots`: production source roots covered by the rule
- `imports_as`: top-level import names owned by the surface
- `allowed_dependencies`: direct owned surfaces this owner may import
- `forbidden_modules`: host/runtime modules forbidden for this owner
- `declared_distribution`: package metadata file checked for parity
- `responsibilities`: concise owned behavior
- `temporary_exceptions`: file/edge/reason/removal condition; empty at completion

Validation: roots and import names are unique; dependencies reference known owners; the graph is acyclic; every discovered owned edge is declared; metadata and policy agree; exceptions must be exact and expiring.

## Workspace Identity

- `workspace_id`: immutable identifier
- `workspace_dir`: confined canonical root
- `display_name`: user-facing name
- `session_id`: explicit agent/session binding
- `agent_id`: selected agent identity

Relationships: a workspace has zero or more sessions; a session belongs to exactly one workspace; operations carry explicit identity and never infer it from recent activity.

## Workspace Command

- `operation`: stable application action
- `workspace_id` or `session_id`: explicit target
- `payload`: validated operation-specific value object
- `deadline`: positive bounded duration
- `cancellation`: caller cancellation signal

State: received → validated → authorized/resolved → executing → succeeded or failed/cancelled/timed-out. No failed terminal state is silently converted to success.

## Workspace Result

- `operation`: originating action
- `value`: immutable operation-specific result
- `effects`: durable changes requested/completed
- `notifications`: refresh events attempted
- `warnings`: redacted non-fatal diagnostics

Validation: results contain no credentials, raw secret-bearing commands, HTTP types, or adapter-specific objects.

## Application Error

- `code`: `not_found`, `invalid_input`, `conflict`, `forbidden_path`, `dependency_unavailable`, `timeout`, `cancelled`, or `internal`
- `message`: safe stable explanation
- `operation`: affected action
- `details`: redacted structured context only
- `cause`: internal-only chained exception

Mapping: transport adapters map codes to the established HTTP status categories; use cases never construct transport exceptions.

## Workspace Repository Contract

Operations cover workspace CRUD/list/touch, explicit session association/title/list/select, context load/save, settings, remote metadata, tool selections, and credential-reference status. Records retain existing identifiers and nullable/default semantics.

## File and Path Contract

Operations cover confined resolution, metadata/tree, byte/text read, atomic write, create/move/delete, backup create/list/read/delete/restore, and preview/download classification. Every path is relative to an explicit workspace capability and preserves no-follow protections.

## Version-Control Contract

Operations cover status, diff, revert, commit, history, push, pull, checkout/create branch, and merge. Remote operations receive credential references separately from URLs/argv. Results expose redacted output and stable conflict/error categories.

## Blocking Execution Contract

- `work`: callable owned by an adapter
- `deadline_seconds`: positive finite value
- `operation_name`: safe telemetry label
- `capacity_key`: optional workspace/resource serialization key

Terminal outcomes: completed, timed out, cancelled, dependency unavailable, or failed. Capacity is bounded and shutdown awaits or cancels owned work.

## Notification Contract

- `event_type`: tool list, workspace activation, session selection, or context refresh
- `workspace_id`/`session_id`: explicit scope
- `generation`: optional monotonic change value

Delivery occurs after durable mutation. Failure is observable and non-transactional for this feature.

## Compatibility Adapter

- `legacy_symbol`: old callable/import path
- `delegate`: one owned application operation
- `live_callers`: evidence list
- `removal_condition`: exact call-graph/test condition
- `expiry`: one release after Feature 045

Validation: no independent logic, state access, provider selection, or alternate error semantics.
