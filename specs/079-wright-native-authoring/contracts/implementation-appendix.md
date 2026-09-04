# Frozen Implementation Decisions v1

This appendix resolves planning review C1/U1–U7/I1. The semantic JSON schema and examples in this directory are concrete contract artifacts, not passed implementation evidence.

## Shapes, operation signatures and units

`native-process.schema.json` defines the complete document. `steps` own operation/config, `ports` own step ID/key/label/direction/type/cardinality/required, `connections` own exact port IDs, and `outputs` name artifact output port IDs. Port keys are unique within step/direction. Output declarations must refer to artifact output ports. Empty documents are saveable but not runnable. All unknown keys fail. Unknown versioned operations allow only the bounded config vocabulary in the schema and are unbound/non-runnable. Native semantic IDs remain globally unique, including outputs and connections.

| Operation | Input keys/types | Output key/type | Configuration and effect |
|---|---|---|---|
| `text.input@1` | none | value/text | optional value, max 4000 characters; missing means needs input |
| `quantity.input@1` | none | value/quantity | optional exact value; missing means needs input |
| `artifact.input@1` | none | value/artifact | optional authorized relative path, max 240 characters; recheck file digest at execution |
| `text.join@1` | first, second/text | text/text | optional separator, max 100 characters, defaults to empty string; concatenate in first/second order |
| `text.require@1` | text/text | text/text | 1–20 unique required substrings (max 200 each); fail on absent term, pass through on success |
| `quantity.multiply@1` | left, right/quantity | value/quantity | required target unit; multiply exact values/dimensions and explicitly convert |
| `quantity.convert@1` | value/quantity | value/quantity | required target unit; same dimension only |
| `quantity.range@1` | value/quantity | value/quantity | required minimum/maximum; inclusive, compatible dimension, minimum <= maximum |
| `quantity.format@1` | value/quantity | text/text | optional label max 200; output `label: value unit` or `value unit` |
| `artifact.write-text@1` | text/text | artifact/artifact | required safe filename `.txt/.md/.json/.csv`; UTF-8 bytes, no timestamps/run IDs in content |
| `artifact.read-text@1` | artifact/artifact | text/text | strict UTF-8, max 4000 text characters; reauthorize and digest-check |
| `mcp.call@1` | arguments/text | result/text | config empty; parse arguments as bounded strict JSON object; binding supplied separately; canonical JSON text for structured result, otherwise bounded text |

All builtin ports are required, cardinality one, exactly the listed set. Generic one/many types can be authored, but no builtin silently assembles collections. Missing builtin ports/config produces readiness errors; declared wrong type/key/direction is a structural contract error for a known operation. Unknown operation is structurally saveable, unbound at readiness.

Unit dimensions use length L, mass M, time T: `1` dimensionless; mm/cm/m = L at factors .001/.01/1; mm2/cm2/m2 = L2 at .000001/.0001/1; mm3/cm3/m3 = L3 at .000000001/.000001/1; g/kg = M at .001/1; kg/m3 and g/cm3 = M L-3 at 1/1000; N = M L T-2 at 1; Pa/MPa = M L-1 T-2 at 1/1000000. Multiplication adds exponents; a requested unsupported/incompatible dimension fails. A generic quantity port does not assert a dimension; known input values/config are checked during readiness, runtime-produced values before operation execution.

Canonical decimal representation uses ordinary decimal digits without exponent, leading plus, leading zeroes, trailing fractional zeroes, or negative zero. `1` is valid; `1.0`, `01`, `+1`, `1e0`, `-0` are rejected. `0.001` and `-0.001` are valid. Bound magnitude to 1e18, fractional scale to 18 and significant digits to 34. Compute with Decimal precision 68, trap inexact/rounded/overflow/invalid arithmetic, then require the result fit the same canonical bounds; no silent rounding. Arithmetic operands/config quantity values are immutable exact strings.

Canonical document bytes: strict UTF-8/no BOM, NFC keys/strings, no duplicate keys/floats/negative-zero integers/unpaired surrogates; recursively sort keys by UTF-8 bytes, preserve arrays, minimal safe integers, no spaces, UTF-8 unescaped except JSON quote/backslash/controls. Reuse the proven F02 canonicalization contract only via an extracted generic helper with unchanged F02 vectors; do not import the sample reader into native runtime. Freeze ASCII/Unicode/control/rejection vectors alongside schema/examples. Presentation is a separate map from step IDs to integer x/y in [-100000,100000], with no unknown IDs and at most 100 entries; viewport/selection are transient.

## API and headless

Prefix `/api/native-processes`. Every workspace route has a required `session_id` query (1–200 characters), resolved to an existing managed workspace. Existing Wright auth remains authoritative: current enforced mode authenticates an operator token and role; this milestone does not invent per-user workspace ownership absent from that model. All document/run/file identities must match the resolved workspace, and engineer/admin read/write/run permissions are checked. Compatibility auth mode is loopback/test only under existing host policy.

| Method/path | Input | Output |
|---|---|---|
| GET `/examples` | none | `{examples:[{id,title,definition,presentation}]}` |
| GET `/contract` | session | `{format,schema_version,schema,operations:[{id,inputs,outputs,config_schema,required_config_keys}],canonicalization}`; same packaged schema and registry used by validation/runtime; no tool credentials |
| GET `` | session | `{documents:[{id,title,revision,token,updated_at}],next_cursor}`; limit default 25/max100 |
| POST `` | `{definition,presentation,request_id}` | saved envelope, 201; existing ID conflicts |
| GET `/{id}` | session | `{definition,presentation,revision,token,semantic_digest,updated_at}` |
| PUT `/{id}` | `{definition,presentation,expected_token,request_id}` | saved envelope, 200 |
| POST `/check` | `{definition,bindings}` | `{structurally_valid,ready,findings:[{code,step_id,port_id,message,recovery}]}` |
| POST `/{id}/runs` | `{expected_token,request_id,bindings,derived_from_run_id,timeout_seconds}` | `{run_id,state,semantic_digest}`, 202 |
| GET `/{id}/runs` | session, optional opaque cursor/limit | scoped recent summaries, default25/max100 |
| GET `/runs/{run_id}` | session | snapshot summary, steps, artifacts, cause/recovery, last sequence |
| GET `/runs/{run_id}/events` | session, after_sequence>=0, limit<=200 | events + next_sequence; max200 per response |
| POST `/runs/{run_id}/cancel` | session | current run summary; queued/running cancellation, terminal is unchanged idempotent 200 |
| GET `/runs/{run_id}/artifacts/{artifact_id}` | session | bounded verified bytes, attachment filename, content digest |
| GET `/bindings` | session | actual permitted tool identities/schemas; no invocation |

Enforce document request size 1 MiB plus bounded envelope overhead (maximum total 1100 KiB), run/check body maximum 1100 KiB, remaining requests 64 KiB. Unknown/malformed payload rejects before mutation. Tokens are opaque SHA256, body expected_token is required for update/run. JSON error envelope `{code,message,recovery,trace_id,findings}` uses `NATIVE_INVALID`, `NATIVE_NOT_FOUND`, `NATIVE_DENIED`, `NATIVE_CONFLICT`, `NATIVE_REQUEST_REUSED`, `NATIVE_NOT_READY`, `NATIVE_BINDING_CHANGED`, `NATIVE_RUNTIME_BUSY`, `NATIVE_ARTIFACT_INVALID`, `NATIVE_LIMIT`, `NATIVE_INTERNAL`; runtime-busy is 503. No stack/local paths/secrets are exposed.

CLI `python -m workspace_service.native_process_cli --base-url ... --session-id ... check|run|inspect|cancel` is a headless HTTP client to the same local runtime API and uses existing token environment configuration; it never opens a second direct database executor. Tests compare normalized snapshots/content digests. Run creation is idempotent by request ID + full canonical fingerprint. A repeated submission does not enqueue twice, even after terminal completion.

## Execution ownership, terminal state and artifacts

Native run DTOs (shared UI/headless): a summary contains `run_id`, `process_id`,
`state`, `semantic_digest`, `created_at`, nullable `started_at`/`completed_at`,
nullable `derived_from_run_id`, nullable `reason` finding, and `trace_id`.
History returns `{runs:[summary],next_cursor}`. Inspection adds
`snapshot:{definition,revision,token,semantic_digest}`, `bindings`, `actor`,
`timeout_seconds`, `steps`, `artifacts`, and `last_sequence`. A step contains
`step_id`, `operation`, `state`, nullable start/completion timestamps,
nullable `inputs`/`outputs` maps keyed by exact port ID, and nullable `reason`.
Values are text strings, `{value,unit}` quantities, or
`{artifact_id,content_digest,size,filename}` artifact references. Indexed artifacts
contain `artifact_id`, `step_id`, `port_id`, `filename`, `content_digest`, `size`,
`media_type` and an actual bounded JSON `provenance` object. Artifact filenames
are download metadata; stored file leaves are generated internal identities.
Events return `{events:[{sequence,occurred_at,kind,payload,trace_id}],next_sequence}`.
Cancellation returns the current summary. Findings have `code`, `message`,
`recovery`, nullable `step_id` and nullable `port_id`. Times are UTC ISO strings.

Binding discovery returns `{bindings:[{server_id,tool_name,title,input_schema_digest,
output_schema_digest,input_schema,output_schema}]}`; output schema is nullable.
Run/check binding maps are keyed by step ID; each value contains exactly
`server_id`, `tool_name`, `input_schema_digest`, `output_schema_digest`. Digest of
an absent output schema is SHA256 of canonical JSON `null`. Artifact retrieval
returns attachment bytes with `X-Content-SHA256`. This freezes DTO detail without
adding new execution semantics or promoting mocked transport checks to live proof.

One native runtime coordinator per data root owns an OS-held advisory file lock for its lifetime; acquire before accepting run execution or reconciling prior nonterminal runs. A competing coordinator gets `NATIVE_RUNTIME_BUSY` and never interrupts the owner. File-lock release on process death allows the new coordinator to classify abandoned queued/running runs interrupted. CLI uses the HTTP owner. Tests cover a second coordinator, owner termination/restart and disconnected HTTP caller (caller disconnect does not cancel).

Step states: pending/running/succeeded/failed/blocked/cancelled. On first failure stop scheduling remaining steps; dependents become blocked with root cause and independent pending steps become cancelled with `run_stopped_after_failure`. Run success requires all steps succeed. A queued cancellation transitions directly to cancelled without operation calls. During execution, cancel/deadline/success contend through conditional terminal writes; the first committed terminal transition wins, all later attempts return that state.

Artifact lifecycle: staged → promoted-unindexed → indexed. Promotion occurs before one explicit transaction that checks run and producer step are still running, inserts index/output event, and commits the producing step result. If cancelled, transaction rolls back and promoted file is removed or reported as residue. Crash after promotion before index leaves an unpublishable orphan for reconciliation; crash after committed index leaves a complete digest-checked artifact. Completed steps' indexed artifacts remain inspectable after a later step fails, labeled with producer state and overall failed run. Output content digest excludes run-specific provenance, which is stored separately.

Save idempotency fingerprint includes operation(create/update), workspace, process ID, expected token and full semantic/presentation payload. Replays return the originally saved envelope even if a later successful save exists; clients then fetch current state rather than treating the replay as latest. Run fingerprint additionally includes bindings, timeout and prior-run ID. Same key/different fingerprint is always a conflict.

## Previous reader and recovery procedure

Current dev schema is 16; add native migration 17. Preserve an upgrade-generated verified schema16 backup and the schema17 database. A schema16 reader must reject schema17 without modification. To run a predecessor, stop the runtime, retain the complete schema17 database/WAL backup under a distinct identity, and restore the schema16 backup to a separate data root. That root does not include post-upgrade native work. To regain native work, run a schema17-capable build against the retained schema17 root. No downgrade, overwrite of the newer root or promise of merging the two roots. Tests exercise preservation of both roots, old rejection and successful forward reopening. Actual packaged predecessor/build identities are recorded at T029 before any support claim.

## Scoped PR gates

Dashboard PR: T001–T005 scope, AC01 and dashboard-specific technical/accessibility/package/dev checks; no requirement that native runtime tasks already pass. Authoring PR: T006–T016 and applicable AC02/AC03/AC09 subsets. Runtime/tool PR: T017–T026 with the full cumulative milestone acceptance. T027/T029/T030/T031 are applied to each affected subset candidate; their final checkboxes represent cumulative milestone completion. T028 full five-participant protocol is required for final milestone acceptance; actual earlier pilot evidence can improve earlier increments without being promoted to that result.

T031/T032 record post-merge verification/status, so their integration state is explicitly not-applicable with a reason. The dashboard has 32 implementation tasks and a separate declared integration denominator; completion evidence binds shipped product scope and does not require an endless merge of its own report commit.

## UI and observability obligations

T004/T013/T014/T022 reuse the existing Tokens → Primitives → Components → Patterns layers and design tokens; interactive controls have stable test IDs. T016/T023 verify component states, mocked page journeys and actual backend/browser journeys. No external renderer style may bypass the Wright token layer without an explicit adapter mapping.

T010/T011/T017/T019/T024 preserve the request trace ID through service, SQLite operations and tool dispatch using existing structured JSON logging and local OpenTelemetry facilities. Tests assert trace linkage for save, successful/failed run, artifact publication and denied/failed tool calls; no plaintext secrets or complete unbounded payloads in logs. T023/T025 inspect actual trace linkage. Artifact UI shows actual constraints, operation/input/binding identity and provenance; it must not invent an LLM prompt or Python script for a deterministic operation that used neither. T029 verifies packaged/native and Docker tracing behavior using the existing offline/local collector policy.
