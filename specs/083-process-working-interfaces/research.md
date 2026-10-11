# Research and resolved decisions

**Date:** 2026-09-30. Source inspection and three Spec Kit research subtasks;
no implementation, runtime tests, model calls or machine actions in this task.

## R1 — One served execution path, detached observers

**Decision:** Extend canonical source execution and its recorder/continuation,
not a second native run engine. Add a backend-owned source-run use case/supervisor
with durable start request receipts and separate snapshot/event attachment.

**Rationale:** `apps/api/src/api/routers/workspace.py` currently executes the
source-run stream under the request and cancels its producer on disconnect.
`workflow_run_record.py` is the actual durable source-run record. The core
`CanonicalWorkflowRunRepository` has tests but is not the served source-run
authority. Existing operation-monitoring/leases/continuation are useful seams.

**Alternatives:** Keeping execution in the SSE request contradicts close/reopen.
Routing source through the separate native/Rivet engine would introduce competing
semantics. Unconditional restart replay is unsafe for uncertain tool effects.

## R2 — Immutable run inputs and bounded readiness

**Decision:** Add a run-input snapshot/overlay consumed by preparation, execution
and continuation. Preserve accepted source bytes and existing source defaults.
Compile dependency readiness over supported item/order paths, including declared
human responses and upstream producers. Reject unsupported semantics explicitly.

**Rationale:** `WorkflowSourceRunRequest` in `apps/api/src/api/schemas/workspace.py`
has no values field; `workflow_run_preparation.py` reads source input_text/files.
`workflow_source_execution.py` supports connected data/order graphs and bounded
rework, not arbitrary conditional graphs. Predictable later user requirements
must be resolved without demanding future producer outputs now.

**Alternatives:** Writing user values into the accepted definition per run loses
definition/input separation. Guessing inputs at a later tool stage violates the
unattended policy. A new general graph planner is beyond this feature.

## R3 — Explicit structured-input barriers

**Decision:** Add a small source `human-input` template/declaration and continuation
version 3, preserving version 2 approval restoration. Responses become ordinary
typed output results; they are not external-action receipts.

**Rationale:** `workflow_execution_continuation.py`, `workflow_approval_execution.py`
and `workflow_external_actions.py` already pin subjects and one-shot continuation.
There is no general questionnaire barrier. The response must bind to exact source,
input snapshot, upstream outputs, schema and checkpoint cursor.

**Alternatives:** A browser-only pause is not durable. Modeling a questionnaire as
a printer/supplier action gives the wrong authority and evidence meaning.

## R4 — Interaction projection, not new execution state

**Decision:** `wright.process-interaction/1` projects existing source/run/result/
validation/review facts and new input/checkpoint facts. Mutations call the owning
service and recheck currentness; the projection does not decide engineering truth.

**Rationale:** `workflow_results.py` and `core/process_validation.py` supply exact
result/representation/profile/currentness identities. Existing approval dispatch
currently accepts local review and an enrolled test handoff only. Add one bounded
`mcp-operation` dispatcher through the gateway for genuinely configured operations.
Preserve consume/unknown-outcome rules; no generic browser invokeTool authority.

**Alternatives:** UI-owned job status, capability names guessed from vendor strings,
and a general tool-call proxy would bypass established result/action authority.

## R5 — Public packages and a fixed static-app envelope

**Decision:** Add local/pinned `@wright/process-client` and `@wright/ui-kit` packages
using the repository's npm/Vite/React/TypeScript toolchain. Generate static
App.tsx/CSS/assets plus strict bindings. A Wright-owned builder runs fixed compiler
arguments against an allowlisted bundle; no generated backend/launch/package scripts.
Save source, build report and immutable dist artifacts.

**Rationale:** `apps/web/package.json` already pins relevant tools. Existing tokens,
ImagePreviewer, ThreeDViewer and surface renderers are extraction candidates.
Current ThreeDViewer is STL-only with dark colors; export requires theme cleanup
and honest unsupported-format fallback. Isolated apps cannot import private
apps/web files or inherit parent CSS. Native/Docker installed resources must
include the public packages/instructions/asset runtime; authoring checks compiler
availability, saved use does not require it.

**Alternatives:** Runtime npm installs or model-selected build commands add fragile
execution authority. Importing private React files couples saved apps to checkout
internals. A universal declarative UI language would constrain useful composition.

## R6 — Existing isolated hosting, new process-scoped bridge

**Decision:** Reuse managed surface isolation/cookies/grants with a Wright-owned
static asset runtime. Reserve `/__wright/process` on the preview origin for the
process client. Bind authority server-side to presentation, workspace, process,
UI revision and permitted run. Do not broaden MCP App provider grants.

**Rationale:** `surfaces/manifests.py`, `live_app_service.py`, `live_app_manager.py`,
`presentation_service.py`, `presentation_tokens.py`, API `surface_route_authority.py`
and `surface_preview.py` already supply distinct origins, bootstrap, lifecycle and
reserved proxy paths. Existing manifest capability values are closed; extend them
deliberately. `wright-surface-sdk.ts` registers page-local tools for Wright to call;
it is not a page-to-process client.

**Alternatives:** Sending the parent bearer credential into generated JavaScript
or placing generated code in the control-plane origin grants excessive authority.
Static scanning is a quality gate, not a substitute for origin/server enforcement.

## R7 — Existing document tabs, explicit panel intent

**Decision:** Add typed common/working/preview descriptors to the existing
WorkspacePanel/EditorTabs host. Reuse LiveAppSurface inside the document tab,
explicitly requesting a panel for process UIs. Restore view intent from backend
references; close revokes that presentation only.

**Rationale:** WorkspacePanel has existing workflow/Rivet/BREP document tabs.
SurfaceWorkspace also has an overlay with a different tab strip; using only that
overlay is insufficient. Generic live-app defaults currently prefer browser and
auto-panel only Rivet. Preserve editor commands/layout/source conflict behavior.

**Alternatives:** Another browser window or top-level tab strip fails the agreed
journey; globally changing all app defaults would affect unrelated surfaces.

## R8 — Bounded coding role on existing adapter

**Decision:** Implement `process-ui-author/1` in workspace_service over
BaseAgentEngine, adding an optional invocation context/capability description to
the existing adapter. Initially inherit the configured default model with Hermes.
Supply effective versioned instructions every turn; return structured source and
bindings with at most two diagnostic repair attempts. No arbitrary shell/MCP tool
access is needed in the first role.

**Rationale:** BaseAgentEngine has create_session(workspace,instructions) and
stream_chat but AgentChatRequest lacks role/model/scope. Hermes `_build_messages`
reconstructs a generic hint/history, so instruction effectiveness needs evidence.
Ordinary agent/chat activates enabled workspace tools and can mutate global
gateway configuration; UI authoring must not use that broad setup. Existing
report-generation helper is Hermes-specific and unsuitable. OpenClaw is presently
a stub despite registry metadata; future adapters require qualification.

**Alternatives:** Changing the global model for one task, using a Hermes-only
helper, or building an additional agent platform conflicts with separability.
Prompt-only restrictions do not establish tool authority.

## R9 — Two existing engineering proofs, separate from campaign

**Decision:** Use fresh isolated `printed-replacement-part` and
`heat-spreader-sizing` runs; retain assignments and evidence. See
[acceptance-cases.md](acceptance-cases.md) for exact scope and gates.

**Rationale:** Printed preparation has Blender mesh → measured/repaired/oriented
geometry → actual slicing/package inspection. Heat has AgentCAD STEP/measurements
→ OASiS/scikit-fem conduction → independent fields/balance/refinement checks.
The latter is materially different from manufacturing/device monitoring.

An independent slicer is already catalogued as `bambu-p1s-mcp-marctheshark3`, pinned
upstream revision `7b50d0288fb7b91af8af422b96c4df4db0f1110c`. Historical catalog
evidence records a Windows offline STL-to-gcode.3mf result, not printer dispatch
qualification. Its slice_model_file has source/plate/output/orient/arrange/confirm
options; profiles are provider configuration, not per-call material fields.
It does not return toolpaths/preview/options. Fresh normal qualification and
bounded generic artifact inspection are required; no new Bambu MCP is needed.

**Alternatives:** Another printer would not demonstrate generality. Robot is
explicitly weak as a multi-tool flagship; water has unresolved assumptions.
Historical packages or fixed UI fixtures cannot establish the two new live proofs.

## R10 — No global feature activation during planning

**Decision:** Prepare feature 083 with explicit paths while keeping
`.specify/feature.json` and the managed 082 AGENTS block unchanged. The goal's first
implementation step activates 083 on its own branch and records the prior pointer.

**Rationale:** User guidance preserves 082/campaign history. Spec Kit setup supports
feature-directory overrides, but Bash is denied on this Windows host and no
PowerShell setup scripts are present. The plan/spec/tasks core templates were
read and used directly. Optional pre/post commit/context hooks are not executed.

**Alternatives:** Silently rewriting the active pointer or committing all dirty
prototype files would interfere with other work. No constitutional amendment or
runtime implementation is authorized by saving this package.

## Remaining dependencies, not unanswered product decisions

Fresh qualification of the installed default model, authoring compiler and
engineering providers belongs to M0/M4. Missing resources must be reported and
bounded; work on independent platform tasks continues. Live proofs cannot be
marked complete by replacing missing providers with fixtures. No unresolved
product choice is needed to start the approved implementation.
