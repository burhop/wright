# Process working interfaces

Wright offers two views of the same accepted process and durable run: the
flowchart/source editor for building and inspecting, and a common or tailored
working interface for carrying out the job. The process defines its stages and
decisions. A tailored interface changes presentation, not execution.

**Qualification:** Feature 083 is locally verified on
`codex/083-process-working-interfaces` within its bounded contracts. Common/tailored
views, actual-model generation/update, saved reuse, prototype migration, two digital
engineering chains and installed native/Linux UI-resource checks have evidence.
The [completion audit](https://github.com/burhop/wright/blob/dev/specs/083-process-working-interfaces/completion.md)
records exact limitations. This guide is not a release or engineering-acceptance
claim. Consult the
[task record](https://github.com/burhop/wright/blob/dev/specs/083-process-working-interfaces/tasks.md).

## Current-source setup

This guide describes development source as of 11 October 2026. Published releases
may lag it. Current native and Docker builds enable the workflow editor, working
views and workspace surfaces. For a standalone source frontend, enable these Vite
flags **before building**:

```dotenv
VITE_WRIGHT_WORKFLOW_RECOVERY=true
VITE_WRIGHT_WORKFLOW_COMPOSER=true
VITE_WRIGHT_PROCESS_DEFINITION_VIEW=true
VITE_WORKSPACE_SURFACES_ENABLED=true
```

Set `WRIGHT_WEB_API_PROXY_TARGET` to the running Wright API. These flags enable UI
surfaces; they do not configure a model, install engineering applications or grant
MCP permissions. Use the normal authenticated workspace and enable the providers
needed by the selected process. Existing release installation instructions remain
in the [getting-started guides](../getting-started/overview.md).

Docker exposes the same four names as build arguments, defaulting to `1`.
They are compiled into its frontend; changing container runtime environment
variables does not enable a feature omitted during the image build. The native
builder and merge gate use the same enabled features.

Bundled Hermes 0.19.0 does not expose the discovery/session-lock HTTP contract.
Docker now explicitly selects Wright's existing confined SDK transport for
workflow responses and tool decisions. It resolves the configured provider/model
and freezes the profile, endpoint and SDK identity; changes hold continuation.
Tool proposals still pass through Wright's existing validator/runtime/gateway.
There is no tool executor in the SDK worker or fallback after a failed request.
The workspace shows only the observed configured model and directs intentional
changes to Model Setup. Source/native hosts retain the HTTP transport unless an
operator explicitly configures a qualified SDK installation.

The clean candidate image passes the installed stock-package test using synthetic
local endpoint responses. Its normal packaged workspace walkthrough verifies blank
authoring, save/reopen and discovery of the model from setup's named profile.
These checks establish request/evidence mechanics and packaged authoring; live
provider inference and engineering acceptance require separate evidence. See the
[packaged profile qualification](https://github.com/burhop/wright/blob/dev/specs/083-process-working-interfaces/evidence/mechanical-packaged-model-profile-092.md)
for exact source/image identities and scope.

The full delivery gate and publication remain pending. Gateway health alone is
not routing qualification. See the
[delivery checkpoint](https://github.com/burhop/wright/blob/dev/specs/083-process-working-interfaces/dev-delivery-checkpoint-090.md)
for its scope. Previously qualified native/provider evidence is separate.

## Instructions, assumptions and deliberate questions

Choose **Instructions** in the workflow editor to inspect the saved
instruction collection, effective role instructions and assumption policy.
**Document reasonable assumptions** allows unspecified choices to be recorded;
explicit requirements still constrain the task. Step overrides are inspectable
in the block's instruction controls. Protocol instructions remain subject to
compatibility checks and backend enforcement.

In Settings, **Workflow instruction defaults** configures newly authored
workflows. **Update from current defaults...** proposes an explicit update for an
existing workflow; review it and save a new revision. Changing global defaults
never silently changes a saved workflow or a run already underway.

Use **Request input** for a deliberate question, including a first-step question.
Configure its fields and connect its response to downstream work. A declared
condition can select whether to ask. A valid answer continues the same durable
run. It does not approve an engineering review or authorize an external action.
Unattended steps do not create opportunistic questions; missing configuration
appears in readiness, and execution faults retain an error or configured hold.

**Export / import workflow** includes saved instruction bodies and supported
reference, validation and UI dependencies. Inspect the package before importing;
configure missing capabilities in the receiving workspace. Credentials, live
runs, prior answers, approval authority and trusted UI builds do not transfer.
Imported UI source requires local compatibility checking, rebuild and review.
If an import is interrupted, inspect its destination and retained files before
another attempt. Wright reserves the import manifest before writing assets and
publishes the workflow source last. A manifest records the intended transfer;
it does not prove completion. An existing manifest blocks another import at that
destination, including after restart. Partial files are retained for reconciliation.

## Open an existing run

**Open working view** prepares the saved process for a new run. To follow work
already started, expand **Run details**, then **Previous runs**, expand the
recorded run and choose **Open run in working view**. This opens that exact run
in a Wright tab. Reloading reconciles its observed state; it does not start again.
The link requires a recorded run identity and the current accepted source digest.
Other revisions retain **Open saved run log** and their recorded results.

When the diagram source cannot be drawn, the error remains visible and **Results
from the saved run** includes the same history controls. Opening existing work
does not repair the definition, relax its checks or approve its results.

## Open and prepare a process

### Name a workflow in the diagram

Click the workflow name above the diagram to edit it. Press **Enter** or move
focus away to apply the name, then **Save**. **Escape** cancels the edit; an empty
name restores the previous one. **Undo** and **Redo** include name changes.
The name is saved in the workflow definition; this does not rename its file or
start a run. Name editing follows the same locks as other diagram edits during
an unapplied source draft, pending save, run or candidate preview.

### Connect a CAD model between steps

For a configured CAD task that supports identified model handoffs, choose
**CAD model from another block** under **Model to work on**. The task exposes a
**CAD model** input immediately. Drag a compatible upstream CAD model output to
it, or use the **CAD model from** list in the Inspector. Both edit the same
connection and support **Undo**, **Redo**, **Save** and reopening.

Choosing **Create a new model** removes the upstream model connection and its
input. This does not run a CAD operation. Compatibility and run readiness still
depend on the configured providers and workflow; a drawn connection alone does
not establish that a model has been produced or verified.

### Rebuild an imported interface

Open the imported workflow's working view and choose **Create or choose interface**.
When the workflow package includes interface source, **Imported interface** lists
those candidates. Select one, describe the adaptation in **How should this
interface help the user?**, then choose **Rebuild imported interface**. Review
the resulting **Open preview** before choosing **Save interface**. The saved
local interface is then available for reuse on this process's runs.

The imported source is reference material for Wright's configured coding role.
It does not transfer a trusted build, credentials, answers, approvals or a live
run. Wright checks the exact selected bytes, records them with the request, and
builds against the current workflow bindings and installed UI kit. A changed or
missing candidate requires refresh or restoration; it is never silently replaced.
If a request's outcome is uncertain, **Reconcile request** follows the original
request even if the imported file later changes. The common working view and
ordinary local interface creation remain available when import data is unusable.

Local controlled tests and actual-model workspace verification cover selection,
rebuild, preview, save, chooser reuse, reload and common-view fallback. The
[engineering execution ledger](https://github.com/burhop/wright/blob/dev/specs/083-process-working-interfaces/mechanical-engineering-execution.md)
records the exact build, workflow and retained failures. This does not certify
arbitrary imported interfaces or grant engineering acceptance.

### Reopen after a browser interruption

Opening a saved interface reclaims expired Wright process views in the same
user, workspace and session before allocating another UI host. It revokes their
presentation grants and stops only the corresponding static UI instance when
no valid presentation remains. A late close from an older instance cannot stop
its replacement. Saved interfaces, engineering files and process runs remain
unchanged.

Presentation authority currently lasts eight hours. This cleanup does not
detect a browser crash immediately: an unexpired view can still occupy a slot.
Close unused interface tabs normally to release them sooner. The common view
remains available when the managed-interface limit is reached. This policy does
not close engineering applications or cancel their operations.

### Inspect work from before a correction

In the common working view, **Previous attempts** keeps models, drawings,
measurements and documents from before an automatic correction. Use **Open file**
to inspect them or **Download exact file** to retain the recorded bytes. These
are labelled historical evidence and stay separate from current results, even
when a later correction fails. **Open producing step** returns to the owning
block. Opening or reloading this evidence does not restart the process.

This view requires recorded workspace files with exact byte identities. Live
application documents and unpinned files are not historical snapshots. Changed
or missing files remain errors; Wright does not substitute a newer file.

### Read engineering documents

Use **Open file** beside a result or review attachment. Markdown requirements,
assumptions and inspection plans show formatted headings, lists and tables in the
shared reader. **View source** exposes the original Markdown; **Download exact
file** returns the recorded file unchanged. Larger documents retain a download
fallback. Links and embedded images in Markdown are shown as references; open
related files using their own evidence controls.

On a narrow workspace, select **Surface** to return from Chat to the working view.
Document viewing does not answer a question, approve evidence or resume a run.

### Inspect numerical results

Open a CSV result and expand **View numerical samples**. Choose the horizontal
and vertical columns; choose a value column to color the recorded samples.
The axes show numerical ticks and retain the supplied column names/units. A
field plot has a labeled color scale for its own recorded range. Colors do not
indicate whether a requirement passes or fails; use the linked assessment.

Display labels may be rounded. The exact table, sample tooltips and downloaded
file retain the original values. All supported samples are plotted even when
the table shows only one page. Other coordinates remain in the table; projecting
onto two axes can overlap samples and does not create an interpolated surface.

### Prepare the run

In a compact workspace, **Workspace Files** opens navigation over the document.
Use **Close**, press **Escape**, or click the shaded space beside navigation to
return. Resizing back restores the desktop sidebar preference. Long engineering
labels wrap in the common view; wider saved-interface content can be scrolled
horizontally. These controls preserve the accepted process and recorded run.

Readiness checks the selected tools' known execution permissions as well as
inputs, schemas and configuration. A missing permission identifies the affected
step and blocks start before execution. Existing workspace provider grants remain
the authority; built-in reviewed operations and exact integration-test enrollment
retain their separate scope. This check grants no permission and does not replace
the final dispatch checks or a process's declared human review.

1. Use **Workflows** to create a new blank workflow, or open the intended existing
   file through Workspace Files or **Open workflow** in the editor's file menu.
   File tabs retain the existing editor, diagram and source controls.
   An explicit workflow link selects that source rather than a restored unrelated
   tab. Opening an existing file does not create a missing workflow.
2. Save your edits, then choose **Open working view** to open the same saved
   workflow's input, result and progress interface in a workspace tab. It does
   not select a template or start execution. **Open workflow** returns to the
   authoring view. The editor requires unsaved changes to be saved first.
3. Supply required values, files, images and available provider choices. Run
   preparation freezes these inputs separately from the accepted definition.
   Uploaded images have thumbnails; changes invalidate prior preparation.
4. Check readiness before **Start**. Missing supported-path dependencies block
   start with reasons. Use **Open related item** on a missing-input reason to
   inspect its exact input step. Outputs declared to be produced upstream need
   not exist beforehand. Readiness is not an engineering verdict.
   Required validation checks also qualify their registered reader and evidence
   method against the pinned profile before work starts. Optional checks,
   explicitly excluded checks and human review do not require an automatic
   reader at preparation. This does not evaluate future outputs or accept a
   review. Runtime inspection still checks the actual capability, format and
   exact output; changed availability retains its normal hold/failure behavior.
5. Start deliberately. Follow backend activity and actual tool contributions.
   Inspect outputs, findings and evidence. A declared human review/action/input
   persists waiting state until its exact response is accepted. Unattended
   segments do not invent questions or engineering defaults.

To author a prompt-driven task by hand, add a **Text input**, enter the request,
then choose a configured provider from **MCP servers**. Draw a connection from
the text output to the task's **Prompt** input. The Inspector's **Prompt source**
and **Prompt from** controls offer the same binding. Alternatively, add
**MCP task · choose server later**, then select its
provider in the Inspector. **Refresh servers** rereads the enabled workspace
inventory. An unbound task remains editable but must be bound before running.
Internal Wright file/validation operations remain available to the runtime;
they are not presented as independently configured MCP servers.

### Reuse supplied material before optional research

An MCP task normally requires successful tool-call evidence. For analysis that
can finish from supplied references, explicitly save
`"mcp_completion_policy": "supplied_inputs_or_tools"` in that task's source
settings. This is an opt-in source setting; existing tasks keep
`tool_evidence_required`. Select only tools annotated `readOnlyHint: true` in
`mcp_task_tools`. Unknown or changing tools block readiness, even when no call
is expected. The selected provider must still be available.

The workflow must contain the saved `context.mcp-input-completion` instruction
asset from defaults 1.3.0 or an explicitly reviewed compatible asset. Update
older workflow instructions visibly and save a new revision; changing installed
defaults does not update accepted workflows. Export/import carries the saved
setting and instruction body through the existing workflow bundle.

With sufficient supplied inputs and no executed tool calls, the model may return
`{"status":"completed","response":"...","evidence":[],"completion_basis":"supplied_inputs"}`.
Wright records the completion basis and a digest of the actual composed task
input, alongside its existing request, source, reference and result evidence.
This is analysis of those inputs, not proof of their claims. If a tool runs,
completion still requires successful call numbers; supplied-input completion
cannot conceal failed or uncertain tool outcomes.

This setting cannot replace CAD operations, design checks, application tasks,
tool-produced files or external actions. Required measurements, declared questions,
review, frozen routing and continuation checks retain their existing authority.
Use an ordinary AI task when tools are never needed. PDF reading is a separately
qualified provider capability; a downloaded PDF alone does not establish that its
contents were read.

### Model screenshot to a rendered image

For a workflow whose final deliverable is a realistic image:

1. Connect the design text to the CAD task's **Prompt** input. In its **Exports**,
   choose **Add model image** when the selected provider supports image export.
   The existing Solid Edge provider declares **Image (JPEG)**. Retain any model
   exports needed for engineering review.
2. Add an **AI prompt** or **MCP task** for rendering. Write the rendering
   instructions separately, including the geometry, proportions and features
   to preserve. Choose **Image (PNG)** or **Image (JPEG)** as the response format
   and set the image filename.
3. Draw the CAD image output to that step's **Reference image** input. The image
   is supplied as image content; it does not replace the written instructions.
4. For an **AI prompt**, Wright uses the configured AI connection's native image
   output. The qualified Codex connection accepts the image and text together
   and returns PNG/JPEG; no additional MCP is required. An explicitly selected
   image MCP remains an alternative. Readiness checks the selected path before
   starting, and a changed AI model/configuration invalidates the prepared call.
5. Save, inspect readiness and run. The returned image is the final result;
   the task's textual activity summary remains supporting evidence. Each run
   writes its image under a separate run output directory.

To view a produced image in the editor, choose **Results → Image**, then
**Open plot or image in tab**. The green result card opens the same result
viewer. An unproduced output uses **View output status** and explains the saved
run state, with **Inspect failed step** and **View run details** when applicable.
Expected filenames are not downloadable results. Opening a result resets the
inspector to the top; inspecting status or a saved file does not rerun the process.

A failed run also shows a persistent **Workflow failed** alert above the diagram,
even when Run details is collapsed or the workflow is reopened. **View error
details** opens the full saved error; **Inspect failed step** selects a step only
when the matching run identifies it. An error from a different source version is
labelled as a saved-run error and is not attributed to the current edited blocks.

Image tasks reuse the existing workflow runner, configured AI adapter or MCP
gateway, file storage/verification and result viewer. The native image adapter
uses the installed SDK's provider-side image tool with the resolved default
model; it has no independent executor or job state. Verification checks the exact output path, changed file bytes,
PNG/JPEG header dimensions and recorded hash. It does not establish realistic
appearance or preserved engineering geometry; add an explicit review or suitable
validator for those requirements. A successful authoring walkthrough does not
prove that a particular image provider or CAD export has executed.

The process services own state and permitted actions. Closing or reopening a tab
does not cancel or restart a run. Submission, observed start, completion,
cancellation request and actual outcome remain separate. An unknown external
outcome requires reconciliation rather than another mutation.

The compatibility approval-resume endpoint and working-view actions use the
same task supervisor and canonical continuation records. A disconnected resume
request detaches its observer; retry the same request identity to attach again.
The compatibility response still returns the exact segment's recorded result.
Cancellation may be unavailable during preparation or when the active provider
has no qualified cancellation capability. A runtime shutdown records interruption
and does not establish that a remote operation was cancelled. Recorded uncertain
work is not replayed.

## Create, save and reuse a tailored interface

In the working tab choose **Create or choose interface**. Enter **Interface
title** and **How should this interface help the user?**, then **Create interface**.
The [neutral reference instruction](https://github.com/burhop/wright/blob/dev/examples/process-interfaces/reference-instruction.txt)
is a useful starting point. Ask for a comparison, dashboard or other layout that
helps accomplish this particular job; no lifecycle is mandatory.

Wright invokes its configured coding role and displays generation, binding,
build and bounded correction progress. **Creation details** identifies the job,
revision, resolved model and adapter. If authoring is unavailable, use a saved
interface or the common view while its model/adapter/compiler is configured.

Choose **Open preview** and wait for its loaded observation. Review layout,
keyboard use, missing-data states and exact navigation before **Save interface**
becomes available. Preview grants are read-only. The model supplies frontend
source/bindings; Wright supplies the compiler, isolated host and process bridge.
It does not approve engineering results or create another executor.

Select a **Saved interface** and **Saved revision**, then **Open saved interface**.
Reuse uses the immutable built assets, not new model generation or recompilation.
**Update selected interface** creates a separate checked revision. **Use this
revision** activates an earlier compatible saved revision. Binding changes require
compatibility checks; the common working view remains a fallback.

If a request acknowledgement is lost, use **Reconcile request** for that retained
identity. **Clear local request locator** clears browser bookkeeping, not a
backend job. **Cancel interface creation** concerns authoring only, not the
engineering run. **Refresh job status** reattaches observations.

## Inspect results and history

Use exact result/evidence links and their block/run navigation. Geometry,
toolpaths and numerical views report supported data and parser provenance; they
do not certify a part or analysis. Unknown classification and unavailable
formats remain explicit. Detailed findings and technical diagnostics are available
without turning them into the default engineering explanation.

Older `printDemoRun` links use a bounded read-only recorder adapter. **View saved
result**, **Back to workflow** and saved file tabs retain original states/errors
and artifacts. History has no process/device controls and does not turn a failed
run into a success. Active prototype endpoints/startup/automation have been
retired with exact inactive archives and bounded compatibility evidence.
Unchanged prior-feature integration references remain inventoried debt; the
read-only entry does not qualify a replacement device capability.

## Developer boundaries

| Boundary | Use |
| --- | --- |
| Native workspace authoring | Authenticated scoped process-interface routes; existing host adapter. |
| Generated frontend | `@wright/process-client` and `@wright/ui-kit`, supplied `AppProps`, current snapshot and bounded navigation. |
| Execution and engineering checks | Existing source runtime, gateway, recorder, reviews/actions and 082 validator. |
| Hosting | Wright workspace tabs and managed isolated surfaces; presentation-bound process bridge. |
| Tool capabilities | Existing independent MCP providers and qualified operation contracts. |

Use the [public client](https://github.com/burhop/wright/blob/dev/packages/process_client/README.md),
[UI kit](https://github.com/burhop/wright/blob/dev/packages/ui_kit/README.md) and
[runnable examples](https://github.com/burhop/wright/blob/dev/examples/process-interfaces/README.md). Version-1
client/kit packages are currently private workspace/build resources, not published
npm dependencies. The packaged authoring instructions, public API and reference
template are in `workspace_service.process_interfaces.resources` and are shipped
with the Python package. Compiler readiness is explicit; generation must not
invent package scripts, plugins, backends, shell commands or host launchers.

Installed builds resolve the kit's geometry and Markdown readers from the
explicitly configured toolchain root. The versioned `toolchain.json` includes
`react-markdown` and `remark-gfm`; missing or mismatched libraries make compiler
readiness unavailable. Verify a packaged build outside the source checkout when
adding a shared component dependency. Saved interfaces remain usable without a
compiler. Passive PDF previews require the PDFium and Pillow libraries declared
by `wright-engineering[runtime]`; viewing an existing drawing does not require
the CAD application that produced it.

Generated interfaces receive no native bearer token, global workspace client,
generic tool invocation or agent-authoring authority. MCP App same-server grants
and WebMCP registration remain separate contracts. Required binding mismatches
block save/open; optional absence needs an explicit visible fallback.

### Native API reference

All routes below use `/api/workspace/process-interfaces`. Native reads carry
`session_id`, `path` and `expected_storage_digest`; bodies carry the same source
scope. Existing authentication and workspace/session ownership apply. Use the
native scoped client instead of copying credentials into generated source.

| Route | Responsibility |
| --- | --- |
| `GET /authoring-capabilities` | Current role/model/compiler qualification. |
| `POST /authoring-jobs` | Durable request identity, instruction/title, optional exact UI/base revision. |
| `GET /authoring-jobs/{job_id}` and `/events` | Saved status and bounded progress observation. |
| `POST /authoring-jobs/{job_id}/cancel` | Explicit cancellation of interface creation. |
| `POST /authoring-jobs/{job_id}/preview` | Managed read-only presentation of an exact build. |
| `POST /uis/{ui_id}/revisions/{revision_id}/save` | Save only after exact loaded-preview/build checks. |
| `GET /uis` and `/uis/{ui_id}/revisions` | Scoped saved-interface/revision discovery. |
| `GET /uis/{ui_id}/compatibility` | Exact revision/source/binding compatibility. |
| `POST /uis/{ui_id}/present` | Existing saved build, preparation or exact run attachment. |
| `POST /uis/{ui_id}/activate` | Explicit revision activation/rollback. |
| `GET /uis/{ui_id}/runtime-diagnostics` | Exact UI/revision/surface diagnostics, labelled live or reconciliation state. |
| `POST /presentations/close` | Close only that view. |

The [read-only inspection utility](https://github.com/burhop/wright/blob/dev/examples/process-interfaces/inspect_interface.py)
uses the first and third rows. Other operations should use Wright's controls and
owning clients; their request schemas and capabilities remain authoritative.

The same mount exposes the native process client:

| Route | Responsibility |
| --- | --- |
| `GET /interaction` | Exact accepted-process/run snapshot. |
| `POST /inputs`, `/inputs/upload`, `/readiness` | Declared input publication, immutable preparation and fresh readiness. |
| `POST /runs`, `GET /runs/{run_id}`, `/events` | Durable start, reconciliation and observation; subscription does not execute. |
| `POST /interactions/{checkpoint_id}/response` or `/decision` | Declared exact-subject response/review, server-derived actor. |
| `POST /actions/{action_id}`, `/runs/{run_id}/cancel` | Existing permitted action or explicit cancellation; unknown outcomes are not replayed. |
| `POST /representations/read`, `/navigation` | Exact hash-checked evidence and host navigation, without process mutation. |

See the [versioned interaction contract](https://github.com/burhop/wright/blob/dev/specs/083-process-working-interfaces/contracts/process-interaction.md)
for body fields, limits, errors, presentation grants and currentness.

### Supplied artifacts and external actions

A process may explicitly set `approval_settings.include_supplied_files: true`
for existing fixed artifact approvals to review/hand off connected frozen files
without regenerating them. Default behavior is preserved. Exact source/input/file
identity checks and existing approval/effect authority still apply. This setting
does not make an input a tool-produced output, authorize a printer/supplier,
or extend MCP-operation argument contracts. See the
[runtime contract](https://github.com/burhop/wright/blob/dev/specs/083-process-working-interfaces/contracts/runtime-and-source.md).

### Longer external operations

An independently qualified operation may declare `observation_timeout_seconds`
in its version-1 `wright/operation` metadata, for example `7200` for two hours.
This optional finite budget is separate from submission, status/result calls and
AI decisions. It must be configured and pinned before starting; changing it
requires reviewing the changed binding/policy. The maximum is seven days.
Without the field, existing step/task timeout behavior is preserved.

Wright polls the identified operation through the existing runtime. Acceptance,
observed completion, cancellation and unknown outcome remain distinct facts.
Closing a view does not submit another job; an uncertain action is reconciled.
This requires the provider's qualified observation capabilities and does not
imply universal MCP Tasks or physical-device support. See the
[operation contract](https://github.com/burhop/wright/blob/dev/specs/083-process-working-interfaces/evidence/mcp-operations.md).

## Locally verified proof environment

At the recorded 4 October UTC checkpoint, the owned API8063/UI5246/native-addon19988
accepted connections. These are historical local addresses, not current setup instructions. The documented inspection utility performs two actual scoped
GETs without changing interface/authoring/continuation records. Open the
[current local workspace](http://127.0.0.1:5246/workspace/083-fresh-prompt-055?workflow=canonical&workflowPath=workflows%2Fprinted-replacement-part-mixed-default-071.workflow.wflow)
and choose **Open working view** (called **Use saved process** in the 4 October
evidence). Existing local authentication/session setup is
required. These temporary source-proof services are separate from the historical
installed hosts below and may stop with their owned processes. See
[current operator check](https://github.com/burhop/wright/blob/dev/artifacts/process-interfaces/083/20261004-current-operator-guidance-verified/checked-scope.json).

The full printed demonstration retains mandatory human review and its ordinary
builtin-write readiness limitation. Exact enrolled digital-test authority used
in its proofs is not general public-start permission. Installed saved-view
reuse needs no model/compiler; new authoring requires qualified resources.

The recorded proof used API [localhost:8030](http://127.0.0.1:8030)
and frontend [localhost:5243](http://127.0.0.1:5243). The isolated workspace
is [083-heat-live-005](http://127.0.0.1:5243/workspace/083-heat-live-005).
These addresses are machine-local, may stop with their owned services and are
not a public deployment or a replacement for another user's saved workspace.
The post-pause operator check found both listeners stopped; these are recorded
proof addresses, not a claim that the services are currently available.

This source frontend enables `VITE_WRIGHT_WORKFLOW_RECOVERY`,
`VITE_WRIGHT_WORKFLOW_COMPOSER` and `VITE_WRIGHT_PROCESS_DEFINITION_VIEW`, with
its API proxy target explicitly set. Those build flags describe this checked
environment, not an installed-release guarantee. Evidence:
[workspace acceptance](https://github.com/burhop/wright/blob/dev/specs/083-process-working-interfaces/evidence/workspace-acceptance.md),
[heat proof](https://github.com/burhop/wright/blob/dev/specs/083-process-working-interfaces/evidence/heat-proof.md),
[wheel proof](https://github.com/burhop/wright/blob/dev/specs/083-process-working-interfaces/evidence/printed-proof.md),
and [installed scope](https://github.com/burhop/wright/blob/dev/specs/083-process-working-interfaces/evidence/distribution.md).

### Fresh installed qualification, 2 October

The fresh local installed proof opens at [native Wright home](http://wright.localhost:8032/).
Open home first for its normal native session bootstrap, then open the copied
`083-heat-live-005` workspace and use **Workflows**. Choose either retained wheel
preparation or heat-spreader workflow, then **Use saved process** and
**Create or choose interface**. Previously saved revisions remain usable while
the authoring compiler is unavailable. These views retain their exact waiting
run/review; opening or reloading does not resume engineering work.

The clean Docker proof uses [Docker Wright home](http://wright.localhost:8033/)
with an existing authorized operator session. Its browser fixture supplies that
session; this is not a new login mechanism or a weakening of native loopback
bootstrap. Both environments are copied private qualification workspaces, with
provider autostart disabled. They may stop with their owned services.
See the [native report](https://github.com/burhop/wright/blob/dev/artifacts/process-interfaces/083/20261002-installed-native-workspace-009/workspace-walkthrough/report.html)
and [current Docker qualification record](https://github.com/burhop/wright/blob/dev/specs/083-process-working-interfaces/evidence/installed-docker-reuse.md)
for exact build, capability limits and checked scope. These local candidate
checks do not establish release, full engineering parity or human acceptance.

### Importing an interface into another workspace

A workflow bundle carries the saved interface source and bindings as an inactive
candidate. It carries no trusted build, live run, answers or review authority.
Use the common working view while qualifying local providers and rebuilding the
interface. A local saved view must pass its current binding checks and managed
preview before saving; its availability does not make the engineering process
ready to execute.

The 10 October isolated proof used Wright's native authoring service to adapt the
imported source into a new local UI identity, preview/save it, and request a small
wording update. It verified reload and common fallback, plus a required output
rename that visibly blocked the incompatible UI. Restoring the original source
made the saved view compatible again. This API-driven proof does not establish a
one-click import/rebuild picker or destination engineering execution. See the
illustrated record (local evidence archive; see the retained execution record)
and the [execution ledger](https://github.com/burhop/wright/blob/dev/specs/083-process-working-interfaces/mechanical-engineering-execution.md).
