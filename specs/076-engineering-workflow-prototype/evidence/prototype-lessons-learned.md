# Engineering Workflow Prototype — Lessons Learned

**Status**: Frozen reference evidence as of 2026-08-26

**Branch**: `076-engineering-workflow-prototype`
**Started**: 2026-08-25

## Purpose

This record preserves discoveries from hands-on prototype review so a formal
implementation is driven by observed failures and user expectations rather
than by the prototype code. Prototype code remains disposable. These findings,
their evidence, and their resulting design constraints are durable inputs to
CP7 and any later production specification.

Each lesson records:

- the observed problem and why it matters;
- the underlying design or implementation cause;
- a candidate design rule;
- the required user experience and corrective messaging;
- an implementation consequence; and
- a regression or evaluation case.

A lesson is a **candidate rule** until human review accepts it. CP7 may accept,
revise, supersede, or reject it, but must not silently omit it.

## Instructions for future agents on this branch

Treat this file as durable evidence and the prototype source as disposable.
Before extending a behavior, state the ambiguity, hypothesis, smallest
experiment, exclusions, and observable success or failure condition. After
testing, record what happened even when it contradicts the intended design.
Never convert a fixture-specific workaround into generic behavior, and never
describe a provisional schema, executor, or UI choice as production architecture.
Leave the next agent a concrete remaining question and a keep, revise, or
discard recommendation. The operating protocol is also recorded in
`../plan.md` under **Discovery Operating Mode**.

## LL-001 — A fixture must never masquerade as analysis of user data

**Observation**: An arbitrary user-uploaded image was followed by a specific
`OUTCOME_EVIDENCE_INSUFFICIENT` finding about missing mounting spacing. The
image was never inspected. The finding and its evidence were predetermined by
the diagnostic fixture.

**Why it matters**: The UI made a false causal claim, damaged trust, and made a
test-specific outcome appear to be generic workflow reasoning.

**Candidate design rule**:

1. User-supplied runtime data must never be paired with a predetermined
   semantic result.
2. Fixture mode must use controlled fixture inputs and display a persistent
   `Predetermined fixture` indicator.
3. Live mode may display only findings produced by the current run.
4. If an executor is unavailable, execution stops with `Executor not
connected`; it never fabricates completion.

**Required UX**: Display the active run mode, the source of every result, and
whether an output is fixture-generated or produced from current inputs.

**Implementation consequence**: Separate `FixtureExecutor` and `LiveExecutor`
behind one generic execution contract. UI components render `RunRecord` data;
they do not read semantic findings directly from a scenario definition.

**Regression case**: Upload an arbitrary image in live or unconnected mode and
verify that no fixture-specific diagnostic can appear.

## LL-002 — Validation is layered, and each layer stops at a different point

**Observation**: Missing attachments, missing semantic information, malformed
tool arguments, tool failures, and unacceptable outcomes were initially
presented as one generic workflow failure.

**Why it matters**: Users cannot correct a problem when the UI does not say
which boundary detected it or which downstream work did not run.

**Candidate design rule**:

| Layer                | Question                                                                                                          | Owner                             | Stop behavior                                   |
| -------------------- | ----------------------------------------------------------------------------------------------------------------- | --------------------------------- | ----------------------------------------------- |
| Definition           | Is the workflow structurally and syntactically valid?                                                             | Compiler/validator                | No run starts                                   |
| Preflight            | Are required runtime values, files, bindings, permissions, and executors present?                                 | Runtime                           | Stop at first unavailable execution frontier    |
| Semantic preparation | Can the AI resolve the request and produce the required output or tool arguments without unsupported assumptions? | AI task plus structured validator | AI task returns `needs-input`; MCP does not run |
| Tool-call validation | Do generated arguments satisfy the exact selected MCP tool schema and approval requirements?                      | Generic MCP adapter               | Tool is not called                              |
| Execution            | Did the selected executor complete and return a valid transport result?                                           | AI/MCP executor                   | Dependents are blocked                          |
| Outcome evaluation   | Does the produced artifact satisfy explicit acceptance criteria?                                                  | Evaluator/oracle                  | Feedback follows evidence to relevant blocks    |

**Required UX**: Use distinct language such as `Definition invalid`,
`Preflight stopped`, `Needs input`, `Tool call rejected`, `Execution failed`,
and `Outcome unacceptable`. Show `Blocked by <block>` on downstream steps.

**Implementation consequence**: Model these states explicitly instead of
using one overloaded `failed` flag.

**Regression case**: Exercise one failure at every layer and verify that the
message, selected block, blocked dependents, and recovery action are different.

## LL-003 — A block is a cause only when current-run evidence identifies it

**Observation**: The diagnostic runner automatically marked the first block
`Possible cause` after any predetermined outcome failure.

**Why it matters**: Position in a graph is not evidence of causality. The
workflow may have obtained the missing information from an image, a document,
a lookup, another branch, or the tool itself.

**Candidate design rule**: A diagnostic may highlight a block only when a
current-run finding contains that stable block identity and traceable evidence.
Absence of evidence must be rendered as uncertainty, not as a cause.

**Required UX**: Each finding shows detection point, related blocks, expected
and actual values, evidence sources, confidence or uncertainty, and suggested
recovery actions. `Why is this highlighted?` must always have an inspectable
answer.

**Implementation consequence**: Findings carry `relatedBlockIds`, evidence
references, and provenance. Canvas overlays are projections of findings, not
hard-coded block positions.

**Regression case**: Produce an outcome failure with no related block evidence
and verify that no upstream block is marked as a cause.

## LL-004 — Prompt / Request is one generic multimodal primitive

**Observation**: Separate image and text blocks were understandable in a
specific design story but cumbersome for common requests. Research review,
design requests, supplier comparisons, and failure analysis share the same
core runtime inputs.

**Candidate design rule**: Offer one engineer-readable `Prompt / Request`
input that accepts text, images, readable files, parameters, and references to
existing artifacts. Preserve typed artifacts internally rather than flattening
them into one opaque prompt string.

**Required UX**:

- one discoverable `Add attachments` action for supported images and files;
- previews, names, media types, roles, upload/readability state, and removal;
- configurable requirements such as prompt required, minimum images, or
  minimum documents;
- workflow-specific display aliases such as `Design Request` or `Research
Review Request` without new runtime classes; and
- clear session-only or persisted status.

**Implementation consequence**: The canonical output is a typed
`PromptRequest` package containing instructions, artifact references,
parameters, and requirement evidence.

**Regression case**: Use the same primitive for a photograph-based design
request and a multi-paper research review without adding domain-specific code.

## LL-005 — Semantic sufficiency belongs at the consuming AI task

**Observation**: The input block was treated as if it could determine whether
mounting dimensions were present or required.

**Why it matters**: Input presence is deterministic; semantic sufficiency
depends on the requested output, actual attachment contents, target tool
contract, and allowed assumptions.

**Candidate design rule**: The input block validates presence, type, and
readability only. The consuming AI task evaluates semantic sufficiency against
its output contract or exact bound tool schema and returns one of
`completed`, `needs-input`, or `failed`.

**Required UX**: When the AI needs information, select the AI block and show
the unresolved value, why it is needed, sources examined, assumptions declined
or proposed, and a question or upstream correction action.

**Implementation consequence**: AI outputs are structured and schema-checked.
A `needs-input` result contains unresolved inputs, evidence, questions, and no
executable MCP call.

**Regression case**: Supply a dimension in an image and verify that a capable
live evaluator cites the image rather than reporting it missing. If it cannot
resolve the dimension, verify that the AI block—not the input block—stops.

## LL-006 — An AI cannot prepare an MCP call without the exact tool contract

**Observation**: A generic `Create Candidate Output` block appeared before a
generic `Run Selected MCP Tool` block without exposing how the AI knew which
output to create.

**Candidate design rule**: Before an AI prepares MCP arguments, the workflow
must resolve an exact server/tool binding and make its reviewed input schema,
output schema when available, declaration identity, and approval metadata
available to that AI task. A friendly capability category never selects
runtime code.

**Required UX**: Show the friendly task name and exact target tool separately.
If no exact tool is bound, show `Choose target MCP tool` and stop before the AI
call. Allow inspection of the schema used to validate the generated arguments.

**Implementation consequence**: Keep one generic MCP adapter. Tool binding is
configuration data, not a CAD/FEA/CAM/CFD service taxonomy.

**Regression case**: Bind materially different fixture tools and verify that
the same AI/MCP block contracts validate each schema without tool-name or
domain dispatch branches.

## LL-007 — Every executable block needs observable inputs and outputs

**Observation**: The simulated AI and MCP blocks were marked complete without
a way to inspect what they received or produced.

**Candidate design rule**: A successful state is not credible without a
reviewable output and provenance. Every executable block exposes Inputs,
Output, Activity, and Diagnosis. Connections expose the typed payload or
artifact references crossing them.

**Required UX**:

- readable summary plus exact structured output;
- executor/model/tool identity and run mode;
- assumptions, unresolved inputs, citations, and artifact links;
- timestamps, duration, and current-run correlation identity;
- redaction and truncation indicators; and
- comparison between retained reruns rather than overwriting prior evidence.

**Implementation consequence**: Persist immutable step results in a run record
and derive visual state from those results.

**Regression case**: For every completed executable block, verify that the UI
can open a non-empty output or an explicit valid empty-result record.

## LL-008 — Deterministic and live execution are both required and must be obvious

**Observation**: Deterministic fixtures are necessary for fast tests, but a
fixture badge was not sufficient to prevent users from interpreting simulated
results as analysis of their data.

**Candidate design rule**: Support explicit `Validate only`, `Fixture`, and
`Live` modes. Automated unit/component/contract tests use deterministic
adapters. Human integration testing may use configured live AI and MCP
adapters. A run record always identifies its mode.

**Required UX**: A persistent toolbar indicator explains the mode before Run.
Fixture mode names its controlled dataset. Live mode names the configured
provider and governed tool boundary. Unavailable live dependencies stop with a
repair action.

**Implementation consequence**: Selection of execution mode is explicit run
configuration, never inferred from the presence of a fixture object.

**Regression case**: Verify that fixture and live results cannot be confused
in the toolbar, step output, history, export, or diagnostic report.

## LL-009 — Recovery guidance is part of the execution contract

**Observation**: A red failure and generic feedback arrow did not tell the user
whether to change a prompt, add an image, answer a question, select another
tool, modify tool arguments, or revise acceptance criteria.

**Candidate design rule**: Every non-success result provides bounded recovery
actions appropriate to its detection layer. Suggested actions never mutate
upstream inputs silently.

**Required UX**: Show the problem in plain language, technical details on
demand, what ran and did not run, evidence, and one or more explicit actions
such as `Add attachment`, `Answer question`, `Edit prompt`, `Choose tool`,
`Review generated arguments`, or `Revise criteria`. Preview changes before a
rerun and retain the earlier attempt.

**Implementation consequence**: `StepResult` and `DiagnosticFinding` include
machine-readable recovery actions with target block identities and required
approval semantics.

**Regression case**: Each modeled failure layer must offer at least one valid
recovery path or explicitly state why human intervention outside Wright is
required.

## LL-010 — The canonical program and UI must remain one representation

**Observation**: A visual-only fixture could display execution states that no
interpreter had produced.

**Candidate design rule**: The canvas and text/code view project the same
versioned canonical workflow. Definition validation, preflight, execution, and
diagnosis consume that model and produce separate immutable run records. View
state may never invent execution state.

**Required UX**: Users and LLMs can inspect the same stable block identities,
ports, requirements, bindings, and result references. Validation errors link
to both the textual location and visual block.

**Implementation consequence**: Keep layout/presentation metadata separate
from executable contracts while preserving stable identities between views.

**Regression case**: Round-trip text to model to canvas without semantic
changes, then verify that only a run record—not fixture presentation data—can
mark a block completed or failed.

## LL-011 — Fast tests should prove contracts, not reproduce manual clicking

**Observation**: The existing Rivet feedback loop and broad Playwright usage
were slow and fragile. The prototype also showed that deterministic component
tests could catch route, state, and stop/continue behavior quickly. During
CP3E, eight focused code/diagram tests completed in about five seconds. The
72-test prototype batch exhausted its five-second per-test budget in several
unrelated UI-heavy tests under parallel load, while every affected file passed
when isolated. A four-worker rerun reduced the failures to one unrelated axe
timeout, which also passed in isolation.

**Candidate design rule**: Pure validators, reducers, compilers, and execution
contracts receive most coverage. Component tests verify focused user-visible
state transitions. Browser automation is reserved for a few cross-boundary
journeys and visual/accessibility evidence.

**Required UX evidence**: Human checkpoint scripts remain necessary because a
passing test did not reveal that the hard-coded diagnostic was misleading.

**Implementation consequence**: Every lesson that changes a contract adds a
T0/T1 regression before a browser journey is considered. Keep the focused
contract suite as the edit loop; bound suite concurrency based on measured host
capacity, and do not mask resource contention by broadly increasing every test
timeout.

**Regression case**: Maintain the plan's T0/T1/T2 timing budgets and record
environment failures separately from product failures.

## LL-012 — Preflight requirements must be explicit, visible, and traceable

**Observation**: The diagnostic fixture silently configured `minImages: 1`
because the sample prompt mentioned supplied photographs. The user had not
authored or accepted that requirement, and the canvas did not make its source
clear before Run.

**Why it matters**: Free-form prompt text is not a machine-readable workflow
contract. Turning an example-specific phrase into a hidden preflight rule
causes Step 1 to reject otherwise valid generic requests and repeats the same
test-specific leakage as the predetermined mounting-spacing result.

**Candidate design rule**:

1. Preflight enforces only requirements explicitly stored in the canonical
   workflow or supplied by an exact downstream contract such as a bound tool
   schema.
2. Every requirement records provenance such as `workflow-author`,
   `tool-schema`, `organization-policy`, or `user-accepted-ai-proposal`.
3. Requirements inferred from free-form text are semantic findings or
   suggestions in the consuming AI task; they are not silently promoted to
   preflight rules.
4. A generic Prompt / Request defaults attachments to optional unless the
   workflow author explicitly changes that contract.

**Required UX**: Show required inputs and their source on the block before Run
and in Details. For example, `1 image required · workflow author` is different
from `Prompt mentions photographs · AI needs clarification`. Allow an author
to inspect and edit workflow-authored requirements. Never make users reverse
engineer a requirement from an error.

**Implementation consequence**: Input requirements are typed canonical data
with stable identities and provenance. Semantic AI results may propose a new
requirement, but accepting that proposal is a separate reviewed authoring
change.

**Regression case**: Run a prompt mentioning photographs with no image and no
explicit image requirement. Step 1 must complete; Step 2 may return
`needs-input` after interpreting the actual request. Add an explicit image
requirement and verify that Step 1 stops while showing its source before Run.

## LL-013 — Compound requests need typed views, not forced flattening or block proliferation

**Observation**: One Prompt / Request is easiest to author, but downstream
consumers do not all accept the same modalities. A text-only model must not be
given an opaque image bundle, while an image-processing branch should not need
a second copy of the user's request.

**Candidate design rule**: Preserve one canonical multimodal request and expose
typed views from it: complete request, instructions, images, and documents. A
connection selects one compatible view. Specialized Text, Image, or Document
input blocks remain optional convenience aliases, not separate runtime types.

**Required UX**: Default to `Complete request`; show the available typed ports,
the selected connection payload, attachment counts, and target compatibility.
Warn when a text-only route intentionally leaves attachments unused. Stop
before execution when the selected output is empty, unreadable, or rejected by
the target block.

**Implementation consequence**: Ports and connections carry stable identities
and data types. The validator checks source/target compatibility independently
of React Flow. Canvas handles are a projection of canonical ports rather than
the source of routing truth.

**Regression case**: Verify complete-request, text-only, image-only, and
document-only routes. A text-only consumer accepts instructions, warns about
unused attachments, and rejects image/document ports without executing.

## LL-014 — Model choice is run configuration; tool isolation is a separate contract

**Observation**: The first live implementation tried to set a selected model
through `POST /api/sessions/{id}/model`. The running Hermes gateway returned
404 even though the new session appeared in its session catalog. The installed
Hermes completion contract instead accepts `provider`, `model`,
`require_model_lock`, and `model_options.reasoning` on the execution request.
After moving to that contract, a live low-thinking request returned `LIVE_OK`
and the temporary session was deleted.

A second discovery was equally important: preventing Wright from activating
workspace MCP servers does not prove that every Hermes runtime toolset is
disabled. Hermes 0.20 accepts OpenAI-shaped `tools` and `tool_choice` fields but
its agent construction still derives enabled toolsets from platform
configuration. The prototype observed no tool call, but must not describe that
as a hard sandbox.

**Candidate design rule**:

1. Provider, model, thinking level, service tier, and similar controls are
   immutable per-run execution configuration.
2. A workflow run must not mutate the user's global/default model merely to
   execute one block.
3. Unsupported model or thinking selections fail explicitly; the runtime never
   silently substitutes another selection.
4. `Do not activate Wright MCP`, `no external tools`, and `no tools of any kind`
   are distinct enforceable policies with distinct evidence.
5. A production `no-tools` policy requires a backend acknowledgement or a
   dedicated executor that cannot load tools. Prompt instructions and absence
   of observed tool events are not sufficient proof.

**Required UX**: Put model and thinking selectors on the AI block. Show the
actual provider/model/thinking values with its output. State the verified tool
boundary precisely and expose any tool event as a policy violation.

**Implementation consequence**: Carry model selection through the generic
execution request and run record. Keep MCP activation policy separate from
model configuration. Add an executor capability such as
`supportsHardToolIsolation` before production can offer a hard `No tools`
option.

**Regression case**: Select two different configured models without changing
the global model, verify the requested provider/model/reasoning payload, and
verify Wright skips MCP sync/activation for the isolated AI block. Separately
verify that a claimed hard no-tools executor rejects or cannot perform a tool
call.

## LL-015 — A long-running step must expose activity, elapsed time, and cancellation

**Observation**: A live AI step appeared stuck for several minutes. The UI
showed only `Running selected AI`. A clean rerun proved that Wright had
registered a backend stream but received no model output. The long-lived API
had retained an older `localhost` gateway URL while Hermes listened only on
IPv4 `127.0.0.1`. Direct IPv4 model execution was healthy; restarting the API
to reload the current endpoint restored the complete Wright stream.

**Why it matters**: A user cannot distinguish model reasoning, attachment
upload, connection delay, stream failure, cleanup delay, or stale UI state.
An inactivity timeout does not provide a total execution deadline when a
provider continues to send stream data.

**Candidate design rule**:

1. Every executable step emits a durable, ordered activity stream with a run
   ID, step ID, timestamps, and executor identity.
2. The UI shows elapsed time and the current lifecycle stage, such as upload,
   queued, generating, validating, or cleanup.
3. Partial output may be previewed as uncommitted stream data; only a completed
   result becomes a downstream artifact.
4. Every long-running step has an explicit cancel action and a separately
   configured total deadline.
5. Browser reconnect or stale-state recovery reconciles against the backend
   run record instead of remaining indefinitely in `running`.

**Required UX**: Show elapsed time, last activity time, streamed preview,
Cancel, total deadline, and a collapsible event log. After interruption, state
whether partial output was discarded or retained for diagnosis.

**Implementation consequence**: Move transient session logging into immutable
workflow run/step events. Record connection, first-event, and first-output
boundaries. Session cleanup must have its own bounded timeout and must not
delay publication of an already completed or failed step result.

**Regression case**: Simulate a gateway connection failure, a silent provider,
a provider sending heartbeats, a cleanup hang, browser reconnect, and user
cancellation. Verify that each produces a distinct visible state and bounded
completion.

**CP3F discovery increment — 2026-08-26**: The diagram now receives generic
LLM lifecycle events and shows a fixed run monitor with the active block,
elapsed time, all four block states, current activity, and partial text. Partial
text is labeled `Uncommitted output preview` and becomes a committed output
only after the adapter completes. This tests whether immediate visibility
improves comprehension; it does not satisfy the production rule above because
events remain page-local, cancellation and total deadlines are absent, and a
browser reconnect cannot recover the run. Hands-on review immediately exposed
the consequence: gateway connection, provider waiting, and token generation
were collapsed into one zero-output `running` state. A production UI must not
claim more than the backend has established, must expose a durable run
identity, and must reconcile missing jobs into an explicit stale or
interrupted state.

## LL-016 — MCP discovery and executable tool binding are two separate choices

**Observation**: Wright exposes nine installed MCP servers in the current
catalog, while those servers expose many individual tools with different input
schemas. A single flat engineering-category list cannot identify an executable
target. The generic diagnostic context also did not justify silently choosing
one CAD or analysis server.

**Candidate design rule**:

1. First select an installed MCP server; then select one exact catalog tool
   from that server.
2. Show all installed servers, including inactive or unavailable entries, with
   explicit status instead of silently hiding them.
3. A contextual default may be applied only when the canonical block context
   explicitly identifies a unique server or exact tool, or when workspace
   policy identifies exactly one eligible default for the requested category.
   Broad semantic similarity may rank suggestions but never silently choose
   among multiple runtime candidates.
4. Friendly domains such as CAD, FEA, CAM, CFD, PLM, and kinematics remain
   discovery metadata, not executable dispatch categories.
5. Selection is not execution. The exact identity and declared schema must be
   reviewed and mapped before a governed invocation is enabled.

**Required UX**: Provide an immediately accessible `Installed MCP` picker when
the block is created or selected, followed by an `Exact tool` picker. Do not
require scrolling through a general properties panel for the primary binding
action. Show active/inactive and enabled/disabled state, exact tool ID,
description, required inputs, and the declared schema. Explain `No safe
default` when context is ambiguous, and label whether a value came from the
user, an agent proposal, a fixture, or workspace policy.

**Implementation consequence**: Bind stable `serverId` and `toolId` catalog
identities as workflow configuration. Context suggestions return reviewed
binding proposals; they do not introduce vendor or tool-name branches in the
generic runtime.

**Regression case**: List active and inactive installed servers, filter tools
by selected server, bind an exact tool without executing it, and verify that
generic engineering language produces no automatic default. Separately verify
that an explicit server/tool name produces a reviewable suggestion.

**Explicit fixture-default refinement — 2026-08-26**: The diagnostic example
now declares `BREP MCP` and `brep.model.apply_history` as its fixture-authored
starting binding. Wright resolves those exact, unique names to installed
catalog IDs rather than embedding this machine's UUID or branching on a CAD
category. The UI labels the source `Fixture starting value` and remains
manually selectable. If either identity is missing or ambiguous, the UI reports
the unavailable fixture default and does not substitute another server or tool.

**Inline-binding refinement — 2026-08-26**: Selecting the MCP block, or reaching
it as the active execution frontier, now exposes server and exact-tool
dropdowns directly above the canvas. The controls share the same state as the
detailed inspector, so the quick interaction and schema review cannot diverge.
This is a provisional placement experiment; a mature large catalog likely
needs a searchable combobox with recommended, workspace, and all-installed
sections rather than an ungrouped native dropdown.

## LL-017 — Code and diagram should project one semantic workflow model

**Observation**: Users and LLMs need a precise representation they can create,
review, validate, diff, and test without reproducing a long sequence of canvas
interactions. Engineers also need the diagram to remain the approachable view
of that same workflow. Maintaining separate text and canvas definitions would
allow them to disagree.

**Candidate design rule**:

1. Text and diagram are two projections of one canonical semantic model.
2. Block, phase, port, and connection identities are explicit and stable.
3. Syntax/schema errors and semantic-reference errors are reported before a
   changed definition can execute.
4. An invalid edit preserves the last valid diagram and states that it is stale.
5. Applying a valid text edit is explicit in the discovery UI so users can
   distinguish validation from mutation.
6. Visual layout is either a deterministic projection or separately modeled;
   it must not become hidden executable semantics.

**Required UX**: Provide a clear `Diagram / Code` switch, structured errors
with paths and codes, an `Apply to diagram` boundary, and an unambiguous
`valid but not applied` state. The workflow Run action remains disabled until
the displayed definition is valid and applied.

**Implementation consequence**: The CP3E experiment uses strict JSON and a
small schema solely to test round-trip semantics. It intentionally excludes
layout from source and temporarily requires the four fixture block identities
because the existing runner is fixture-bound. Neither choice is a production
decision. A later specification must compare JSON, YAML, or a purpose-built DSL
and must decouple execution from fixture identities.

**Regression case**: Edit a workflow title, block title, and connection in
text; apply it and verify the diagram changes. Then introduce malformed JSON
and an unknown block/port reference; verify structured errors, disabled Run,
and preservation of the last valid diagram.

## LL-018 — `Running` must identify the boundary that is actually alive

**Observation**: A clean live rerun registered a Wright chat stream but
produced no model tokens. The long-lived Wright API had cached a former
`localhost` gateway URL while the current Hermes gateway listened on IPv4
`127.0.0.1`. Direct IPv4 model execution was healthy, and restarting Wright's
API to reload the current endpoint restored the full stream. A separate
sandboxed restart then failed during installed-CLI discovery, before the API
could bind its port.

**Candidate design rule**:

1. Do not collapse API registration, gateway connection, provider execution,
   token generation, and cleanup into one generic `running` state.
2. Persist an opaque run identity and timestamps for registered, connected,
   first executor event, first output, and terminal outcome.
3. Bound gateway connection, first event, first output, total execution, and
   cleanup separately. A heartbeat proves only the boundary that emitted it.
4. Resolve and record the effective executor endpoint without credentials.
   Detect configuration changes or state explicitly that a service restart is
   required.
5. Distinguish transport failure, unavailable executor, authentication failure,
   provider silence, user cancellation, and sandbox/permission denial in both
   run records and recovery guidance.

**Required UX**: Show a concise current phase such as `Starting Wright run`,
`Connecting to AI gateway`, `Waiting for model`, or `Receiving output`, plus
elapsed time and a cancellable run identity. On failure, identify the boundary
and give a concrete retry/reconfigure/restart action rather than leaving a
spinner or reporting `unknown error`.

**Implementation consequence**: Executor adapters need structured lifecycle
events and typed terminal errors, not only token/tool/error output. Endpoint
configuration must not be treated as immutable merely because the hosting
process is long-lived. Development launchers also need a supported permission
profile for installed local executors.

**Regression case**: Prove that a direct model request, a Wright-to-gateway
request, and a complete UI run can be diagnosed independently. Include stale
configuration, IPv4/IPv6 loopback mismatch, sandbox-denied startup, silent
provider, cancellation, and successful token streaming.

## LL-019 — Bind the consuming tool contract before generating its arguments

**Observation**: Preselecting BREP MCP alone moved the user to another vague
stop: `Select exact MCP tool`. Selecting `brep.model.apply_history` then exposed
the deeper incompatibility. The operation requires a `history` object, while
the preceding AI step was explicitly prompted to return prose. Both steps can
be individually healthy while the workflow remains impossible to execute.

**Evidence**: The required field comes from the installed tool's declared input
schema. The prototype does not infer a missing engineering fact or hard-code a
BREP-specific failure. It reports the generic producer/consumer type mismatch
and does not attempt the MCP call.

**Candidate design rule**:

1. Resolve or review the consuming MCP server, exact tool, and schema before
   configuring an upstream AI task that is expected to produce its arguments.
2. Treat server selection, exact-tool selection, argument generation, argument
   mapping, schema validation, approval, and invocation as distinct states.
3. A selected tool is not `ready` when any required schema field is unmapped.
4. Derive missing-input messages from the current catalog schema and canonical
   connection types; never introduce test-specific findings.
5. An agent may propose the server, tool, and mapping from context, but each
   proposal retains provenance and remains reviewable before invocation.

**Required UX**: At the active MCP frontier, show the server and operation
pickers without requiring inspector navigation. Once selected, name each
unmapped required field, identify the incompatible upstream output, state that
no call was attempted, and offer concrete corrections: change the producer's
output contract or insert a mapping step.

**Implementation consequence**: A production workflow compiler needs typed
ports plus schema-aware argument mappings. AI prompt construction should accept
the reviewed consumer schema or a derived output contract. The generic runtime
must not contain branches for `BREP`, `history`, CAD, or any other example;
those names remain fixture/catalog data.

**Regression case**: Bind a tool with one required object field to an upstream
text output and verify a pre-invocation mapping diagnostic. Repeat with a
no-required-input tool and a nested multi-input tool. Confirm that changing the
fixture/catalog changes the message without changing runtime code.

## LL-020 — Execution is UI-independent, but application-backed MCP identity is not

**Observation**: The four semantic blocks ran successfully without React or a
graph library once the AI received the selected tool contract. The first BREP
attempt nevertheless alternated between an empty model and the applied
five-feature model because two control pages were polling one command queue.
Each page owned a different in-memory CAD state.

**Evidence**: `apply_history` returned five features. The first inspection
returned zero; later inspections returned five. After restarting the BREP
runtime with exactly one headless control surface, the repeatable live runner
completed in 22.663 seconds and three consecutive inspections returned the
same five ordered IDs and run metadata.

**Candidate design rule**:

1. Workflow execution, validation, and evidence must not depend on the diagram
   being mounted.
2. The UI and an agent/CLI are peers projecting one canonical definition and
   durable run record.
3. Application-backed MCP calls require an authoritative application/surface
   identity or exclusive lease; `connected: true` is not sufficient.
4. A run must reject inconsistent observations instead of retrying until one
   matches the desired result.
5. Browser-local attachments require stable artifact identities before a
   headless runner can consume them.
6. Evaluation criteria are explicit workflow data. Successful mutation and
   inspectability prove orchestration only, not engineering correctness.

**Required UX**: A headless run should appear in the same block activity and
evidence views as a UI-started run. When an MCP application identity is missing
or contested, identify that boundary and stop before claiming an outcome.

**Implementation consequence**: Keep the semantic runner outside React and the
canvas adapter. Persist typed step events and evidence. Extend application-MCP
contracts with client/surface identity, liveness, and exclusivity or immutable
candidate semantics; do not solve this with a BREP branch in the workflow
runtime.

**Regression case**: Run the same four-block definition through UI and CLI and
compare run records. Mount two application clients and prove the second is
rejected or isolated. Kill the authoritative client and verify typed liveness
failure rather than a sticky connected state or command timeout.

## LL-021 — AI should produce semantic artifacts, not application-internal payloads

**Observation**: The AI returned valid JSON for the BREP experiment, but placed
feature identity in a shape that the hand-written `PartHistory` validator
rejected. The selected MCP schema exposed `history` only as an object, which was
too weak to teach or verify the application's internal representation.

**Candidate design rule**:

1. An AI block returns a small, versioned, tool-independent semantic artifact
   whenever one can express the engineering intent.
2. A deterministic adapter validates that artifact and compiles exact MCP
   arguments after an exact server and operation are selected.
3. The generic runtime knows only typed ports, schemas, bindings, and adapters;
   it never branches on BREP, CAD, FEA, or another example category.
4. Raw AI output, parsed semantic output, compiled arguments, tool result, and
   evidence remain distinct inspectable records.
5. An adapter failure stops at the mapping boundary and identifies the
   incompatible producer field and consumer field.

**Required UX**: Show the semantic result as the normal AI block output. Show
compiled tool arguments as a reviewable technical layer on the MCP block, not
as if the user authored or validated application internals.

**Regression case**: Give two different exact MCP operations deterministic
adapters for the same semantic artifact. Confirm that the AI output is
unchanged, each operation receives its own valid arguments, and an adapter
error prevents invocation with a field-level diagnostic.

## LL-022 — Primary actions describe the action, not the fixture or status

**Observation**: Toolbar labels such as `Retry four-block workflow`, `Run
selected AI`, `Map MCP input: history`, and `Demo complete` leaked test
topology, implementation state, and diagnostics into the primary action. The
block count does not help an engineer decide what clicking the button does.

**Candidate design rule**:

1. The primary workflow actions are `Run`, `Running…`, `Retry`, and `Cancel`.
2. Step counts and the active block belong in progress, not in the action label.
3. Success and failure belong in status banners and run records, not in a
   disabled action-shaped status control.
4. Wright's current configured model is the default. Model and thinking
   controls are optional overrides, not startup requirements.
5. Missing configuration identifies the affected block and offers a direct
   fix next to that block; it does not rewrite the global action into an error
   sentence.

**Regression case**: Vary the fixture from two to fifty blocks, use the current
model and a deliberate override, and force input, mapping, and tool failures.
The action vocabulary remains stable while progress and diagnostics contain
the changing detail.

## LL-023 — Engineer-facing results need progressive disclosure

**Observation**: The first per-block result view rendered large headings, raw
ISO timestamps, a long error, output JSON, and evidence JSON in one continuous
column. It preserved data but made the result harder to understand and pushed
the corrective action below developer-oriented details.

**Candidate design rule**:

1. Lead with state, elapsed time, consequence, and the next useful action.
2. Summarize small scalar engineering results as labeled values and show
   readable text as bounded prose.
3. Keep exact produced data, IDs, timestamps, provider metadata, schemas, and
   evidence available under explicit technical disclosures.
4. Failed results preserve partial output and evidence without presenting them
   as accepted artifacts.
5. Runtime errors should evolve from strings to typed diagnostics with code,
   summary, cause, affected port or field, remedy, and technical details.

**Required UX**: An engineer can answer “did it run, what happened, what did it
produce, and what should I change?” without reading JSON. A developer can still
reach the exact payload in one additional action.

**Regression case**: Render not-run, running, completed text, completed
structured output, failed-without-output, and failed-with-partial-output states
at the narrow inspector width. Verify no raw payload appears until expanded and
that the exact evidence remains accessible.

## LL-024 — A successful run must deliver actionable outputs

**Observation**: The first correct four-block run turned green and exposed a
valid terminal object, but the user still could not answer what was produced or
open the live BREP model. Execution success and output delivery are separate
product requirements.

**Candidate design rule**:

1. Any block can produce zero or more serializable output references; the final
   run summary aggregates the outputs that matter to the user.
2. An output reference declares identity, title, kind, format, description,
   durability, producer provenance, and currently available actions.
3. Actions use a small generic vocabulary such as view, open, download, and
   open-in-application. The producing runtime resolves the action; the workflow
   UI does not branch on CAD, documents, Onshape, Solid Edge, or another product.
4. Live application-backed outputs outlive step execution long enough for user
   inspection. A runtime may not destroy the only viewable result in its normal
   `finally` cleanup.
5. Session and ephemeral outputs are labeled and released deliberately. Durable
   files use stable artifact identities and remain available from run history.
6. The UI never advertises an export or application action that the producing
   tool did not actually provide.

**Required UX**: Completion announces how many outputs are ready and shows
recognizable cards with direct actions. A document can expose View and Download;
a web model can expose View or Open link; a native CAD result can expose Open in
application when a host adapter can resolve it. Raw payloads remain technical
details, not substitutes for delivered artifacts.

**Regression case**: Complete runs producing no artifact, one document, one
session model, multiple durable files, an expired artifact, and an unavailable
native application action. Verify accurate counts, provenance, lifetime text,
safe action dispatch, and deliberate resource release.

## LL-025 — Ports, connections, artifacts, and components are separate concepts

**Observation**: Artifact-placement concepts repeatedly overloaded one tiny
glyph with four meanings: the static input/output contract, the graph
connection, the runtime value, and the action for inspecting that value. A
second artifact rail improved access but looked like a duplicate workflow.
Industry review also showed that visually collapsing nodes and publishing a
reusable component are separate operations.

**Candidate design rule**:

1. A port defines a stable, typed, directed contract with requiredness and
   cardinality; a connection binds compatible ports; a run produces value or
   artifact references independently of both.
2. Default blocks place readable inputs on the left and outputs on the right.
   The connection target and artifact inspection target may be adjacent but
   must have distinct behaviors and accessible names.
3. Data/artifact flow is visually distinguishable from execution, decision,
   approval, and feedback control flow.
4. A primitive operation, local collapsed graph, reusable component, and
   external MCP-backed action use the same external port semantics.
5. Local collapse is organizational. Reuse requires an explicit, versioned
   public interface with compatibility review.
6. Lollipop/socket notation is reserved for provided/required capability
   interfaces unless usability evidence shows that engineers understand it for
   another purpose.

**Required UX**: At normal zoom, users can connect a port, read its short name,
identify required/optional and collection state, determine whether the current
run produced a value, and open that value without expanding every block. A
composite opens its internal graph with breadcrumbs; a boundary failure links
to the failing internal step.

**Implementation consequence**: The canonical model must not encode runtime
artifact state in port or canvas objects. Composite definitions publish stable
port identities and versions; instances bind those interfaces. Renderers
project contracts, bindings, and run references together without making the
graph library authoritative.

**Regression case**: Render the same required, optional, collection, missing,
pending, produced, failed, and stale ports on a primitive and a composite.
Verify producer-to-consumer traceability, distinct connect/open interactions,
keyboard access, component drill-down, and an internal failure surfaced at the
public boundary. See
[CP3O block-interface research](cp3o-block-interface-and-composition-research.md).

## Current prototype debt exposed by these lessons

| Priority | Current prototype behavior                                                                    | Required interim correction                                                                             |
| -------- | --------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------- |
| P0       | Arbitrary uploaded input can receive a predetermined mounting-specific finding                | Stop at the unconnected AI task or use controlled fixture input with an unmistakable fixture-mode label |
| P0       | The diagnostic fixture silently makes one image a Step 1 requirement                          | Default attachments to optional; enforce only explicit, visible canonical requirements with provenance  |
| P0       | The reducer forces a failed outcome after preflight                                           | Replace forced transitions with executor-produced `StepResult` data                                     |
| P0       | The first block becomes `Possible cause` without evidence                                     | Derive overlays only from current-run related-block evidence                                            |
| P0       | Multiple MCP application surfaces can consume one command queue and return different models   | Require authoritative surface identity/exclusivity and reject inconsistent evidence                     |
| P1       | Image and document attachment actions are separated and easy to miss                          | Provide one attachment action and typed attachment list                                                 |
| P1       | AI and MCP blocks can appear completed without inspectable outputs                            | Add Inputs, Output, Activity, and Diagnosis views backed by run records                                 |
| P1       | Per-block output is presented as a raw developer dump                                         | Lead with an engineering summary and recovery; place exact payloads behind technical disclosure         |
| P1       | A passed run exposes data but no recognizable or actionable deliverable                       | Aggregate typed output references with view, open, download, and application actions                    |
| P1       | Tiny artifact glyphs overload connection, contract, runtime state, and inspection             | Test a hybrid typed port and keep each concept separate in the canonical model                          |
| P1       | Visual grouping has no explicit distinction from reusable composition                         | Separate local collapse from a versioned component with a published, compatibility-checked interface    |
| P1       | The selected MCP tool contract is not visible to the preceding AI task                        | Require and display an exact reviewed binding before AI argument generation                             |
| P1       | The AI is asked to construct an application-internal MCP object                               | Use a typed semantic result and deterministic exact-argument adapter where practical                    |
| P1       | The AI step produces prose before its consuming MCP schema is resolved                        | Make producer output contracts schema-aware and report unmapped fields before invocation                |
| P1       | Fixture, validate-only, unconnected, and future live states are not sufficiently distinct     | Make run mode and executor availability persistent and explicit                                         |
| P1       | A live AI call can remain `Running` without elapsed time, activity, total deadline, or cancel | Publish durable step events, streamed preview, cancel, and bounded lifecycle stages                     |

### P0 correction progress — 2026-08-25

- **Corrected in the interactive prototype**: attachments default to optional;
  the prompt-only request reaches Step 2.
- **Corrected in the interactive prototype**: the predetermined mounting
  finding and simulated AI/MCP completion claims were removed.
- **Corrected in the interactive prototype**: a selected configured AI runs,
  its provider/model/thinking values and text output remain inspectable, and
  execution stops honestly at the generic MCP binding or argument-mapping
  boundary.
- **Corrected in the interactive prototype**: the first block is no longer
  labeled `Possible cause` based only on its position.
- **Corrected in the interactive prototype**: Prompt / Request exposes typed
  request, text, image, and document outputs with pre-execution compatibility checks.
- **Corrected in the interactive prototype**: the MCP block lists installed
  servers with active/inactive status, scopes a second dropdown to exact tools,
  exposes the selected schema, and stops before invocation. Contextual defaults
  require explicit catalog identity; the generic example intentionally has none.

## Production implementation gates derived so far

A formal implementation must not begin execution integration until it can
demonstrate all of the following with generic fixtures:

1. the canonical workflow distinguishes definition data from run records;
2. required runtime values block dependents without calling AI or MCP;
3. AI tasks can return structured `needs-input` results;
4. exact MCP bindings and schemas are available before argument generation;
5. every completed executable step has inspectable output and provenance;
6. diagnostics highlight only blocks identified by current-run evidence;
7. fixture and live results are unmistakably different;
8. recovery actions target stable block identities and preserve prior runs;
9. no generic domain, runtime, or component branch dispatches on CAD, FEA,
   CAM, CFD, PLM, kinematics, supplier, or other example categories; and
10. focused model/component tests remain the default feedback loop;
11. long-running steps expose lifecycle activity, elapsed time, cancellation,
    and a total deadline; and
12. contextual MCP defaults require a unique, reviewable catalog identity and
    never bind from a broad engineering category alone; and
13. code and diagram round-trip through one validated semantic representation,
    while invalid edits cannot silently replace or execute the last valid model;
    and
14. run state distinguishes API registration, executor connection, first event,
    first output, and terminal outcome with bounded deadlines and typed errors;
    and
15. application-backed MCP execution binds an authoritative live surface or
    immutable candidate identity and rejects competing consumers; and
16. primary action labels remain stable across workflow topology and fixture
    changes; and
17. per-block result views provide human summaries and recovery before raw
    technical output; and
18. AI semantic output and deterministic MCP argument compilation are separate,
    inspectable records; and
19. successful runs expose actionable typed output references with explicit
    lifetime and producer provenance; and
20. ports, bindings, runtime artifacts, and component definitions remain
    separate while primitive and composite blocks expose one consistent public
    interface.

## Review log

| Date       | Review source                        | Finding                                                                                                         | Disposition                                                                                            |
| ---------- | ------------------------------------ | --------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------ |
| 2026-08-25 | Hands-on diagnostic workflow review  | Missing image must stop before AI                                                                               | Candidate rule recorded in LL-002                                                                      |
| 2026-08-25 | Hands-on Prompt / Request review     | Multimodal inputs should share one generic primitive                                                            | Candidate rule recorded in LL-004                                                                      |
| 2026-08-25 | Hands-on outcome diagnosis review    | Mounting-spacing failure was fixture data, not analysis                                                         | P0 correction and LL-001/LL-003 recorded                                                               |
| 2026-08-25 | Architecture discussion              | AI tool-call output depends on exact selected MCP schema                                                        | Candidate rule recorded in LL-006                                                                      |
| 2026-08-25 | Repeated hands-on run                | Hidden `minImages: 1` incorrectly stopped Step 1                                                                | P0 correction and LL-012 recorded                                                                      |
| 2026-08-25 | Corrective prototype increment       | Prompt-only and optional-image requests now stop honestly at the unconnected AI boundary                        | P0 interactive corrections implemented; production rules remain open for CP7                           |
| 2026-08-25 | Typed-routing increment              | One multimodal request must serve text-only and artifact-specific consumers without duplicating blocks          | Hybrid compound/typed port rule recorded in LL-013; four route cases covered by focused tests          |
| 2026-08-25 | Live LLM smoke test                  | Separate session-model route returned 404; per-request model lock succeeded and returned `LIVE_OK`              | Execution contract corrected and LL-014 recorded                                                       |
| 2026-08-25 | Installed Hermes source review       | Skipping Wright MCP activation is not a proven all-tools sandbox                                                | UI wording corrected; hard tool isolation remains a production gate in LL-014                          |
| 2026-08-25 | Live diagnostic wait review          | AI step lacked usable current-run timing, activity, cancellation, and persisted logs                            | Observability and bounded-lifecycle rule recorded in LL-015                                            |
| 2026-08-25 | Installed MCP selector increment     | Installed servers and executable tools require separate choices; generic context cannot choose safely           | Two-level exact binding rule recorded in LL-016; selection stops before invocation                     |
| 2026-08-26 | Code ↔ diagram discovery increment   | Humans and LLMs need a validated textual representation without a second workflow source of truth               | Provisional JSON experiment and LL-017 recorded; syntax, layout, and edit granularity remain open      |
| 2026-08-26 | In-flight run usability review       | A toolbar spinner did not reveal the executing block, activity stage, elapsed time, or emerging output          | CP3F fixed run monitor added; durable events, cancellation, deadlines, and reconnect remain open       |
| 2026-08-26 | CP3F initial live review             | UI remained running with zero output; the first late backend inspection found no active stream                  | Initial hot-refresh hypothesis was superseded by the clean rerun                                       |
| 2026-08-26 | CP3F clean live rerun                | Backend stream registered but a stale `localhost` gateway URL stalled before model output                       | Restarted API with current IPv4 endpoint; full Wright stream passed in 4.7s; LL-018 recorded           |
| 2026-08-26 | CP3F restart boundary check          | Sandboxed API launch could not inspect the installed Hermes CLI and never bound port 8000                       | Relaunched with normal host permissions; permission failure retained as a distinct regression case     |
| 2026-08-26 | Explicit MCP fixture-default review  | Diagnostic example should use BREP while preserving generic server and exact-tool selection                     | BREP and apply-history resolve by exact catalog names; installation UUIDs are not hard-coded           |
| 2026-08-26 | MCP binding-friction review          | Selecting a block and scrolling through properties makes primary MCP configuration unnecessarily slow           | Added synchronized canvas-level pickers that also appear automatically at the MCP frontier             |
| 2026-08-26 | MCP argument-readiness review        | A selected BREP operation still could not consume the preceding prose AI output                                 | Required `history` is now reported from schema; no call is attempted; LL-019 records the design rule   |
| 2026-08-26 | Headless four-block live run         | The chain passed without workflow UI; competing BREP control pages initially produced 0/5 feature views         | Repeatable runner and CP3G evidence added; LL-020 requires authoritative MCP application identity      |
| 2026-08-26 | Shared UI/headless runner correction | UI and headless paths had diverged; raw BREP history generation failed despite syntactically valid JSON         | One runner now feeds both projections; typed semantic fixture and deterministic compiler prove LL-021  |
| 2026-08-26 | Primary-action usability review      | “Retry four-block workflow” described the fixture rather than the user's action                                 | Runtime action reduced to `Run`, `Running…`, and `Retry`; general rule recorded in LL-022              |
| 2026-08-26 | Per-block result usability review    | Raw timestamps, errors, output JSON, and evidence dominated the narrow inspector                                | Human-first summary and recovery added; exact data retained in disclosures; LL-023 recorded            |
| 2026-08-26 | First successful UI run review       | The run passed, but the user could not identify or interact with the produced model                             | Output cards and generic action dispatch added; live BREP result retained for viewing; LL-024 recorded |
| 2026-08-26 | Block interface industry research    | Tiny ports lack artifact access, while separate rails duplicate the workflow; composites need stable boundaries | CP3O compares mature systems and records hybrid typed ports plus explicit composition in LL-025        |

## Open questions for production planning

The following questions remain intentionally unresolved and must be considered
by the clean `dev`-based program plan rather than answered by silently extending
this prototype:

- compare simple dots, square engineering terminals, and hybrid typed ports
  across required, optional, collection, missing, pending, produced, failed,
  and stale states, including reusable composition;
- independently reproduce the shared UI/headless execution result and compare
  every summarized and technical block result;
- test human- and LLM-authored code/diagram edits before choosing strict JSON,
  another syntax, or an Apply interaction; and
- evaluate installed-server and exact-tool selection with inactive servers and
  realistically large catalogs.

Continuing any of these experiments requires a new explicit authorization.
