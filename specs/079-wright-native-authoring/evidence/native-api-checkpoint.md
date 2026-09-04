# Native service, API and HTTP CLI checkpoint

The native process service now composes the run repository, runtime and exact
MCP adapter using the application's existing gateway. Startup acquires the
runtime owner before accepting new submissions or reconciling generated
artifact storage. Reconciliation retains indexed evidence and records bounded
residue for inaccessible stores. No run enqueues until the startup sweep ends.
Shutdown closes the native runtime and its adapter before the shared gateway.

Run submission checks exact request replay before looking at the current saved
token or readiness. New runs use the shared validator and current gateway
preflight. Workspace authority is revalidated after asynchronous preparation;
the database commit and runtime enqueue then execute without an intervening
await. The submitted run remains owned by the application when its requesting
HTTP client disconnects. Inspection, events, history, cancellation and artifact
downloads all resolve the current managed workspace and enforce run scope.
Downloads verify stored size and digest before returning inert attachment bytes.

The frozen CLI is available as:

```text
python -m workspace_service.native_process_cli --base-url http://127.0.0.1:8000 --session-id SESSION check DEFINITION.json
python -m workspace_service.native_process_cli --base-url http://127.0.0.1:8000 --session-id SESSION run PROCESS --expected-token TOKEN --request-id REQUEST
python -m workspace_service.native_process_cli --base-url http://127.0.0.1:8000 --session-id SESSION inspect RUN
python -m workspace_service.native_process_cli --base-url http://127.0.0.1:8000 --session-id SESSION cancel RUN
```

Check and run accept `--bindings FILE`; run also accepts
`--timeout-seconds` and `--derived-from-run-id`. Authentication uses the existing
`WRIGHT_API_TOKEN` environment setting. The CLI invokes the HTTP API and opens
no database or executor. It prints JSON; an unready check exits 2, a request or
transport failure exits 1, and a successful request exits 0.

Focused verification uses isolated SQLite stores, the real native runtime,
FastAPI routes and HTTP client transport. It compares all three packaged
examples with the frozen artifact-byte oracles; covers programmatic/API/CLI
inspection parity; verifies exact replay after a newer unready save; and checks
active cancellation, requesting-client disconnect, scope changes, gateway
binding policy, digest tampering, request limits and owner-only reconciliation.
The existing authoring API and application startup ordering tests remain in the
same focused check. The binding test proves current catalog/policy discovery
without starting its disposable fixture; it is not live MCP protocol evidence.

The focused command is:

```text
pytest apps/api/tests/test_native_process_execution_api.py apps/api/tests/test_native_process_api.py apps/api/tests/test_database_startup.py -q
```

The final focused run passed **23 tests**. Tests use the existing Python 3.13.5 environment with this worktree's source
directories on `PYTHONPATH`. Temporary paths and empty explicit Hermes config
paths remain under `.local-run`; no installed agent configuration is needed.
Ruff format/lint and `git diff --check` are also required for this checkpoint.
The HTTP tests use ASGI transport; an actual product server, browser journey,
installed-wheel lifecycle, and independent integration review remain separate
evidence owned by the parent workstream.
