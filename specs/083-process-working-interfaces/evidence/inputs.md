# Immutable inputs and readiness — T009, T011, T012

Date: 2026-09-30. Branch: `codex/083-process-working-interfaces`.
This is contract/service/executor regression evidence. It does not establish
served UI, actual model generation, live engineering MCP qualification or acceptance.

## Implemented

- Source defaults and supplied run values share one bounded conversion layer.
  Accepted source bytes are unchanged. Input IDs, values, file hashes, provider
  revisions, schema and timestamps are retained in immutable snapshots.
- Native JSON types remain intact for tool arguments and durable continuation.
  Only LLM prompt/reference rendering converts typed values to canonical JSON.
  An explicit false/null default is distinguishable from an absent default.
- Missing required inputs block preparation, including a choice connected only
  to a later stage. Upstream-produced results are classified separately and need
  not exist before the run. Optional absence removes only its input references
  from the prepared plan, without changing the accepted definition or adding
  synthetic text. Required consumer sockets cannot be weakened by an optional label.
- Files use the existing confined workspace reader and `WorkflowReference`.
  Hashes are checked on preparation and requalification. Text tool arguments use
  actual contents. Images retain their existing typed reference treatment.
- Configured provider choices use the existing gateway/runtime. Only qualified
  read-only tools without a mutation approval requirement can provide choices.
  Schema, binding, actual option IDs/values and resource revision are checked.
  Expired, future-dated or changed selections cannot qualify. The projection
  exposes observed/expiry timestamps so clients need not invent them.
- The service owns `set_inputs`, `check_readiness` and preparation snapshots.
  Reading source defaults is stateless; `set_inputs` persists a preparation before
  start. Existing recorded-run attachment keeps its original receipt. A caller
  cannot supply a replacement preparation while attaching a recorded run.
- Readiness invokes existing authorized source preparation, including template,
  tool schema, validation profile, CAD/application and path qualification. It
  closes any opened runtime and never executes generation or engineering stages.
  Ready is a current assessment; start must recheck it through the execution owner.
- Known connected MCP arguments now undergo preflight before any stage executes.
  Whole native argument objects and scalar types are preserved. Unknown upstream
  values remain pending and undergo full validation at actual invocation.
- Source-default provenance is verified rather than accepted from a label.
  Version-1 integration grants remain limited to their exact source defaults and
  staged file hashes. New arbitrary overlays/provider choices require explicit
  enrollment support in the later checkpoint work; old grants cannot acquire it.

## Accepted-source input metadata

Optional `settings.interaction_input` on a canonical `input` block:

```json
{
  "version": 1,
  "value_schema": {"type": "integer", "minimum": 1, "maximum": 250},
  "required": true,
  "unit": "mm",
  "default": 100
}
```

`default` is used only when explicitly present. Existing nonempty `input_text`
and existing `workspace_file` defaults retain their meaning. File inputs are
identified by their declared file/image ports or workspace-file settings; file
defaults use an exact workspace path, rather than an arbitrary inline object.
Units/frame are retained and are never silently converted.

A configured option source instead supplies `option_source` with exact
`binding_id`, `server_id`, `tool_name`, `schema_digest`, bounded `arguments` and
JSON pointers for the options list, ID, title and value. An optional resource
pointer contributes the actual provider revision. Defaults require an exact
`default_option_id`. Freshness is bounded to 1–300 seconds (default 30); reads
have a bounded timeout. This is generic provider data, with no printer protocol.

Unsupported source/schema semantics return an explicit actionable category.
Declared human-response barriers remain T022–T024 work; the current compiler does
not manufacture a question or classify unsupported barriers as ready.

## Verification

New known-value, preparation-service, authority and identity tests were observed
failing before the missing implementation was added. Existing fixture filenames
were corrected to match their JSON output format; no production gate was weakened.

Combined regression command from the repository root, Python 3.13.5:

```powershell
.venv/Scripts/python.exe -m pytest packages/core/tests/test_process_interface_contracts.py packages/core/tests/test_process_validation.py packages/data_vault/tests/test_process_interface_migrations.py packages/data_vault/tests/test_process_run_identity_queries.py packages/data_vault/tests/test_migrations.py packages/data_vault/tests/test_workflow_continuation_repository.py packages/data_vault/tests/test_process_validation_repository.py packages/workspace_service/tests/test_process_interface_service_boundaries.py packages/workspace_service/tests/test_process_interaction_projection.py packages/workspace_service/tests/test_process_interaction_pages.py packages/workspace_service/tests/test_process_interaction_owners.py packages/workspace_service/tests/test_process_recorded_run_read.py packages/workspace_service/tests/test_process_approval_inspection.py packages/workspace_service/tests/test_workspace_service.py packages/workspace_service/tests/test_workflow_execution_snapshot.py packages/workspace_service/tests/test_workflow_execution_continuation.py packages/workspace_service/tests/test_workflow_approval_execution.py packages/workspace_service/tests/test_workflow_artifact_review.py packages/workspace_service/tests/test_process_input_readiness.py packages/workspace_service/tests/test_process_input_execution_overlay.py packages/workspace_service/tests/test_process_input_mcp_values.py packages/workspace_service/tests/test_process_preparation_service.py packages/workspace_service/tests/test_workflow_mcp_execution.py packages/workspace_service/tests/test_workflow_integration_policy.py -q -p no:cacheprovider --tb=short --basetemp=C:/Users/markb/.codex/visualizations/2026/09/24/01a0d4b8-b5fa-79d0-8e8b-fc78c3dfd056/process-interfaces-083-tests/input-readiness-regressions-final
```

Result: **354 passed, one existing host symlink skip, 38.13 seconds**.

Source/CAD/application regressions:

```powershell
.venv/Scripts/python.exe -m pytest packages/workspace_service/tests/test_workflow_source_execution.py packages/workspace_service/tests/test_workflow_cad.py packages/workspace_service/tests/test_workflow_application_task.py packages/workspace_service/tests/test_workflow_application_exports.py -q -p no:cacheprovider --tb=short --basetemp=C:/Users/markb/.codex/visualizations/2026/09/24/01a0d4b8-b5fa-79d0-8e8b-fc78c3dfd056/process-interfaces-083-tests/input-source-regressions-1
```

Result: **75 passed, 1.61 seconds**.

After adding public choice freshness fields, regenerated schema fixture and
constructing a choice using those actual fields:

```powershell
.venv/Scripts/python.exe -m pytest packages/core/tests/test_process_interface_contracts.py packages/workspace_service/tests/test_process_input_readiness.py packages/workspace_service/tests/test_process_preparation_service.py packages/workspace_service/tests/test_process_input_execution_overlay.py -q -p no:cacheprovider --tb=short --basetemp=.local-run/process-interfaces-083/pytest/public-option-freshness-green
```

Result: **78 passed, 1.28 seconds**. Test handles were polled to completion.

Ruff check and formatting check pass for all 14 changed/new Python modules.
The owned diff has no whitespace errors. All 11 preserved runtime/prototype
file hashes and the three protected campaign/review/binding hashes still match
the pre-implementation baseline. No service or test process is left running by
this increment.

## Remaining

Thin authenticated API (T010), backend-owned run lifetime/start/events/cancel
(T013–T016), declared responses, client/kit/common tabs, actual Wright model UI
authoring, both live engineering proofs, migration and installed distribution
checks remain required. No milestone completion, engineering acceptance, physical
dispatch or publication is implied by these fixture/service regressions.
