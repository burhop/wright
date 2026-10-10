# Portable workflow instructions and deliberate user interaction

**Date:** 7 October 2026.
**Status:** Historical analysis and plan, recorded 7 October. The portable
instruction and declared input implementation completed its bounded local
verification on 8 October; see the
[implementation audit](../../specs/083-process-working-interfaces/instruction-portability-completion.md)
and [current user guide](../workflows/process-working-interfaces.md).
The original findings below describe the pre-change code and remain as rationale.
Later usability changes and unfinished engineering work are tracked in the
[execution ledger](../../specs/083-process-working-interfaces/mechanical-engineering-execution.md).
**Applies to:** the accepted workflow source, shared execution services, editor,
common working view and generated process interfaces. Follow
[V1–V7](../design/workflow-platform-vision.md) and the
[process UI contract](../design/process-apps.md).

## User journey and requirements

An author chooses how AI should work, builds the process, and saves it. A saved
or exported workflow carries the instructions that govern its behavior. Another
user can inspect those instructions and run the workflow with compatible tools
without silently inheriting different local prompt policies.

The author can allow AI to choose unspecified design parameters and document
its assumptions. Explicit requirements remain constraints. A process that needs
a person's answer, review or approval declares that interaction in its graph.
It pauses durably at that step and continues the same run after a valid response.
Unexpected missing configuration is explained as a readiness or execution
problem; it does not silently create a new question or approval.

This supports engineering design, analysis, reporting and other processes.
The sheet-metal rendering workflow is the motivating example, not a new
manufacturing-specific architecture.

## Findings from the current code

This is a static analysis of the current working tree. Previous runtime evidence
and existing tests are retained; this analysis does not qualify new behavior.

| Finding | Current source and consequence |
|---|---|
| Hidden general policy | [workflow_step_outcomes.py](../../packages/core/src/core/workflow_step_outcomes.py) embeds `UNATTENDED_STEP_POLICY`. [workflow_mcp_execution.py](../../packages/workspace_service/src/workspace_service/workflow_mcp_execution.py), `run_task`, adds the separate prohibition on inventing missing engineering requirements. Changing a workflow's visible prompt does not remove that instruction. |
| Different AI paths construct different prompts | [report_generation.py](../../packages/agent_adapters/src/agent_adapters/report_generation.py) constructs text, image and post-tool recovery instructions. Text generation says to label assumptions, while MCP execution separately prohibits inventing missing requirements. Output envelopes, behavior policy and formatting are mixed together. |
| Additional instruction sources | [hermes.py](../../packages/agent_adapters/src/agent_adapters/hermes.py) contains retry guidance, Onshape selection instructions and a conditional legacy Rivet context. [runtime.py](../../packages/workspace_service/src/workspace_service/adapters/runtime.py), `compile_workspace_mcp_instructions` and `write_workspace_agent_context`, combines code literals, installed-server instructions and `workspace_prompt`. These are distinct paths and must not be assumed to affect every workflow invocation. |
| Helper prompts also affect behavior | [workflow_cad.py](../../packages/workspace_service/src/workspace_service/workflow_cad.py), [workflow_application_task.py](../../packages/workspace_service/src/workspace_service/workflow_application_task.py), [validation feedback](../../packages/workspace_service/src/workspace_service/process_validation/feedback.py) and [hermes_openai_bridge.py](../../packages/agent_adapters/src/agent_adapters/hermes_openai_bridge.py) add instructions for resource scope, correction or protocol translation. Legacy FreeCAD chat/CFD prompts also exist under `packages/freecad_mcp`. |
| Prompt wording controls a code branch | `report_generation._recorded_evidence_completion` searches system-message text for `format response as html` / `format response as json`. Editing a prompt can therefore alter recovery formatting. These decisions need typed configuration. |
| Saving source does not snapshot all instructions | [WorkflowRecoveryPage.tsx](../../apps/web/src/components/pages/WorkflowRecoveryPage.tsx), `saveWorkflow`, sends source/layout to [workflow_sources.py](../../packages/workspace_service/src/workspace_service/workflow_sources.py). Visible step prompts, input text and `task_guidance` are saved. Hidden system/helper instructions are reconstructed later. A source digest alone therefore does not identify all behavior sent to the model. |
| Source grammar has no instruction collection | [recovery-authoring.ts](../../apps/web/src/prototypes/workflow-recovery/recovery-authoring.ts) admits a bounded set of workflow fields and step settings. [workflow_source_execution.py](../../packages/workspace_service/src/workspace_service/workflow_source_execution.py), `PromptStep` and `compile_prompt_workflow`, has no general resolved instruction-set contract. Both sides must change together. |
| Portable export is incomplete | The inspected canonical workflow file menu offers open, new and template selection; no complete instruction/dependency export contract was found there. Copying a `.wflow` transfers its embedded step data but cannot transfer code-injected prompts, local server identities or external input files automatically. Existing run-evidence export is a different artifact. |
| Execution evidence does not consistently preserve submitted instructions | The executor records task prompts, tool evidence and model usage, but ordinary task paths do not consistently persist the complete Wright-submitted system/helper messages. The compatibility run route in [workspace.py](../../apps/api/src/api/routers/workspace.py) also reconstructs `format_instructions` from current code when returning results/events. Those reconstructed strings are not reliable historical evidence. |
| A reusable foundation exists | [process interface resources](../../packages/workspace_service/src/workspace_service/process_interfaces/resources/__init__.py) loads versioned instruction files. [authoring.py](../../packages/workspace_service/src/workspace_service/process_interfaces/authoring.py) retains instruction text and resource identity; [CodingRole/RoleResolution](../../packages/core/src/core/process_interfaces.py) and [AgentInvocationContext](../../packages/agent_adapters/src/agent_adapters/base.py) record instruction/model/adapter identities. These are scoped to UI authoring today, not a completed general prompt-settings system. |
| Explicit input is already implemented | [workflow_human_input.py](../../packages/workspace_service/src/workspace_service/workflow_human_input.py) compiles a declared typed input step. [workflow_human_input_runtime.py](../../packages/workspace_service/src/workspace_service/workflow_human_input_runtime.py), [interactions.py](../../packages/workspace_service/src/workspace_service/process_interfaces/interactions.py) and [runs.py](../../packages/workspace_service/src/workspace_service/process_interfaces/runs.py) preserve the checkpoint, response identity and same-run continuation. |
| Input authoring is too technical and limited | [authoring-objects.ts](../../apps/web/src/prototypes/workflow-recovery/authoring-objects.ts) puts “User input step” under More. [InteractionDeclarationEditor.tsx](../../apps/web/src/prototypes/workflow-recovery/InteractionDeclarationEditor.tsx) requires a JSON response declaration. The compiler requires upstream task evidence, preventing a straightforward first step that only asks the user for information. |
| Diagram transport can misreport a valid wait | The compatibility run route accepts `completed`, `pending_review` and `awaiting_approval`, but excludes `waiting_human`. Its response schema and [web client](../../apps/web/src/services/workspace-service.ts) share that omission. The shared process projection already understands `waiting_human`. The route delegates to the existing supervisor, so fix its projection/transport rather than introducing another runner. |

## Recommended instruction architecture

### Resolve defaults when authoring; preserve them when saving

Use one shared resolver with this explicit authoring order:

1. Wright-wide, role-specific defaults.
2. An optional explicit workspace/organization profile, using existing workspace
   configuration where appropriate.
3. Workflow instructions and behavior settings.
4. Step instructions and permitted step overrides.

Structured policy fields override by key with validation. Free-text layers have
an explicit append/replace mode and visible order. Do not attempt to infer an
override by comparing prose. Show the effective instructions for each step,
their origin and any overridden settings before saving.

On the first save, materialize the selected defaults and every applicable
Wright-owned prompt template into the accepted workflow revision. Later saves
preserve that snapshot unless the author explicitly edits it or chooses “Update
from current defaults.” Updating global settings applies to new drafts; it does
not rewrite existing workflows, exports or in-progress runs. Updating defaults
in an existing workflow produces a visible diff and a new accepted revision.

Keep role scoping: a workflow task, image generator, chat assistant and confined
UI author have different capabilities. Shared resolution must not inject general
chat history or broad workspace instructions into a confined authoring role.

### Store text as data and make instruction dependencies complete

Introduce a versioned instruction-set contract in `core`. Each entry contains an
identifier, role/purpose, body/template, version, digest, originating profile,
template variables and compatible execution-contract version. Workflow and step
bindings select entries by stable ID and digest. Deduplicate shared entries
within a workflow; a global profile ID without its text is insufficient.

Put shipped default instruction text in packaged resources with a schema and
version. Expose behavior defaults through authenticated settings backed by
existing configuration/storage ownership. The Settings page's current browser
UI preferences are not adequate persistence for execution policy.

Extend the `.wflow` grammar with an explicit instruction collection and policy
bindings, updating the shared contract, frontend model/parser/formatter/commands
and backend compiler together. A simple saved `.wflow` must contain all required
instruction text. Optional bundles may carry larger assets, but must not make
the basic saved workflow depend on a machine-local prompt file.

Capture the whole instruction dependency chain: main system messages, response
format templates, bounded repair/recovery templates, resource-context framing
and validation-feedback framing. Keep tool descriptions and schemas attributable
to their external provider. Parameterize workspace paths and run/result IDs;
save the templates, never the previous user's absolute paths or credentials.

Protocol templates can be versioned, inspectable compatibility resources with
restricted editing. They travel with the workflow alongside behavior prompts.
Backend permissions, schema checks, output verification and approval enforcement
remain executable rules. A prompt claiming permission cannot grant it. Required
runtime incompatibility blocks execution with an explicit migration path.

### Preserve the effective invocation and support portable exports

At run start, resolve a frozen execution profile containing the accepted source,
instruction set, structured policy, model/adapter selection and qualified tool
bindings. Record it with the existing durable run/continuation context.
Continuations reuse that identity; a service restart or default change must not
substitute new prompts halfway through a run.

Before each model request, retain the actual Wright-submitted instruction text
and message order, rendered template values, tool-schema identities and input
artifact references. Include recovery/translation calls in this provenance.
Large images/files can use immutable references and hashes. Use existing access
and redaction controls; credentials must not enter shared workflow exports.
State the boundary honestly: Wright can record what it submits and the reported
provider/model version, not undisclosed provider-internal system instructions.

Provide “Export workflow” with the instruction-complete source and a manifest.
When the process uses reference files, validation profiles or saved working UI,
offer a bundle containing selected required assets, layout, UI bindings/source
and compatibility versions. Identify deliberately external dependencies. Import
checks completeness, schema versions and tool/model capabilities before running.
Map portable provider bindings to local installed servers through the existing
registry. A local UUID or friendly name alone is insufficient to prove equivalence.

An import must not silently replace embedded instructions with local defaults or
copy execution approvals, credentials or active-run authority. Any instruction,
model or tool substitution is visible and recorded. Record the actual model
resolution even when an author explicitly permits compatible model substitution.
Identical prompts improve reproducibility but do not guarantee identical
generative outputs or availability of a provider's old model version.

## Assumptions, errors and deliberate pauses

Offer a workflow setting for **Document reasonable assumptions** versus **Require
specified values**, with explicit step overrides and protected requirements.
For new design-oriented workflows, recommend the first setting. Existing
workflows keep their captured policy during migration until deliberately updated.

Allowing assumptions is declared AI work. Record each chosen value, units,
rationale and affected output as an assumption, separate from supplied facts and
measured evidence. An explicit requirement cannot become an assumption merely
because it is inconvenient. Changes to assumptions invalidate affected downstream
results/reviews through the existing dependency and revision mechanisms.

For the current L-shaped-part demonstration, an assumptions-enabled design step
may select and document the unspecified bend parameters while preserving the
provided thickness, flat dimensions and centered bend. This would not authorize
changing a required dimension or claiming the result was checked. Documented
assumptions remain available as run evidence even when the deliverable is an image.

| Situation | Recommended behavior |
|---|---|
| A required initial field, prompt resource or tool binding is absent | Block Start with a readiness explanation and the field/step to fix. Save incomplete drafts normally. |
| An unspecified design choice is within the saved assumption policy | Choose and record an assumption, then continue. |
| The workflow reaches a declared input step | Enter “Waiting for your input,” persist its exact question/evidence/schema, and resume the same run after a valid response. |
| The workflow reaches a declared review/approval step | Wait under the existing review/action contract for the exact subject. An ordinary input answer does not count as approval. |
| A submitted answer fails its schema | Keep the same checkpoint pending and show field-level corrections; do not fail or restart the process. |
| A required choice is discovered inside unattended work, assumptions are disallowed, and no question path was declared | Stop with an actionable configuration/execution error. Preserve completed outputs and explain how to revise the workflow. Do not invent a dialog or resume a failed run with changed instructions. |
| Validation finds a design defect | Follow the declared bounded rework/review policy; hold dependent work until its existing checks pass. |
| A provider is temporarily unavailable | Follow the configured bounded retry/wait policy and display its reason. Retry only where the operation's contract establishes that it is safe. |
| A submitted external operation's outcome is unknown | Require reconciliation of that recorded operation; do not replay it or label it completed. |
| The model/tool returns an invalid result or recovery is exhausted | Report a failure with step, cause, evidence and next action. Keep already produced artifacts accessible. |

No blanket “ask whenever unsure” setting is recommended. A requirements-analysis
step can instead produce a structured list of unresolved choices and proposed
assumptions as its normal output. An explicitly connected user-input step owns
the subsequent questions. An analysis step reporting unresolved requirements is
different from a construction step falsely claiming to have completed its work.

Static readiness can check declared fields, dependencies and capabilities; it
cannot guarantee that it has understood every requirement in arbitrary prose.
Use an explicit requirements-analysis/validation stage where semantic review is
needed, and retain honest runtime failures for genuinely unexpected conditions.
The requirement is predictable behavior with useful evidence, not a promise that
every possible problem can be detected before the first step.

## User-input step recommendation

Promote the existing **User input step** as **Request input** in the Create UI.
Reuse its current checkpoint service, scoped client and durable continuation.
Keep Request input, engineering validation and Review/approve as distinct
contracts; present them together as familiar process-building choices.

Replace mandatory JSON editing with a field builder for the existing supported
schema subset: text, numbers/units, choices and required fields. Keep source/JSON
editing available. Show the question's instructions, connected evidence and
answer output ports in both the diagram and common working view. Responses are
run inputs and do not rewrite the reusable definition.

Extend the declaration deliberately to support an initial input step without a
fake upstream AI task. Prefer the preparation form for values needed immediately;
allow an explicit first interaction when that is the intended process. This
requires corresponding changes to the compiler, checkpoint subject schema and
readiness classifications, not just removing a UI restriction.

Initially implement the current unconditional checkpoint clearly. For conditional
questions, add a versioned, bounded declaration such as “ask when declared fields
are unresolved,” driven by a typed upstream requirements result. Validate the
condition and response schema before starting, persist evaluated evidence, and
record a skip when no response is needed. Do not imply arbitrary conditional
graphs or agent-generated, unconstrained forms already work. Variable question
wording must come from an explicitly bound upstream output; allowed answer fields
and their types remain declared.

Make the diagram's run transport, summary types, history and error banner reflect
the same `waiting_human` checkpoint as the common/generated view. “Continue”
submits a typed response through `process-client.respond`, which rechecks the
exact run, step, instruction/source revision and evidence. Reopening either view
reconciles with that checkpoint; duplicate responses or reconnects cannot replay
completed steps. Preserve the existing prohibition on automatic rework loops
crossing an already answered human checkpoint until a versioned design supports it.

## Implementation sequence and ownership

| Stage | Work and owning seams | Completion evidence |
|---|---|---|
| 1. Contract and inventory | Complete the instruction-call-site inventory above; define instruction assets, effective policy and invocation records in `core`. Specify grammar/version changes and migrate prose-driven recovery branches to typed values. Update platform/agent guidance with the distinction between permitted assumptions and changed requirements. | Every Wright model invocation path has an instruction owner and export/provenance disposition. No branch depends on human-readable prompt wording. |
| 2. Settings and portable saved source | Add server-backed role defaults and shared resolution using existing settings/repositories. Extend canonical editor commands, source parsing/formatting, storage revisions and compiler. Add workflow/step settings, effective-instruction inspection and explicit default updates. | Save/reopen/clone/export/import retains instruction text, precedence and digests; changing local defaults does not alter a saved revision. Draft and conflict handling preserve user edits. |
| 3. Execution and historical evidence | Pass the resolved profile through run preparation, ordinary text/image/MCP paths, helper prompts and qualified adapters. Snapshot it in recorder/continuation; retain actual invocations. Replace response-time instruction reconstruction. Migrate vendor-specific chat guidance to explicit provider-owned/catalog resources and retire obsolete Rivet injection under its existing cleanup work. | Both model paths and post-tool recovery use the saved instruction set. History displays recorded instructions. Restart/resume cannot change policy or duplicate effects. |
| 4. Assumptions and interaction UX | Add explicit assumption output/provenance, friendly Request input configuration, first-step support and compatible wait handling in the diagram API/client. Reuse validation, review, common UI and scoped response actions. Add conditional questions as a separately versioned increment after unconditional waits work across views. | Assumptions continue when permitted; declared input and approval wait visibly; invalid answers remain pending; undeclared questions fail clearly; affected evidence invalidates correctly. |
| 5. Portable package and migration qualification | Export/import required prompt/UI/reference assets and provider binding requirements. Preserve legacy source revisions/runs. Offer “Make instructions explicit” with a diff; use a named compatibility profile for unmigrated definitions and mark them as dependent on legacy defaults. | Two installations/workspaces with different defaults execute the same exported instructions. Missing capabilities are diagnosed before start. Legacy history is not rewritten or claimed to have captured prompts it never recorded. |

Phases 2–4 depend on the versioned contracts in phase 1. A minimal source-only
export is part of phase 2; phase 5 adds dependent assets and broad migration
qualification. Settings and prompts do not create a second executor, validator,
provider implementation or job-status authority.

Use the existing storage/CAS path for accepted edits; model/adapter resources for
prompt delivery; gateway/registry for tools; run recorder and continuation store
for execution; validator/review owners for evidence; workspace tabs, UI kit and
process client for presentation. Extend existing owners rather than creating a
parallel prompt runner or agent platform. New UI bindings declare their supported
contract/client/kit versions. Older generated UIs fall back to the common view
when required instruction or interaction bindings become incompatible.

## Verification and acceptance plan

1. **Instruction portability:** Save a workflow under defaults A. Change the
   global/workspace defaults to B, reload and export/import into a fresh workspace.
   Confirm identical saved instruction bodies/digests and effective policy. An
   explicit update shows a diff and creates a new revision. Include Save as,
   clone, source/diagram round trips and concurrent-save conflicts.
2. **Complete invocation coverage:** Exercise ordinary text, image, MCP and their
   correction/recovery paths. Compare the request actually handed to the adapter
   with retained evidence. Change wording without changing typed output settings
   and verify recovery behavior is unchanged. Confirm no hidden source literals
   reintroduce the old assumption rule.
3. **Assumption behavior:** Use the existing CAD-to-render process with permitted
   missing design choices. Check visible assumption records and preserved explicit
   dimensions; then disable assumptions and confirm useful readiness/failure
   behavior. An image alone does not establish dimensional correctness.
4. **Deliberate pauses through the normal workspace:** Start from the flowchart,
   reach Request input, switch to the working view, close/reopen, answer and
   resume. Verify the same run and completed tool-call identities. Repeat with a
   review checkpoint, invalid/duplicate answers and stale evidence. The diagram
   must never turn a normal wait into a red failure banner.
5. **Changed conditions:** Stop/restart the owned test service at a declared wait;
   change global defaults; resume with the captured profile. Exercise a missing
   tool, incompatible template version and uncertain external outcome using
   isolated digital checks. Each produces the specified state without replay.
6. **Generality:** Reuse the existing Robot Tracking Diagnosis template for a
   data-to-metrics-to-report process with a declared choice of analysis interval
   or interpretation. Qualify actual provider bindings before claiming live
   execution. Preserve its original metric tolerances and review requirements.
   Show evidence passed between tools; a synthetic graph or valid files alone
   do not prove the shared mechanism works for another engineering job.
7. **Package and UI compatibility:** Import with required reference/prompt assets
   missing or changed; verify explicit diagnostics. Test generated UI fallback,
   exact result/step navigation and opening saved UI without regenerating it.

Use focused contract and runtime tests for inheritance, identity, pause/resume
and duplicate-effect prevention, plus served-workspace walkthroughs for the human
journey. Record actual build, workspace, source/run identities and provider/model
resolution. Keep static findings, implemented changes, verified behavior and user
acceptance separate. This document alone does not claim those checks passed.

## 8 October implementation guardrails and evidence boundaries

The approved implementation uses the existing instruction settings/source owner,
run recorder and continuation repositories. Behavioral defaults are versioned
resources and saved instruction bodies; typed formats and interaction declarations
drive runtime branching. New prompt policy must follow these seams, including
helpers and repair calls. Backend schema, exact-subject validation and permission
checks remain deterministic enforcement and cannot be disabled by prompt text.

Model resolution is recorded separately from integration enrollment. Modern runs
freeze the configured provider/model/profile and endpoint/SDK identities; resume
revalidates them before consuming a response. Changed routing is an explicit
configuration failure, without guessing, substituting a provider, or replaying
completed operations. Text/MCP requests create a fresh owned gateway session and
require exact model-lock confirmation before sending the model request. A route
snapshot or an integration-test actor label is never an approval/dispatch grant.
Legacy checkpoints retain their recorded shape rather than acquiring invented
historical instruction or routing evidence.

Actual request captures use existing run evidence, interface-generation records,
and confined authenticated workspace/session chat sidecars. Captures retain
resource identities, redacted request fields and image hashes, including failed
attempts. Requested model aliases, confirmed routes and reported upstream model
revisions are separate facts. Wright cannot inspect upstream internal prompts or
tool turns. Native SDK worker capture is forwarded on bounded cleanup; a host
crash before forwarding leaves an unknown outcome, not proof of submission or
permission to replay.

Portable packages preserve accepted instruction text and required reference,
validation and UI dependency identities. Importability is distinct from readiness
to run. Imports create fresh local source paths and inactive UI candidates,
without credentials, run/review authority, registry grants or trusted builds.
Missing/tampered assets and mismatched pinned profiles fail import qualification;
missing model/tool capabilities block readiness. Saved UI compatibility and local
review use the existing common-view fallback.

Implementation and isolated regression evidence are recorded in
[the invocation inventory](../../specs/083-process-working-interfaces/evidence/instruction-invocation-inventory.md),
[the routing and invalidation audit](../../specs/083-process-working-interfaces/evidence/frozen-model-routing-and-assumption-invalidation.md)
and [bundle transfer evidence](../../specs/083-process-working-interfaces/evidence/workflow-bundle-transfer.md).
These links do not imply live engineering validation or user acceptance; served
workspace and actual provider proofs remain separately identified by their owners.

### 9 October — repair requests must retain their own context

The installed Hermes chat endpoint replaces submitted prior turns with stored
history when `X-Hermes-Session-Id` is supplied. A fresh, model-locked session has
no history. The bridge's earlier repair shape (task, failed assistant decision,
then a short correction user turn) therefore lost the task, schemas and image
at that upstream boundary. A live isolated diagnostic returned that the allowed
tool and argument schema were absent even though the HTTP request contained them
in earlier messages. Do not remove the model lock or reuse uncertain sessions.

The bridge now renders the original transcript, tools, previous rejected decision
and saved repair instructions together in one current user message, retaining
native image attachments. The existing complete-text budget covers this envelope;
an oversized mandatory repair fails before another submission. The adapter still
validates tool choice, argument schema and action intent before dispatch.

Default instruction profile 1.2.1 explicitly describes the full repair envelope.
Accepted workflows retain their embedded versions. The isolated wheel source026
is a new accepted revision with only that helper and workflow identity changed;
no geometry or inspection criteria were relaxed. Response-phase evidence at the
existing invocation owner now includes the response hash, JSON shape and bounded
redacted final-message context, including terminal rejected repairs. It does not
claim full response retention or provider-internal prompt visibility.

The mechanical execution ledger records the reproduced context loss, model-only
diagnostics and actual CAD-run outcomes separately. A translated tool decision
alone does not establish execution, an engineering pass or user acceptance.
