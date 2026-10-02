# Process working interfaces

Wright offers two views of the same accepted process and durable run: the
flowchart/source editor for building and inspecting, and a common or tailored
working interface for carrying out the job. The process defines its stages and
decisions. A tailored interface changes presentation, not execution.

**Qualification:** Feature 083 is in development on
`codex/083-process-working-interfaces`. Local source-checkout common/tailored
views, actual-model generation/update and saved reuse have evidence. Complete
engineering parity, vendor-code retirement, installed native/Docker browser
acceptance and the completion audit remain pending. This guide is not a release
or engineering-acceptance claim. Consult the
[task record](../../specs/083-process-working-interfaces/tasks.md).

## Open and prepare a process

1. Open the intended workflow file in its Wright workspace. The **Workflows**
   control and file tabs retain the existing editor, diagram and source controls.
   An explicit workflow link selects that source rather than a restored unrelated
   tab. Opening an existing file does not create a missing workflow.
2. Choose **Use saved process** to open its working view in a workspace tab.
   **Open workflow** returns to the authoring view.
3. Supply required values, files, images and available provider choices. Run
   preparation freezes these inputs separately from the accepted definition.
   Uploaded images have thumbnails; changes invalidate prior preparation.
4. Check readiness before **Start**. Missing supported-path dependencies block
   start with reasons. Outputs declared to be produced upstream need not exist
   beforehand. Readiness is not an engineering verdict.
5. Start deliberately. Follow backend activity and actual tool contributions.
   Inspect outputs, findings and evidence. A declared human review/action/input
   persists waiting state until its exact response is accepted. Unattended
   segments do not invent questions or engineering defaults.

The process services own state and permitted actions. Closing or reopening a tab
does not cancel or restart a run. Submission, observed start, completion,
cancellation request and actual outcome remain separate. An unknown external
outcome requires reconciliation rather than another mutation.

## Create, save and reuse a tailored interface

In the working tab choose **Create or choose interface**. Enter **Interface
title** and **How should this interface help the user?**, then **Create interface**.
The [neutral reference instruction](../../examples/process-interfaces/reference-instruction.txt)
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
run into a success. Remaining prototype endpoints/startup/automation are still
migration debt; the read-only entry alone does not prove their retirement.

## Developer boundaries

| Boundary | Use |
| --- | --- |
| Native workspace authoring | Authenticated scoped process-interface routes; existing host adapter. |
| Generated frontend | `@wright/process-client` and `@wright/ui-kit`, supplied `AppProps`, current snapshot and bounded navigation. |
| Execution and engineering checks | Existing source runtime, gateway, recorder, reviews/actions and 082 validator. |
| Hosting | Wright workspace tabs and managed isolated surfaces; presentation-bound process bridge. |
| Tool capabilities | Existing independent MCP providers and qualified operation contracts. |

Use the [public client](../../packages/process_client/README.md),
[UI kit](../../packages/ui_kit/README.md) and
[runnable examples](../../examples/process-interfaces/README.md). Version-1
client/kit packages are currently private workspace/build resources, not published
npm dependencies. The packaged authoring instructions, public API and reference
template are in `workspace_service.process_interfaces.resources` and are shipped
with the Python package. Compiler readiness is explicit; generation must not
invent package scripts, plugins, backends, shell commands or host launchers.

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
| `POST /authoring-jobs/{job_id}/preview` | Managed read-only presentation of an exact build. |
| `POST /uis/{ui_id}/revisions/{revision_id}/save` | Save only after exact loaded-preview/build checks. |
| `GET /uis` and `/uis/{ui_id}/revisions` | Scoped saved-interface/revision discovery. |
| `GET /uis/{ui_id}/compatibility` | Exact revision/source/binding compatibility. |
| `POST /uis/{ui_id}/present` | Existing saved build, preparation or exact run attachment. |
| `POST /uis/{ui_id}/activate` | Explicit revision activation/rollback. |
| `GET /uis/{ui_id}/runtime-diagnostics` | Exact UI/revision/surface diagnostics, labelled live or reconciliation state. |
| `POST /presentations/close` | Close only that view. |

The [read-only inspection utility](../../examples/process-interfaces/inspect_interface.py)
uses the first and third rows. Other operations should use Wright's controls and
owning clients; their request schemas and capabilities remain authoritative.

### Supplied artifacts and external actions

A process may explicitly set `approval_settings.include_supplied_files: true`
for existing fixed artifact approvals to review/hand off connected frozen files
without regenerating them. Default behavior is preserved. Exact source/input/file
identity checks and existing approval/effect authority still apply. This setting
does not make an input a tool-produced output, authorize a printer/supplier,
or extend MCP-operation argument contracts. See the
[runtime contract](../../specs/083-process-working-interfaces/contracts/runtime-and-source.md).

## Locally verified proof environment

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
[workspace acceptance](../../specs/083-process-working-interfaces/evidence/workspace-acceptance.md),
[heat proof](../../specs/083-process-working-interfaces/evidence/heat-proof.md),
[wheel proof](../../specs/083-process-working-interfaces/evidence/printed-proof.md),
and [installed scope](../../specs/083-process-working-interfaces/evidence/distribution.md).
