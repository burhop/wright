# Run-path tokens in authority configuration

The existing `wright.run-path/1` binding now rejects reserved Wright tokens in
approval, validation, native application/document and human-interaction
configuration on every step. Undeclared steps and legacy processes cannot defer
these unsupported tokens until an operation or review fails. Literal legacy
configuration and the existing closed templated task fields retain their behavior.

Fifteen added parameterized cases cover five dictionaries in three declaration
contexts. The focused suite passes 44 cases; seven affected suites pass 108.
These counts overlap. Ruff passes both owning files. Exact XML, source hashes
and fresh protected archive/campaign/context checks are retained here.

This is controlled regression evidence. It does not qualify an installed build,
live MCP, UI, provider write boundary or engineering result. The active Heat API
was loaded from a4cfc474 before this correction and contains no affected tokens;
its independent digital proof must not be reported as a live test of this change.

## Reproduce

From the repo, use a fresh temporary/cache directory and run:

```powershell
.venv/Scripts/python.exe -m pytest packages/workspace_service/tests/test_workflow_run_paths.py -q
.venv/Scripts/python.exe -m pytest packages/workspace_service/tests/test_workflow_run_paths.py packages/workspace_service/tests/test_process_input_readiness.py packages/workspace_service/tests/test_process_preparation_service.py packages/workspace_service/tests/test_workflow_approval_execution.py packages/workspace_service/tests/test_workflow_approval_resume.py packages/workspace_service/tests/test_workflow_execution_continuation.py packages/workspace_service/tests/test_workflow_external_action_execution.py -q
.venv/Scripts/python.exe -m ruff check packages/workspace_service/src/workspace_service/workflow_run_paths.py packages/workspace_service/tests/test_workflow_run_paths.py
```

No engineering start, review, provider call, uncertain action replay or physical
effect is part of these checks. The full Feature 083 obligations remain active.
