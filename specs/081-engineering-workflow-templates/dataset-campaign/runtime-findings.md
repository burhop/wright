# Dataset campaign runtime findings

Reviewed 2026-09-12 against the current feature-081 checkout and the running local API at `http://127.0.0.1:8000`. This is a read-only runtime assessment; the requests below describe the existing API rather than a completed campaign integration.

## Current execution boundary

The ten packaged examples are reference definitions. None currently qualifies as a runnable end-to-end campaign process. Live `GET /api/workspace/workflow-source-templates` returned `setup_required` for the three flagship templates and `reference` for the other seven.

The run endpoint checks the instance's template origin before compiling and returns `WORKFLOW_TEMPLATE_SETUP_REQUIRED` unless readiness is `ready` or `verified`. The readiness service currently reads the packaged catalog state directly. An installed MCP server or a successful tool-discovery probe does not satisfy that check.

Code references:

- `apps/api/src/api/routers/workspace.py:1315` — canonical source run endpoint and the template readiness gate.
- `packages/workspace_service/src/workspace_service/engineering_workflow_template_service.py:83` — static catalog-derived readiness.
- `packages/workspace_service/src/workspace_service/engineering_workflow_templates/catalog.yaml:1` — declared integrations, outputs, and blocking reasons.
- `specs/081-engineering-workflow-templates/tasks.md:96` — remaining flagship qualification and complete-definition tasks; follow-on work begins at line 134.

Several templates use `performed_by: configured_tool` or `ai_then_engineer` without a supported execution configuration. `tool: null` alone is not the problem: executable MCP blocks also use a null semantic `tool` field and bind through settings. The missing fields are principally `authoring_template`, selected MCP server/tool/schema or MCP task configuration, typed connected outputs, saved-output/expected-file paths, and accepted prompt/review execution forms. The compiler requires these in `workflow_source_execution.py:487` and `workflow_source_execution.py:564`.

Do not remove instance provenance, force readiness to verified, invoke tools outside the workflow and attribute their files to a process, or replace engineering outputs with generated summaries to increase campaign counters.

## Existing API sequence

All example requests use placeholders. Read actual digests, revisions, IDs, and selected tools from responses; do not reuse illustrative values as execution authority.

1. Read the ten-item list with `GET /api/workspace/workflow-source-templates`.
2. Read details with `GET /api/workspace/workflow-source-templates/printed-replacement-part`. The current detail response wraps metadata/source in `template`.
3. Create a separate canonical instance for each dataset with `POST /api/workspace/workflow-source-templates/printed-replacement-part/instances`:

```json
{
  "session_id": "<workspace-session>",
  "template_version": "1.0.0",
  "expected_source_digest": "<template.source_digest>",
  "workflow_path": "workflows/dataset-print-01.workflow.wflow",
  "request_id": "campaign-print-01-instance-v1"
}
```

An instance response supplies `storage_revision`, `storage_digest`, `definition_revision`, `source`, layout, new workflow ID, and provenance. The current template-instance path schema permits a single filename directly under `workflows/`, rather than nested dataset directories. Creation is idempotent only for the same request ID and exact request. Template seed files are copied to a unique input directory and verified on retries.

4. Stage user-provided input documents through existing workspace file operations, or a workspace-confined campaign importer. The text save API is `PUT /api/workspace/files/content`:

```json
{
  "session_id": "<workspace-session>",
  "path": "inputs/campaign/print-01/prompt.md",
  "content": "Please make a replacement knob from my attached sketch..."
}
```

Use `POST /api/workspace/files` with `session_id`, `path`, and `type` (`directory` or `file`) where an explicit create is required. Images use multipart `POST /api/workspace/workflow-sources/images?session_id=<workspace-session>` with a `file` field; the response gives the actual workspace-relative image path. This image endpoint reads at most 4 MiB plus one overflow byte.

5. Bind dataset inputs into the saved canonical definition through canonical authoring commands, preserving its template origin and typed connections. Save via `PUT /api/workspace/workflow-sources`:

```json
{
  "session_id": "<workspace-session>",
  "path": "workflows/dataset-print-01.workflow.wflow",
  "expected_storage_revision": 1,
  "expected_storage_digest": "<latest storage digest>",
  "semantic_change_validated": true,
  "source": "<updated, parsed canonical source>"
}
```

The `semantic_change_validated` flag must reflect actual canonical validation. Do not set it to pretend arbitrary text was validated. Include layout and its revision only when changing layout. Read a saved definition with `GET /api/workspace/workflow-sources?session_id=<workspace-session>&path=<workflow-path>`.

6. Discover enabled tool identities/schemas with `GET /api/workspace/workflow-sources/tools?session_id=<workspace-session>`. This does not install or qualify a tool.
7. Start a real workflow with `POST /api/workspace/workflow-sources/run`:

```json
{
  "session_id": "<workspace-session>",
  "path": "workflows/dataset-print-01.workflow.wflow",
  "expected_storage_digest": "<digest of exact saved dataset-bound source>"
}
```

Use `Accept: application/x-ndjson` for actual `run_started`, `step_started`, `tool_started`, `output_saved`, `result_ready`, checkpoint, and terminal events. Retain the stream and durable run-log path as evidence. The current endpoint executes within its HTTP request; an NDJSON disconnect cancels the producer after a bounded evidence flush. An unattended runner therefore needs a stable connection, polling-based recovery, and eventual decoupled durable job execution if it must survive client restarts without cancellation.

8. Inspect persisted runs through `GET /api/workspace/workflow-sources/runs?session_id=<workspace-session>&path=<workflow-path>&latest_only=false`. Read individual run JSON and artifacts with `GET /api/workspace/files/content?session_id=<workspace-session>&path=<workspace-relative-path>`. Binary responses contain file bytes; text responses are JSON with a `content` string. Decode that string before hashing text artifacts.

Schemas and routes: `apps/api/src/api/schemas/workspace.py:137`, `:186`, `:216`, `:309`; `apps/api/src/api/routers/workspace.py:968`, `:1027`, `:1088`, `:1195`, `:3276`.

## How inputs actually reach a task

`WorkflowSourceRunRequest` accepts only session, path, and source digest. It has no runtime `inputs`, dataset manifest, or approval-mode field. `prepare_prompt_workflow` reads all inputs from saved input-block settings (`workflow_source_execution.py:922`, `:1016`):

- Typed/pasted text: `settings.input_text`, nonempty, at most 1 MiB.
- Uploaded/staged file: `settings.input_mode: workspace-file` and `settings.workspace_file` pointing inside the workspace.
- Image classification comes from an output port with `kind: reference_images`; task input connections must carry it as image reference material.
- Profile, business context, standards, machine capability, prompt, and images need explicit input blocks/connections or an explicitly referenced assembled context document. Merely copying a folder does not provide its contents to a workflow.

Current document references support nonempty UTF-8 text, Markdown, HTML, JSON and other text formats. PDF/DOCX binaries need an explicit ingestion/import adapter before they can serve as prompt document context. Opaque binary files can pass only to supported application imports when not also consumed as prompt text. Preserve original uploads and separately retain extracted text/provenance when that adapter is added.

Current image decoding supports PNG, JPEG, GIF, and WebP with matching magic bytes (`workflow_references.py:58`). The packaged printed-part reference is SVG, so that starter input is not yet accepted by the image execution path. Dataset authors can provide a raster sketch/concept plus an editable SVG source; only the supported raster file should be bound to the current image port. Do not claim that an SVG-only pack has proven image ingestion.

## Output evidence and structural audits

`record_workflow_run` publishes a workspace run JSON before `run_started` and checkpoints each event (`workflow_run_record.py:275`, `:323`). Files live at `runs/<workflow-slug>/<timestamp>-<id>.json`. The response includes `run_id`, `run_log_path`, `status`, `outputs`, and typed `results`. Each output can supply `output_path`, `output_bytes`, format, and SHA-256. Typed results contain workspace-file representations, with additional files under `exports`.

The campaign collector should recursively collect only recorded workspace-file representations and recorded outputs, resolve every path inside that run's workspace, copy into `output/<dataset-id>/<attempt-id>/`, and retain an artifact manifest mapping original path to copy, size, hash, run ID, task ID, role, and source/dataset digests. A private absolute host path is unnecessary in the portable report.

`workflow_references.py:20` already offers a narrow structural check for expected tool-created files: existence, regular file, nonempty, size no more than 100 MiB, and changed timestamp/size from the pre-task snapshot, then SHA-256. This does not establish engineering validity. Unique per-attempt workspace/output roots make stale-file reuse easier to exclude. Campaign-only output expectations must not erase safety or existing workflow assertions.

Run logs, failure messages, manifests, model prose claiming a CAD file exists, empty files, and copied input files do not satisfy required engineering output roles. Keep diagnostics under a separate diagnostics/evidence directory. A partial run may retain real partial artifacts without raising the completed-with-files counter.

## Approvals: current behavior and required changes

There are currently two approval mechanisms:

1. Terminal artifact review (`workflow_source_execution.py:450`, `:760`). It permits exactly one terminal Engineer review after AI document tasks. MCP/CAD continuation or a nonterminal review is explicitly rejected. Read with `GET /api/workspace/workflow-sources/reviews/{review_id}?session_id=...`; decide with `POST /api/workspace/workflow-sources/reviews/{review_id}/decision` using session ID, exact `expected_package_digest`, `approved` or `changes_requested`, and reason. An approved terminal document review changes its reported status but does not run a later task.
2. Exact external-action checkpoint (`workflow_source_execution.py:378`, `:1810`). Execution stops at the checkpoint, saves completed IDs and artifact/input references, and returns `awaiting_approval`. Supported action kinds are `printer_transfer`, `supplier_upload_preview`, and `cart_quote_handoff`.

Read an external checkpoint with `GET /api/workspace/workflow-runs/<run-id>/approvals/<checkpoint-id>?session_id=...`. Decision request:

```json
{
  "session_id": "<workspace-session>",
  "subject_digest": "<current checkpoint digest>",
  "decision": "approved",
  "reason": "<human decision or explicit recorded integration-test policy>",
  "request_id": "campaign-print-01-approval-001"
}
```

Send it to `POST /api/workspace/workflow-runs/<run-id>/approvals/<checkpoint-id>/decisions`. The current endpoint sets actor to `local_workspace_user`, even for a script. It does not yet expose a distinct automatic-test actor/mode, so scripted decisions should not masquerade as reviewed human decisions. The schema accepts `request_id`, but the current decision service relies on state/actor/reason equivalence instead of persisting this ID.

The current `POST /api/workspace/workflow-runs/<run-id>/resume` body contains session ID, checkpoint ID, exact subject digest, and request ID. **This endpoint currently consumes dispatch authority and records an event; it does not call a tool, reload and continue the execution plan, or execute subsequent steps.** It stores `not_dispatched` and projects `awaiting_external_outcome`. Do not call it speculatively as a runner resume: this consumes an approval without making progress.

`POST /api/workspace/workflow-runs/<run-id>/approvals/<checkpoint-id>/reconcile` records external outcome/evidence. Current projection can set `completed` when an action is marked `dispatched`, regardless of remaining definition steps (`workflow_run_record.py:514`). A campaign must verify all required steps and output roles rather than count that status alone. The two-checkpoint sheet-metal process makes this particularly relevant. Never manufacture a reconciliation receipt to advance a run.

Required implementation for the long-running goal:

- Add persisted `manual` / `auto` policy to a run or campaign. Normal product runs retain manual approval; this explicitly authorized integration campaign defaults to auto. Use an attributed `integration_test` actor and carry policy identity, reason, exact subject digest and decision time in evidence and UI.
- Permit auto approval of the user's authorized integration-test review steps, with exact subject checks. Keep it distinct from engineering-content validation.
- Use configured isolated test destinations for printer/supplier effects and clearly label simulator evidence. Physical printer transfer/start, real supplier upload/order/payment, and publication still require their exact authority and configuration; broad automatic-test approval must not silently acquire a real destination.
- Implement durable continuation with immutable plan/source/input snapshots, saved result mappings, next step, policy, one-shot action state, and resource lease handling. Resume must verify digests, continue after the approved checkpoint, and never rerun completed mutations.
- Preserve pending manual review and blocked unavailable external destinations while continuing other independent scenarios. Retry only known-safe pre-dispatch failures; interrupted or ambiguous dispatched mutations require read-only reconciliation.
- Add manual versus auto tests, restart recovery, stale digest, duplicate decision/resume, unknown outcome, and a multi-checkpoint process test before claiming the runner is unattended.

Relevant code: `apps/api/src/api/routers/workspace.py:1671`, `:1691`, `:1720`, `:1756`; `packages/workspace_service/src/workspace_service/workflow_external_actions.py:118`, `:219`; `packages/workspace_service/src/workspace_service/workflow_run_record.py:472`.

## Campaign and dashboard counting model

The initial campaign starts at `datasets_created=0`, `combinations_run=0`, `completed_with_outputs=0`, `valid_data=0`. Dataset registration then raises only the first count as complete input packs pass their structural manifest audit. A rejected endpoint call, catalog preflight, disconnected attempt that never entered runtime, or fixture-playback result must not raise `combinations_run`.

Use the exact 30 dataset/process pairs as identities and separate numbered attempts:

- `datasets_created`: distinct complete registered dataset manifests, bounded 0–30.
- `combinations_run`: distinct pairs with durable real `run_started` evidence; retrying a pair does not increment again.
- `completed_with_outputs`: distinct pairs whose real run completed all required process steps and whose current expected output roles passed file-presence/size/hash/lineage checks, bounded by combinations run. Automatic approvals and labeled simulated external receipts must be visible, not promoted to physical execution evidence.
- `valid_data`: exactly zero while semantic engineering validation is disabled. File presence is not this metric.

Persist an append-only UTC event stream with sequence, campaign ID, dataset ID, attempt ID, event kind, workflow/dataset/source digests, run/log identity, evidence references, and counters. Apply state change and derived counter snapshot transactionally; expose revision/sequence on dashboard responses. Render all four lines from a true zero baseline, with a table showing latest state, missing files, and blocker per pair. Keep distinct attempts, pending approvals, runtime failures, startup failures, and qualification blockers in secondary diagnostics.

Recommended smallest honest setup is the offline input-pack registrar, immutable manifests, empty output destinations, structural file auditor, SQLite state/history, a live polling dashboard, and a documented live adapter contract. This setup may report 30 datasets and 0 runs today. The subsequent goal must implement the actual canonical runtime gaps above, then execute available pairs and keep unready pairs visibly blocked rather than filling their output folders with substitutes.
