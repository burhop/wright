# Explicit run paths — controlled canonical runtime proof

Source checkpoint `0248e68e` plus the eight owning implementation/test files
hashed in `checked-scope.json`. Branch `codex/083-process-working-interfaces`.
This is local shared-runtime verification, not live engineering, browser,
installed-distribution or human acceptance. No feature task is closed here.

## Change and checked behavior

Reusable sources previously used fixed output paths that could overwrite earlier
engineering evidence. `wright.run-path/1` explicitly resolves declared paths with
the backend run ID before tool checks and reserves fresh directories at execution.
It keeps the existing compiler, executor, supervisor and continuation owners.
See the [contract](../../../../specs/083-process-working-interfaces/contracts/runtime-and-source.md).

- Two controlled source runs share one accepted process and frozen inputs, use
  separate directories and preserve first-run bytes. A start retry does not replay.
- Connected MCP file-template text resolves before schema validation and dispatch.
  Readiness calls no engineering tool and creates no output directory. Both
  dispatches receive their own run ID; the model callback is never invoked.
- A declared-input checkpoint survives owner reopen and resumes in the same
  directory. Changed frozen template bytes block before another call.
- An exactly enrolled local-review test resumes on its original run and retains
  `integration_test:campaign` actor attribution. Repeated resume does not replay.
- Raw and resolved template hashes remain distinct; checkpoint encoding retains
  both. Resolved content, rather than raw file size, governs the inline budget.
- Unsafe IDs/paths, missing/unsupported declarations, unknown tokens, templated
  keys/authority/configuration, opaque artifact consumers, directory collisions
  and missing continuation directories fail. Literal legacy sources still work.

## Results and limits

The current 15-file suite reports **237 passed / one skipped / 44.28 seconds**.
The new run-path file contains 29 parameterized cases. Ruff passes all eight
owning files. The skip is an existing checkpoint-file symlink test: Windows lacks
the symlink privilege (`WinError 1314`); this host does not establish that test.
Earlier overlapping subsets remain private and are not added to the current count.
Attempt 004 ran no tests because a requested filename did not exist; its XML/log
remain under `retained-setup-failure/`.

Fresh `preservation.json` checks eighteen archived prototype files and protected
campaign/context/unrelated prototype bytes. Verification handles 1282/39455 are
terminal. Existing API/provider/UI services were not revalidated by this proof.

A declared path is not a provider filesystem sandbox. Every provider write, job
name or native resource still needs explicit binding and qualification. Printed
and Heat examples have not adopted the contract yet. Source/UI compatibility and
actual saved-interface repeat-run proof remain open, as do T045/T047/T053. No
protected review, physical effect, push, merge or release occurred.

## Reproduce

Use a fresh owned proof root and the existing repository environment. These
commands must not replace the retained test directory:

```powershell
New-Item -ItemType Directory -Path '.local-run/process-interfaces-083/run-path-reproduction'
$runPathSuites = @('test_workflow_run_paths', 'test_workflow_source_execution', 'test_workflow_mcp_execution', 'test_workflow_execution_continuation', 'test_workflow_approval_execution', 'test_workflow_approval_resume', 'test_workflow_checkpoint_file_identity', 'test_workflow_binary_file_consumers', 'test_workflow_ai_file_dependencies', 'test_process_run_supervisor', 'test_process_interface_continuation', 'test_process_input_supervision', 'test_process_input_execution_overlay', 'test_process_input_mcp_values', 'test_process_preparation_service') | ForEach-Object { 'packages/workspace_service/tests/' + $_ + '.py' }
.venv/Scripts/python.exe -m pytest @runPathSuites -q -rs --basetemp=.local-run/process-interfaces-083/run-path-reproduction/tmp -o cache_dir=.local-run/process-interfaces-083/run-path-reproduction/cache --junitxml=.local-run/process-interfaces-083/run-path-reproduction/results.xml
.venv/Scripts/python.exe -m ruff check packages/workspace_service/src/workspace_service/workflow_run_paths.py packages/workspace_service/src/workspace_service/workflow_source_execution.py packages/workspace_service/src/workspace_service/workflow_run_preparation.py packages/workspace_service/src/workspace_service/workflow_references.py packages/workspace_service/src/workspace_service/workflow_execution_continuation.py packages/workspace_service/src/workspace_service/workflow_approval_execution.py packages/workspace_service/tests/test_workflow_run_paths.py packages/workspace_service/tests/test_workflow_approval_execution.py
```
