# Contract: preparation, declared interaction and run continuity

## Immutable input overlay v1

`wright.process-input-snapshot/1` pins ProcessRef plus typed input bindings,
explicit-default resolution, authorized file/representation digests and configured
provider choice revisions. A snapshot is prepared, then frozen before dispatch.
Preparation/execution/continuation read it through the same conversion layer.
Preserve source-defined inputs as defaults for legacy requests; UI overrides are
run values, not source edits. Ambiguous or incompatible conversions are rejected.

Extend accepted input settings with optional `interaction_input` metadata:
version=1, bounded value_schema, unit/frame, required, explicit default,
configured option-source binding and dependency selectors. Existing source stays
readable with inferred text/file types; inference cannot invent engineering values.
Schema UI labels and units do not silently alter tool arguments.

Before start, classify every reachable required binding on the compiler's supported
data/order graph. Upstream production is valid only when its declared output and
consumer types align. A declared human response is valid only from the pinned
interaction step. Unsupported conditional reachability is an actionable unsupported
readiness result. Recheck schema/provider/file/source identity immediately before
dispatch; no frontend readiness badge grants permission.

## Human-input source extension v1

Use the existing task/settings source representation; add an explicit template:

```text
settings.authoring_template = "human-input"
settings.human_interaction = {
  "version": 1,
  "kind": "input",
  "instructions": "Choose the comparison to carry forward.",
  "response_schema": {
    "type": "object",
    "properties": {"selection": {"type": "string", "enum": ["a", "b"]}},
    "required": ["selection"],
    "additionalProperties": false
  },
  "output_port": "response"
}
performed_by = "engineer"
```

This is a semantic settings illustration, not a new source-language parser. The
actual `.wflow` fields remain the existing indented, JSON-valued source grammar.
Implementation must round-trip this declaration through canonical source/diagram
serialization and declare a typed output port consumed by downstream steps.

Compiler validates one response output, bounded nonexecutable schema, connected
upstream evidence and declaration compatibility. It does not create checkpoints
because an LLM asks a question. At the declared cursor the existing executor
records a barrier with exact source, input snapshot, upstream digests, schema and
checkpoint identity. No downstream execution is released before a valid response.

Response submission validates the frozen schema/subject and server-derived actor,
persists immutable values and one-shot claim, records an EngineeringResult at the
declared port, and resumes the same run. Declining/cancelling is explicit policy;
there is no forced answer. Two simultaneous submissions cannot resume twice.

Existing review/validation/external-action checkpoints retain their own decisions,
subjects and evidence. Do not turn input responses into approval receipts or
combine independent approvals under a single checkbox.

Scoped review requests retain `decision_receipt` in the existing approval
continuation JSON, atomically with its pending-to-decision transition. Terminal
artifact reviews retain their request ID in the existing immutable decision JSON.
No additional decision database or lifecycle engine is introduced. Actor and run
are derived from the authorized process scope and recorded checkpoint. Changed
requests conflict; the same request can reconcile a lost run projection write.
The recorder projects terminal artifact approval/changes-requested outcomes and
retains their exact review event. Review acceptance does not dispatch an external
operation. Older decisions without request metadata preserve their history shape.

## Continuation and source compatibility

Continuation v3 adds checkpoint_kind (approval/input), input_snapshot_id/digest,
response_id/digest and compatible execution state. Existing v2 approval records
remain readable and resumable under their original checks. Changed accepted source,
upstream subject, required input or profile invalidates continuation; UI labels
and layout alone do not.

Do not relax the existing compiler's supported DAG/rework scope or port checks.
Invalid drafts never replace accepted source. Add editor controls for input schema
and declared interaction without replacing the refined canvas/inspectors.

## Backend-owned lifecycle

Native approved action requests are supervised on the same recorded run through
the existing approval executor and consume authority. Persist the exact request
and authenticated principal before provider dispatch. Observer detach does not
cancel the owner. The response may acknowledge authorization before provider
acceptance: `PendingInteraction.action_receipt` retains the separate submission,
delivery, observed outcome and cancellation evidence. Unknown consumed operations
and unfinished continuation claims cannot be replayed; confirmed delivery with
no downstream claim may continue without re-dispatch. Interrupted claims are
sealed as outcome_unknown before final recorder publication. A matching finished
retry is read-only. Browser-cached intent is for explicit reconciliation only,
scoped to the exact process revision/run; it does not grant action authority.

One source-run use case handles readiness, input snapshot, durable start receipt,
run allocation and execution task ownership. It invokes existing
`execute_prompt_workflow`, gateway, recorder, approval/rework and async-operation
machinery. Start/follow are separate; observer disconnect cancels only observation.

The supervisor is local to the existing runtime, bounded and lease-aware. It is
not a new graph scheduler. Persist enough identity before tool dispatch to
reconcile lost acknowledgements. Backend death marks uncertain active segments
interrupted; reconstruction of waiting/finished state does not imply replay is safe.

Keep model/tool-call timeouts finite. Multi-hour supported external operations
use `workflow_async_operations.py` identities, read-only status/results and declared
poll/deadline/cancel policy. Do not extend a model call into an unlimited print monitor.
Absent remaining-time/% data is null; observed_at and stale_after are visible.

Runtime AI outcome is completed/blocked/error. An undeclared request for more user
information becomes an `INTERACTION_NOT_DECLARED` diagnostic with owning step and
correction, following configured failure/recovery policy. Never ask it as an
opportunistic runtime form or invent an engineering assumption to continue.

The configured tool-free model adapter uses the closed
`wright.unattended-step/1` outcome from `core.workflow_step_outcomes`:
version, status (completed/blocked/error), response (document string), and reason
(null for completed; input_required/capability_unavailable/execution_failed for
blocked/error). This disposition is separate from the requested document format.
The adapter preserves usage and disposition metadata on its existing string
response; execution checks it before saving, publishing or releasing downstream
work. A bare prose response or invalid envelope produces MODEL_OUTCOME_INVALID.
Legacy trusted injected string callbacks remain usable; they are not evidence
that a new external model adapter has qualified this contract.

Existing MCP task evidence envelopes retain their successful tool-call numbers.
Missing user dependencies use blocked + reason=input_required. A mixed
blocked/question-and-tool decision cannot dispatch its tool call; a formatting
repair cannot add an input request or replay an engineering operation. Questions
inside legitimate engineering documents are not classified by prose heuristics.
Recorded failures are optional bounded diagnostics[] in the shared interaction
projection, with correction, exact owning step and canonical log reference.

## Neutral permitted MCP action

Add a bounded `mcp-operation` kind to the existing approved action dispatcher.
Its frozen subject contains exact configured server/tool/schema digest, resolved
argument/artifact hashes, destination identity, settings and operation policy.
Validate qualification/authority/freshness at consumption; invoke through existing
GatewayService. The browser only requests the existing permitted action ID.

The backend implementation qualifies explicit version-1
`wright/approved-operation` metadata (effect, destination/file arguments,
structured accepted/rejected status values and provider reference). This is an
optional Wright adapter contract. Missing qualification blocks readiness; it is
not inferred from ordinary MCP tool names or success prose. Source declares exact
connected text/JSON/file argument representations and pins the qualification
digest. Observe mode pins `wright/operation` and each actual status/result/cancel
tool identity before approval. Receipt mode does not imply observed completion.
See [operation evidence/configuration](../evidence/mcp-operations.md) for the
bounded declaration and checked ownership.

Retain local_review/test_handoff aliases and historical records. Test authority
cannot qualify a physical action. Submission accepted, observed start/completion,
rejection, cancellation and unknown outcome are separate recorded receipts/events.
Unknown outcome blocks mutation replay and prompts reconciliation, not blind retry.
Use a nonphysical isolated provider operation for feature acceptance; device/supplier
dispatch needs separate authorization and qualification.

## Required checks at implementation

Explicit `mcp_file_dependencies` are supported on both exact MCP calls and scoped
AI MCP tasks. Each connected `workspace_file` must match its producer's retained
path, byte count and SHA-256 immediately before consumption. Explicitly supplied
or defaulted prepared file inputs are supported through the same identity check;
they are not represented as tool-produced engineering results. A missing recorded
byte count, changed bytes, mismatched path or unavailable file blocks consumption.
The AI receives
verified locator metadata; binary contents are not loaded as prompt documents.
This declaration does not add tools or widen an agent's capability scope. Plain
AI tasks cannot declare application file imports. Missing, changed or mismatched
files fail before the consumer's first tool/model call and emit an exact consumer
`step_diagnostic`. A historical error after a completed producer, without an exact
failure event, links to the run rather than attributing failure to that producer.

Snapshot/source mismatch; file changed during preparation; producer unavailable;
unsupported graph/schema; required later input missing; declared upstream output;
two checkpoint sequence; response schema failure; stale response; duplicate/lost
acknowledgement; tab disconnect; backend reopening; old v2 checkpoint; uncertain
action; cancellation actual outcome; finite async-operation policy; undeclared
clarification. Preserve 082 validation subjects/revision budgets and 081 evidence.
