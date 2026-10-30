# Explicit saved-response handoff — 23 October 2026

Status: implemented in the local working tree; controlled checks passed. Native
installation, accepted-source adoption, real provider execution and engineering
acceptance remain separate. This change does not authorize those actions.

The customer readiness gap was a separate `write_text_document` call used only
to copy a successful slicer response. Its private integration grant was not a
customer setup route. The source report also requested integration-only
`inspect_file` calls despite already having declared upstream JSON references.

## Shared mechanism and compatibility

`saved_response_file_port` explicitly names one declared `workspace_file` output
on an ordinary response-producing task. It requires `save_output: true` and
`file_policy: publish_indexed` or `publish_overwrite`. Both use the existing
`save_response`, workspace file storage, file result, validator registration and
continuation owners. No new runner, gateway permission, provider adapter or
runtime prompt is introduced.

Publication follows successful response/expected-file verification and precedes
dependent execution and validator subject registration. The response file has
its own exact task/port/run/path/size/hash identity, separate from provider-created
files and textual summaries. The actual indexed path is retained; overwrite
publication requires the existing reserved v1 run path. Existing policies retain
their timing. Publication is not supported on automatic correction, application,
native-image, validator or human/action producers in this bounded version.

The compiler rejects missing/wrong ports, mixed provider/response mappings,
disabled saving, incompatible policies, unsafe/mismatched output names, output
collisions (including indexed-name families and directory/file aliases), and
unscoped overwrite. Existing continuation verification checks retained bytes and
source identity; successful continuation reuses the receipt without publishing
again or replaying the tool.

The predecessor compiler from commit
`3e18db6b4943466e34a6e3ca6768e5013d5377a5` rejected both exact MCP and ordinary AI
publication sources with `WORKFLOW_NOT_READY` at its policy check. The current
compiler accepted them. Exact controlled sources, old compiler SHA256 and
outcomes are retained in
`artifacts/first-contact/084/response-publication/old-runtime-rejection.json`.
This is an actual old-source compiler control, not a claim about every historical
release. UI scalar source parsing remains compatible; the editor displays the
new policy and port while requiring coherent source editing of the binding.

## Recipe change and verification

The Printed02 Orca recipe removes two private writer calls and directly connects
each published `slice-provider-response.json` to its inspector, comparison and
review. Native result/profile/package identity and every original/derived check
remain intact. The source report uses ordinary AI with original requirements,
construction/repair results and exact slice evidence, toolpath summary and
orientation comparison JSON references. Its staged version-2 instruction body is
tested for exact equality to the generated prompt, bounded inline reference
handling and explicit unverified engineering acceptance. Orca preparation now
works without a `files_server` binding or private file-tool definitions. Legacy
wheel/default preparation is unchanged. The existing synthetic transfer remains
an explicit test-only boundary.

Affected regression command:

```sh
/tmp/wright084-quality-venv/bin/python -m pytest \
  packages/workspace_service/tests/test_workflow_saved_response_files.py \
  packages/workspace_service/tests/test_workflow_source_execution.py \
  packages/workspace_service/tests/test_workflow_deterministic_files.py \
  packages/workspace_service/tests/test_workflow_ai_named_files.py \
  packages/workspace_service/tests/test_workflow_ai_file_dependencies.py \
  packages/workspace_service/tests/test_workflow_execution_continuation.py \
  packages/workspace_service/tests/test_workflow_run_paths.py \
  tests/test_process_interface_examples.py tests/test_orca_preparation.py -q
```

Result: **300 passed in 6.20 seconds**, including 37 new publication controls.
After excluding the empty default port from the textual-result identity set,
the final focused publication suite again passed: **37 passed in 0.80 seconds**.
The existing thermal sizing basis supplies the substantially different ordinary
AI handoff proof: original case inputs/instructions, controlled model response,
actual persisted bytes and downstream hash-bound reference. This is a transport
test, not a thermal solver run or new engineering qualification. Mixed native
file/response subjects, provider failures, storage failures, stale expected files,
indexed allocation, path mismatch and restart/tampering have explicit controls.
Ruff and `git diff --check` pass for the owned changes. Sandbox thread wakeups
stalled even a minimal `asyncio.to_thread` control; affected tests ran outside the
sandbox with no live providers. Stalled owned processes were terminated.

Independent backend/recipe review found no remaining blocker. Independent
frontend review corrected its fixture to the exact `wright.run-path/1` string
and found a missing `configuredOutputs` mapping for the new file port. The
existing output-contract owner now maps its filename/format; five source/form
tests cover connected output retargeting/removal. The updated frontend diff was
reviewed with no remaining finding. Its owning agent records final frontend
test/typecheck results separately.
