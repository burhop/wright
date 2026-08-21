# Contract: Engineering Model Runtime Adapter 1.0

## Purpose

A runtime adapter executes one or more reviewed model formats behind Wright's process and policy boundary. It is not an installer, model source, MCP server, arbitrary Python environment, or long-lived public endpoint.

## Identity and discovery

Before model verification or load, the supervised adapter returns:

- `adapter_id`, `adapter_version`, and `contract_version`;
- supported model formats, engineering task IDs, platforms, architectures, and execution providers;
- input/output schema dialects and maximum message size;
- cancellation and unload capabilities;
- a health state and bounded diagnostics.

Wright compares these facts with the installed RuntimeAdapterRecord and package requirement. An unknown contract major, version mismatch, unsupported format/task/provider, or unhealthy state blocks load.

## Transport and ownership

- The adapter is launched only by Wright's runtime supervisor from an independently approved installation.
- Transport is a private local stdio or authenticated loopback channel owned by Wright. Commands/endpoints are not exposed in API, evidence, exports, Rivet graphs, or model manifests.
- Messages are length-delimited JSON with a 1 MiB default control limit. Model outputs use the smaller package limit.
- The child receives a minimal environment, a read-only installation view, an operation scratch directory, and no source credential.
- One loaded-handle identity is scoped to adapter process, installation, artifact-set digest, and operation/session lease.

## Requests

### `health`

No model input. Returns adapter identity, supported contracts, health, and safe resource facts.

### `load`

Required fields: `request_id`, exact installation/model/variant/manifest/artifact-set identities, safe read-only artifact keys, task, execution provider, and resource/deadline limits.

Returns either a scoped `model_handle` and measured load resources or a stable failure. It must not fetch content, install dependencies, resolve mutable revisions, or execute repository code.

### `verify`

Required fields: `request_id`, exact installation/model/variant/manifest/artifact-set identities, safe read-only artifact keys, declared format, deadline, and parser/resource limits.

The adapter performs only format-specific structural verification and returns bounded facts plus artifact identities. It cannot supersede Wright's digest/license/source policy, fetch content, or load a reusable inference handle.

### `infer`

Required fields: `request_id`, `model_handle`, `task_id`, schema digest, typed input, deadline, and output ceiling.

Returns: exact request/handle/task/schema identities, typed output, output digest, timing/resource projection, warnings, and terminal state. Non-finite JSON numbers are prohibited. Output after cancellation/deadline is discarded by Wright even if emitted by the child.

### `progress`

Long-running `verify`, `load`, `infer`, `unload`, and `shutdown` requests may emit monotonic bounded progress events containing request ID, phase, completed/total items or bytes, safe message, and sequence. Progress is advisory, redacted, and cannot carry payload bytes, paths, tokens, commands, or authority.

### `cancel`

Required fields: target `request_id` and deadline. Adapter acknowledges receipt and stops work cooperatively. Wright escalates to process termination at the cancellation deadline.

### `unload`

Releases one handle and reports remaining handles/resources. Unload is idempotent.

### `shutdown`

Rejects new work, cancels/unloads existing handles, and exits by deadline. Wright records residue if termination or scratch cleanup is incomplete.

## Validation ownership

Wright validates package identity, input schema, byte/resource admission, deadline, output schema, finite values, output bounds, test predicates, authorization, audit, and publication. The adapter validates its format-specific parser/runtime invariants. Either side may fail closed; adapter success never overrides Wright validation.

## Concurrency and cancellation

- Adapter advertises a bounded concurrency count; Wright never exceeds it.
- Each request ID is unique per adapter process. Duplicate active IDs fail.
- Cancellation state wins over any later normal result.
- A killed/crashed adapter invalidates every handle and reports all in-flight requests failed; it is not silently restarted within the same inference request.

## Stable failures

Adapters return a stable category from: `unsupported_contract`, `unsupported_format`, `unsupported_task`, `incompatible_provider`, `artifact_missing`, `artifact_invalid`, `resource_rejected`, `load_timeout`, `load_failed`, `input_invalid`, `inference_timeout`, `inference_failed`, `output_invalid`, `cancelled`, `unload_failed`, `internal_error`.

Raw tracebacks, environment variables, host paths, commands, tokens, and unbounded logs remain private diagnostics and are never placed in the protocol result.

## Conformance requirements

An adapter cannot be marked healthy until deterministic tests prove identity mismatch rejection, format/task mismatch, malformed/oversized messages, missing/corrupt files, bounded verification and progress, load/inference deadlines, cancellation/late-output suppression, invalid/non-finite output, crash cleanup, handle isolation, idempotent unload/shutdown, and no network acquisition.
