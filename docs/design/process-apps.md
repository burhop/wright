# Process UIs inside Wright

**Date:** 30 September 2026.
**Direction:** [Workflow platform vision](workflow-platform-vision.md), V1-V7.
**Status:** Agreed user experience and architectural direction. Feature 083 is
locally implements its bounded interaction contract, scoped client, common view,
public UI kit and configured-model authoring path. Two actual digital engineering
chains, saved reuse, migration and installed native/Linux UI-resource checks have
recorded evidence. Final local completion and limitations are tracked in the
[completion audit](../../specs/083-process-working-interfaces/completion.md);
release and human/physical engineering acceptance remain separate.

The concrete technical package and ready-to-use goal are in
[Feature 083](../../specs/083-process-working-interfaces/plan.md). It includes
the complete AI-created/reusable interface experience and two engineering proofs,
not only the shared kit. The submitted goal approved implementation. See the
[task record](../../specs/083-process-working-interfaces/tasks.md) and
[progress record](../../specs/083-process-working-interfaces/progress.md) for
checked scope; this vision is not a completion or release claim.

## User experience

Keep the flowchart and block inspector for composing, configuring, inspecting,
and debugging a workflow. Offer an optional process UI for people carrying out
the job: providing inputs, checking results, making decisions, and following work.
Both experiences use the same accepted workflow and backend run records.

The user journey is create/open, choose a common or tailored working view,
review/save that view, run in the workspace, and inspect/refine when needed.
See [How users work](workflow-platform-vision.md#how-users-work). One person can
use either experience; these are not mandatory separate user roles. A run's input
values are distinct from edits to the accepted process definition.

A process UI opens in a workspace tab by default, retaining the workspace and
its navigation. It can link directly to the relevant block, result, finding, or
run detail. Opening an external browser remains an explicit presentation choice.
Closing the tab is not cancelling a run; reopening reconciles with durable state.

AI can build a useful interface for a particular process when it has a documented
Wright foundation. Users request generation and updates through Wright, initially
using its configured default LLM. Supply the foundation once, then reuse it across processes.
The AI arranges interactions and explanations appropriate to the engineering job.
Wright provides common controls, styling, hosting, and process operations.

## Responsibilities

| Layer | Responsibility |
|---|---|
| Accepted workflow | Engineering steps, capability bindings, artifact dependencies, configured requirements, review checkpoints, and permitted actions. |
| Wright process services | Execution, durable state, result identity, validation, review decisions, external-action evidence, events, and recovery. |
| Process interaction contract | Explicit available inputs, outputs, pending questions and reviews, evidence, state, and permitted actions with exact subjects. |
| Shared UI kit and scoped client | Reusable views and controls, theme, accessibility, navigation, and consistent calls to existing process services. |
| Process UI | Job-specific layout, useful instructions, input presentation, result composition, and workflow-defined user interactions. |
| Existing MCP providers | Engineering operations and vendor/device behaviour, with their actual supported options and limitations. |

The process UI does not execute a graph, sequence tool calls in browser code, or
maintain an independent truth about job completion. A backend checkpoint can be
presented differently in the diagram and process UI without changing its meaning.
Device status and options come from bound provider results, not hard-coded slot
counts, profiles, firmware assumptions, or vendor protocols.

## The process interaction contract

This is the critical connection between a process and a working interface.
Publish a bounded, versioned description derived from the accepted definition,
configured capabilities, and actual run state. Reuse existing shapes wherever
possible. Its conceptual contents are:

| Information | Meaning to the UI |
|---|---|
| Context | The actual workspace, accepted definition revision, run, and supported contract version. |
| Inputs | Names, value schemas, units, references, defaults, availability, and declared consequences of changes. |
| Outputs and evidence | Exact result representations, assessments, provenance, findings, and supported viewing/download options. |
| Pending interactions | A declared question, required user action, or review decision the process is currently waiting for; no opportunistic runtime clarifications. |
| Allowed actions | A currently permitted operation, its exact subject, prerequisite state, and an actionable reason when unavailable. |
| Observed state | Activities, progress, lifecycle, external observations, and the freshness or limits of that information. |

The AI uses this description to choose controls and compose useful explanations.
For example, a review button corresponds to a pending decision on an exact output;
the backend records the decision and governs subsequent work. Neither the AI nor
the UI invents that checkpoint, bypasses checks, or becomes an authority on which
operation is permitted. The diagram and process UI consume the same facts.

This contract is not a universal screen schema or a promise of every possible
graph arrangement. Custom viewers and declared extensions can carry specialised
content. Common UI can expose supported interactions without requiring a custom
app, and unsupported semantics remain explicit.

## Run readiness and deliberate interaction

Gather required user choices during preparation. Before starting, validate that
later steps' required inputs are supplied, explicitly defaulted, automatically
produced by declared upstream work, or assigned to a declared user-interaction
step. Analyse the supported paths and identify unresolved conditions honestly;
do not make an unattended run discover predictable missing configuration later.

The process defines its human review/action points. At one of those points the
runtime persists a waiting state and resumes the same run after the response.
An unattended section does not ask new questions because an AI feels uncertain.
Unexpected missing input is an execution/readiness defect with a diagnostic,
not an invented form. A process explicitly designed for a dialogue may declare
that interaction and its allowed scope.

Intermediate engineering outputs are expected to be generated during the run.
Current external availability and evidence must still be checked before actions.
Follow declared wait/recovery/failure policy when circumstances change, without
guessing required values or silently replaying effects. Present the distinction
between waiting for a planned decision, waiting for an external condition, and
failure in both common and tailored views.

## Start with reusable interactions

Feature 083 provides a bounded kit assembled from Wright components and design tokens:

- Text, image/file, dimension/unit, and capability-backed option inputs.
- Run progress, current activity, actionable errors, and reconnect state.
- Result and evidence views: images, 3D geometry/toolpaths where supported,
  tables, charts, findings, and downloads by representation identity.
- Review controls and workflow-defined actions with prerequisite reasons.
- Optional live observations, including a camera stream when a bound capability
  supplies a supported presentation. Absence is disclosed, not silently invented.
- Navigation to the source workflow and exact block, run, or assessment.

Begin with schema-based forms and standard result views as a common fallback.
Allow AI-authored custom composition for workflows that benefit from it. Do not
attempt a schema capable of expressing every possible application, or require
every process to have a generated app. Specialised widgets remain possible.

Build and style the kit for the chosen hosting model. An isolated app cannot
import private React files or inherit the parent frame's CSS automatically.
Bundle the appropriate public components/styles and define theme updates through
the host contract. Do not copy each page's controls into a new styling system.

## A scoped process client

Design a small versioned client over the existing process services. Its intended
operations include binding inputs, starting an accepted workflow, reading and
following a run, retrieving outputs and assessments, recording a review decision,
and requesting the next permitted action or a supported cancellation.

Feature 083's [interaction contract](../../specs/083-process-working-interfaces/contracts/process-interaction.md)
defines implemented operations and native/presentation transports. Map future
operations to current services first. Where a contract is missing, add the smallest
reviewed extension to the owning service; do not create a process-app executor.

The host supplies the actual workspace, workflow revision, run, and permitted
scope. Backend services enforce identity, review prerequisites, and capability
authority. Generated apps receive only declared process operations and result
references; no copied admin token, arbitrary cross-server authority, or printer
credentials. Keep this as normal Wright platform behaviour rather than an extra
permission sequence in the engineering task UI.

Bind UI fields to accepted workflow inputs and result representations, not graph
coordinates or campaign filenames. Changing an input or option invalidates the
dependent work and reviews through declared backend dependencies. A refreshed UI
must not show a previous revision's approval as permission for a new output.

Run progress and external-operation observations remain distinct. An accepted
submission is different from an observed machine start. Missing updates need an
honest waiting, reconnect, or unavailable state; refreshing must not resend an
action with an uncertain outcome.

## Reuse current hosting without conflating its contracts

The current code already includes workspace surface tabs and restoration,
managed application hosting, packaged MCP App views, workflow run/result/review
services, a run event stream, and shared design-token files. See
[workspace surfaces](../workspace-surfaces/README.md),
[MCP Apps and scoped WebMCP](../workspace-surfaces/mcp-and-webmcp.md), and the
[workflow UI integration guide](../contributing/workflow-ui-integration.md).

Those are foundations, not evidence that a complete generated process UI client
already exists:

- A packaged MCP App is a tool/provider view. Its same-server operations remain
  scoped to that provider. It does not gain authority to coordinate other servers
  or the whole workflow by becoming a process UI.
- The current Wright WebMCP SDK registers page-local tools that Wright can call.
  That direction alone does not give an app a client for starting Wright processes.
- A Wright process UI needs an explicit host-mediated process contract. Reuse the
  surface lifecycle and backend services while designing that bounded bridge.
- Preserve both the existing editor tabs and surface presentation rules. Any
  common tab integration needs served-workspace verification; adding another
  disconnected tab strip or standalone route does not establish the desired UX.

Choose the initial packaging model during technical planning. It might be a
declarative view rendered by Wright or a packaged managed app using the shared
kit and client. Arbitrary generated code is not loaded into Wright's main browser
context merely to give it styling or service access.

## Generation, persistence, and compatibility

### Coding-agent role

UI authoring is a Wright operation. The first implementation dispatches it through
the existing agent boundary using the configured default model and prepared
Wright API/UI instructions. A role/profile can later select a different model
or qualified agent platform without changing the workflow executor or UI client.

Map the smallest profile into existing configuration rather than creating a new
agent subsystem. Its design subjects are role identity/version, inherited or
explicit model choice, versioned starting/system instructions, permitted tools
and workspace scope, and adapter capability requirements. The instructions teach
Wright API use and shared UI composition; backend grants remain the authority.

Hermes is the current platform; Codex, OpenClaw, and future platforms are possible
qualified execution environments for the same role. Implement and verify the
first supported path without claiming all prospective platforms are supported.
Record resolved model/profile/prompt/adapter provenance, progress, failures,
generated artifacts, and validation/preview results. Any clarification needed
for UI creation belongs to that declared authoring interaction.

### Save and reuse the interface

AI authors the UI during process creation or refinement, using a reference app,
documented client, available components, the interaction contract, and real
capability descriptions. Save the resulting UI as a versioned workspace artifact with a
binding manifest. Record its workflow compatibility, client/kit versions, input
and result bindings, actions, and required capabilities.

Reuse that artifact on later runs. Do not regenerate the application each time.
If the accepted workflow or capability contract changes, check those bindings
and offer a specific update when needed. Layout changes need not invalidate
engineering output; input, decision, and action semantics must retain exact
revision binding. A missing or incompatible UI leaves the common view available.

Review the actual generated UI, including responsive layout, keyboard use,
available and unavailable actions, revised outputs, disconnect/reload, and
reopening an existing run. A plausible screenshot is not proof of correct process
binding or engineering verification.

## Immediate product plan

1. Map the agreed user journey and interaction contract to existing process,
   result, review, validation, event, and workspace-surface services.
2. Design the first scoped process client, common view, and shared UI kit. Reuse
   existing design tokens, useful viewers, and workspace tabs.
3. Implement generation, preview, saving, and updates through Wright's default
   coding-agent role, with model/prompt/profile provenance and shared authoring
   references. Reuse generated interfaces with checked bindings and supported
   kit/client versions. Validate input readiness and declared interaction points.
4. Migrate a reference process and prove the foundation with a substantially
   different existing engineering process. Qualify their existing MCP providers
   as needed; keep provider-specific compatibility work outside Wright.

See the [refactoring plan](../architecture/workflow-platform-refactoring-plan.md).
The [operator/developer guide](../workflows/process-working-interfaces.md) describes
the implemented controls, native API, replaceable coding role and current
qualification limits. Runnable read-only examples are in
[process-interface examples](../../examples/process-interfaces/README.md).
This is a bounded addition to the workflow platform, not a requirement to build
or maintain a new Bambu MCP, replace the flowchart, or generate every UI by AI.
