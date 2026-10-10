# Frozen model routing and assumption invalidation

## User journey and ownership

A user starts one accepted workflow, sees a declared question or approval in the
same workspace, and resumes that durable run after answering. Changing a model
default during the wait must not silently change the model for its remaining
work. Shared preparation and continuation enforce this; the existing agent
adapters own gateway/SDK qualification and actual invocation evidence. There is
no additional executor, browser authority, approval grant, or vendor protocol.

## Implemented route contract

`wright.workflow-model-routing/1` freezes public text routing
(`hermes-http`, provider, model reference, profile, endpoint digest and
configuration digest) and each qualified native image SDK identity. It carries
no credentials. The ordinary authorized preparer stores it in the existing
execution context, which the existing durable checkpoint/run recorder retains.
Text/MCP AI steps receive the exact expected resolution. Native image steps
retain their existing qualified resolution and SDK digest.

The capability reader accepts native Hermes model-options `provider`/`model`
and the normalized Wright facade's `current_provider`/`current_model`, rejecting
incomplete or conflicting pairs rather than choosing a display alias or an option
from the available-model list. Qualification is a read-only request. Initial
failure produces `WORKFLOW_MODEL_UNAVAILABLE` before execution; a changed
provider/model/adapter/profile or native SDK while waiting produces
`WORKFLOW_MODEL_CHANGED` before the answer/approval can release work. A deliberate
revision starts a new run. Restoring the original configuration allows the same
durable run to continue.

Both declared-input continuation and approval continuation revalidate the
snapshot. Durable restoration additionally checks that the prepared step
resolutions equal the stored snapshot; an unqualified replacement plan cannot
use a modern checkpoint directly. Existing contexts with no routing snapshot
retain their historical shape and are not claimed to contain frozen evidence.
Controlled legacy callbacks lacking the production capability hook remain
compatible.

## Actual invocation boundary

Before ordinary text completion or a translated/recovery MCP decision request,
the existing HTTP adapter creates a fresh private session, requiring HTTP 201,
the exact `hermes.session` object and nested session ID/model. It then requests a
session model lock. It requires the exact
`hermes.session.model_lock` object, session ID, provider, model and runtime
`model_lock: accepted` response before submitting the model request. Collision or
an ambiguous session-creation response cannot borrow existing history. Each
actual bridge request/repair creates a distinct session. An absent,
rejected or different confirmation fails closed. Endpoint/profile changes fail
before requesting even the lock. This is a session-scoped operation, not a write
to global model defaults.

The submission capture includes the confirmed frozen resolution and the exact
transport payload. The response capture adds the provider-reported model and
usage when present. A provider-reported revision can differ from a requested
alias and is recorded separately; the UI alias is not substituted as actual
model evidence. The native image adapter retains its existing qualified SDK
comparison and actual invocation capture.

Boundaries: a confirmed public route does not promise deterministic output or
freeze an upstream vendor's floating alias implementation. Hidden provider
internals remain unobservable. General chat/streaming and process-UI coding roles
remain separate adapter journeys; this change qualifies source workflow work and
does not invent snapshots for historic chat. Legacy checkpoints remain explicitly
legacy rather than silently upgraded.

## Assumptions and existing invalidation

The saved instruction policy permits or rejects assumptions and lists protected
requirements. Model assumptions retain value, units, rationale and affected
output ports in step evidence. The runtime rejects undeclared affected ports and
explicit protected-parameter matches; these checks do not replace engineering
validation or prove semantic compliance.

Existing owners provide the relevant invalidation:

- Editing accepted instruction/policy/source changes the definition digest and
  cannot resume an old checkpoint as the same accepted process.
- Frozen input snapshot and upstream response identities are checked before a
  declared answer. Referenced input and produced artifact bytes are rehashed
  before continuation. Results retain the durable run identity.
- Rework registers a new immutable producer attempt/output revision. The
  validation repository rejects replacing a completed output revision and
  considers only the latest attempt current for that exact run/step/output port.
- Validation profiles and requirement baselines are pinned by version/digest;
  loaders reject changed profile content or a different baseline. Model
  assumptions cannot modify these contracts or manufacture a passing check.
- Sidecar assumptions remain in completed step records across waits. A retry
  clears the in-memory assumption set for that producer so a new attempt cannot
  inherit its previous assumed values as fresh evidence.

There is no public operation for editing a completed run's assumption sidecar in
place. A desired assumption change must change accepted instructions/inputs or
produce a new attempt, using the existing revision path. Sidecar-only assumption
metadata is not a separately addressable validator output or approval subject;
if a process needs to review assumptions independently, it should declare a
structured assumptions output and connect its validator/review. This remains a
bounded authoring concern, not permission to mutate evidence or reuse reviews.

## Isolated verification

New focused tests exercise read-only capability identity, session-lock ordering,
rejected/wrong-model/wrong-session/missing-object confirmations, changed endpoint,
actual response provenance, translated MCP decision capture, frozen native SDK,
legacy contexts, and ordinary plus enrolled approval continuation.

A durable first-question test recreates SQLite-backed owners, rejects a changed
default and an unqualified restored plan while the checkpoint remains unchanged,
then restores the original route, answers, and completes the original run.
Duplicate resume returns the recorded result and does not invoke the model again.
The answer is explicitly attributed as isolated test input, never approval.

Combined routing, adapter, first/conditional input, preparation, approval and
bundle API regressions: **168 passed** (two existing test-client deprecation
warnings). All new routing files pass Ruff. A full adapter suite initially had
**367 passed, 14 fixture setup errors** because sandbox access to installed Hermes
source was denied; the separately authorized complete adapter run then passed
**381 tests** with no failures. These tests use mock model transports and
synthetic responses, not physical operations or proof of a live cloud print.

### Final observer and approval regressions

The final complete adapter suite passed **398 tests**, including actual
text/image/translation/repair payload capture and failure retention. The isolated
workspace/API ownership suites previously passed **146 tests** and the extended
review/routing suites passed **69 tests**. These are overlapping suites, not a
sum of distinct tests. All changed Python files in this subtask pass Ruff.

The model-only execution context is deliberately not integration enrollment.
Automatic decisions, enrolled handoff selection, operation qualification and
submission, and the final gateway dispatch freshness hook require the explicit
integration-policy digest. A normal manual review resumes with its frozen model;
an unenrolled run cannot borrow automatic review authority from routing metadata.
Scoped synthetic test principals retain `integration_test` attribution in their
artifact-review decision/view, external approval decision receipt/attribution,
and durable review events. Attribution does not enroll a policy or grant approval
automatically. Ordinary users retain false attribution; historical records are
not rewritten to claim new metadata.

Actual live model evidence exposed a shared-reference bug: the submitted capture
dictionary was enriched after response, altering the earlier event. Adapter and
bridge observer calls now publish deep snapshots, and the existing recorder
copies nested events/results before retaining them and before notifying UI
observers. **21 routing/recorder/history tests** passed, including an observer
that mutates nested request messages. Submitted request bytes/identities remain
unchanged and the submission/response phases stay ordered. Existing historical
events with missing original phase remain honest; this fix does not reconstruct
unobserved submission evidence.

## Adjacent transfer correction

### Fresh actual invocation readback

After the immutable publication fix, the separately qualified CAD-to-render run
`e333f6183c704380bac48be20b402ccb` completed. A read-only audit of its existing
durable log verified **5** distinct actual bridge submission/response pairs:
confirmed frozen model lock/session identity, ordered phases, unchanged request
digest/messages/schema/instruction identities, and upstream model reporting only
after response. The single actual image SDK capture matched the run's frozen
image configuration digest and retained the actual request-field names/digest.
The readback did not create model requests or decisions and makes no additional
geometry, strength or image-fidelity claim. Report:
`.local-run/process-interfaces-083/instruction-portability/actual-invocation-snapshots-readback.json`.

The served UI transfer walkthrough found that bundle import returned a valid
storage document without the API's scoped source envelope. The import router now
adds authenticated `workspace_id` and `metadata_authority: wright_host`, matching
ordinary source routes. The API regression asserts both fields. Import still
does not transfer credentials, reviews, grants, jobs or UI build trust and does
not assert that an imported workflow is ready to run.
