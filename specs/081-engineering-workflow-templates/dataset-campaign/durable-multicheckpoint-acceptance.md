# Durable multi-checkpoint acceptance

September 12, 2026. DC006B is covered by
`apps/api/tests/test_workflow_multicheckpoint_durable_mcp.py` and the adjacent
existing approval/continuation tests. No live workspace, selected engineering
host, registry, API process or campaign attempt was changed for this test run.

## Test boundary

The new tests invoke the normal saved-source run, approval decision and resume
API handlers with their Pydantic requests. They use actual source compilation,
integration policy validation, SQLite continuation repositories, file adapters,
durable run recording, GatewayService and StdioRunner. A private FastMCP child
implements one fixed operation under pytest's isolated temporary root. It
appends one dispatch record and writes a small computed JSON file. The final
tool result and independently read file SHA-256 enter the run's artifact record.
Only the initial package's model response is deterministic; no model provider,
printer, supplier or engineering application is used by this runtime test.

Each decision and resume constructs a fresh application service, reopening the
same SQLite database and saved source/files. This proves service restart from
durable state, including pending/approved checkpoints before dispatch and
unknown/completed outcomes afterward. These are API-handler integration tests,
not an HTTP authentication test or a forced operating-system crash test.

| Case | Durable result and replay assertion |
| --- | --- |
| Two sequential checkpoints | One run, both review steps and actual final MCP step complete; file hash recorded; duplicate decisions and both old/current resume requests return stored results; exactly one tool dispatch. |
| Cancellation before final MCP dispatch | Resume claim becomes cancelled/unknown; no child call occurs; a fresh service refuses replay. |
| Cancellation after final MCP dispatch | Child file exists with one dispatch; interrupted response leaves cancelled/unknown continuation; a fresh service refuses replay. |
| Lost tool response | Actual child operation completes before injected transport loss; failed/unknown continuation refuses another dispatch. |
| Cancellation after outcome persistence | Completed run survives a caller disconnect; a fresh service returns its cached complete result with exactly one dispatch. |

The existing adjacent suites additionally cover unknown external-action
dispatch, stale source/input/artifact/binding/cursor identity, consumed claims,
concurrent resume, authority expiry/revocation and manual-only/denied decisions.

## Verification

```text
.venv/Scripts/python.exe -m pytest \
  apps/api/tests/test_workflow_multicheckpoint_durable_mcp.py \
  apps/api/tests/test_workflow_integration_run_api.py \
  packages/workspace_service/tests/test_workflow_execution_continuation.py \
  packages/workspace_service/tests/test_workflow_approval_execution.py \
  -q --tb=short \
  --basetemp=.local-run/feature-081-live/pytest-durable-mcp-suite-001
43 passed in 25.80s
```

The focused file passed five tests; Ruff passed. This closes the bounded
continuation acceptance task. It does not increment dataset/process counters,
establish engineering correctness, qualify external integrations or close
DC010A/DC011A.
