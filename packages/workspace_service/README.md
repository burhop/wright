# Wright Workspace Service

`wright-workspace-service` owns application workflows for workspace lifecycle,
sessions, files and backups, Git, execution, context, settings, agent context,
tool selection, runtime reconciliation, and refresh notifications.

Use cases receive their repository, filesystem, Git, process, agent, and
notification capabilities explicitly. Concrete local adapters are selected in
composition; HTTP routes translate requests and results only.

The package may depend on `core`, `data_vault`, `tool_registry`, and
`agent_adapters`. It must not import API routes or HTTP framework types.
`architecture/python-packages.toml` and `tests/test_import_boundaries.py`
enforce this direction and reject dynamic-import workarounds.

Blocking host work uses a bounded executor with finite deadlines and
cancellation propagation. API lifespan owns and closes that executor.

Feature 045 is a code-ownership migration only: SQLite schema, workspace file
layout, authentication, and HTTP contracts remain unchanged. Roll back by
stopping the process and running the prior reviewed version against the same
state, using the normal database backup/restore procedure when needed.
