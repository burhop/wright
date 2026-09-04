# Native MCP adapter checkpoint

This checkpoint covers the bounded T024 adapter and T025 local protocol proof.
It does not mark the full native milestone, runtime integration, release, or a
catalog server qualification complete.

## Implementation

`NativeMcpAdapter(gateway, workspace_resolver)` provides synchronous
`discover(session_id)` and `preflight(session_id, binding)`, plus async
`call(session_id, binding, arguments, timeout_seconds, trace_id) -> str`.
The resolver is the same managed-workspace resolver used by the native service.
Discovery returns the frozen `{bindings:[...]}` DTO and preflight returns one
descriptor. Neither starts a server or invokes a tool.

Every check revalidates the managed session, current enabled catalog identity,
exact input/output schema digests, and gateway policy. Native code supplies no
approval grants. Tools requiring an unresolved approval are unavailable to this
milestone. An opt-in `GatewayService.before_dispatch` callback repeats the
checks after lazy startup refreshes the catalog, immediately before gateway
forwarding. Existing callers without that callback preserve their behavior.
The real engine still applies its existing credential and safety policy gates.

Arguments are copied before asynchronous startup; calls are limited to the
smaller of the remaining runtime budget and 15 seconds. Arguments, schemas,
and results are bounded to 1 MiB, with JSON nesting capped at 64. Schemas must
be self-contained: nonlocal JSON Schema references are rejected before any
resolver can fetch external data. Structured results use finite compact JSON;
text-only results retain text. Unsupported binary/image results, nonfinite
JSON, schema failures, oversized outputs, and tool errors produce actionable
native errors. Provider error payloads are not copied into native diagnostics.

Top-level errors use the frozen `NATIVE_DENIED`, `NATIVE_BINDING_CHANGED`,
`NATIVE_NOT_READY`, or `NATIVE_LIMIT` envelope; `Finding.code` carries the
specific `MCP_*` reason. Native adapter code imports no Rivet module and does
not evaluate document commands or choose a transport from document fields.

Gateway sessions are reused per managed session, capped at 128 per adapter,
and reopened against current workspace authority on every check. Relocated or
reassigned workspaces fail closed. Parent composition must call
`await adapter.close()` at shutdown, before shutting down the shared gateway.
This closes only adapter-owned sessions; it does not stop other gateway users.

## Verification

On Windows, Python 3.13.5 from the existing root `.venv`, with `PYTHONPATH`
explicitly selecting this isolated worktree's package source directories:

- `pytest packages/workspace_service/tests/test_native_process_mcp.py
  packages/workspace_service/tests/test_native_process_mcp_protocol.py
  packages/tool_registry/tests/test_gateway_service.py
  packages/tool_registry/tests/test_gateway_policy.py
  packages/tool_registry/tests/test_gateway_adapters.py -q`: **49 passed,
  1 skipped**. Disposable pytest paths were placed under `.local-run`; the
  protocol test is skipped by default. These use fake child ports and prove
  schema/policy/session startup races, exact bindings, no preflight invocation,
  bounded results, frozen arguments, 15-second clamping, cancellation, timeout,
  cleanup, and legacy gateway behavior. They are not live protocol evidence.
- With `WRIGHT_NATIVE_MCP_PROTOCOL=1`, the focused protocol test alone:
  **1 passed**. `WRIGHT_TESTING` is removed inside this test and the real
  `StdioRunner` type and independent child PID are asserted.
- Ruff format/check and `git diff --check`: **passed**.

The initial sandbox test attempt could not create pytest's default Windows
temporary directory. Moving disposable test files into this worktree resolved
that setup issue. The subprocess proof used the approved local subprocess
execution boundary. It installed no dependency and used no network service.

## Actual local protocol evidence

[Captured protocol and audit](native-mcp-local-protocol.json) records an actual
`NativeMcpAdapter → DatabaseGatewayCatalog/Workspace/Audit →
EngineGatewayLifecycle → McpEngine → StdioRunner` execution. The only tool is
a disposable Python fixture that reads a test-created local measurement file.
The server launches with the existing Python interpreter using `-I -u`, with
no third-party dependencies, credentials, paid APIs, proprietary host, hardware,
or document-supplied command. It is not an engineering catalog server.

The transcript demonstrates `initialize`, `notifications/initialized`,
`tools/list`, and one exact `tools/call`. Input `0.5` and the fixture multiplier
`2.5` produce canonical native text `{"value":1.25}`. The source fixture bytes
remain unchanged and the child process exits during teardown. The recorded
protocol version is `2025-11-25`.

Trace linkage is demonstrated separately by persisted gateway started and
succeeded audit records containing `native-local-protocol-trace`, and the
native span retains the supplied trace ID while downstream tracing inherits
the active OpenTelemetry context. The child JSON-RPC protocol contains no
custom trace metadata extension. Fake startup-denial regression tests verify
failed audit linkage; they are not described as live denied-tool executions.

The evidence export passes through Wright's shared `redact_mapping` helper.
It retains only safe fixture inputs/results and bounded gateway audit metadata.
This local proof does **not** replace the clean Linux container install,
backend action, gateway checks, teardown, and catalog evidence required by
`docs/mcp-catalog/mcp-server-testing-process.md` for catalog qualification.
