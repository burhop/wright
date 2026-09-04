# API, Runtime and Storage Contract

## Transport

Separate authenticated native routes from immutable `/api/process-definitions`. List/create/read/save/check/run/history/inspect/cancel/artifact requests resolve an authorized existing workspace/session in the application service. HTTP mapping: malformed 400, denied 403, absent scoped record 404, stale token/idempotency/binding conflict 409, semantic invalidity 422. Responses include stable code/recovery/trace without absolute host paths or secrets. Headless and HTTP use the same service; parity compares semantic snapshot/output/artifact digests excluding transport timestamps and trace IDs.

## Runtime

Sequential DAG order with declared-order ties. Record actual bounded inputs/outputs, exact operation, timings and cause. Failure prevents dependent execution and records why. Definition/readiness/binding/schema/permission/execution/assertion/artifact-finalization failures stay distinct.

Default total deadline 60 seconds (maximum configurable 300); tool deadline 15 seconds bounded by remaining run time; cancellation/cleanup bound 5 seconds. Limit diagnostics to 256 KiB, structured step values to 1 MiB and each artifact to 10 MiB, with explicit truncation/rejection. Cancellation/completion contend through state CAS; terminal cancellation prevents late publication. Restart classifies abandoned runs interrupted and offers a fresh linked run.

## Persistence

Additive SQLite tables store current/previous document envelope, idempotency request/results, immutable run snapshots, ordered events and artifact index. Use explicit BEGIN IMMEDIATE/rollback and conditional writes. Scope every repository operation by workspace and resolve authorization above it. Never accept a client database path.

Stage artifacts inside managed workspace storage, verify digest/size, atomically promote a generated logical file name, then index successful output. Partial/orphan files cannot become successful outputs. Retrieval checks ownership, containment and digest. Reconciliation reports residue. Retain run/artifacts until explicit authorized removal; no silent expiry. Unsupported readers never rewrite. Migration tests prove backup/interruption recovery/previous-reader rejection and documented retained-data restoration or forward recovery.

## Real MCP integration

Bind exact server ID, tool name, input/output schema digests and current workspace policy. Preflight does not invoke. Revalidate through the existing gateway immediately before calling; changes produce a rebind requirement. The first real proof uses a disposable local stdio MCP server for safe deterministic computation and actual protocol exchange. A mocked gateway is not real-tool evidence. Process documents cannot provide arbitrary server commands.
