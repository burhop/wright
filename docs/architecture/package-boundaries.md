# Python Package Boundaries

Wright enforces one inward dependency direction so application behavior has one owner and transport code cannot become a second service layer.

```text
core
  ^
  +-- data_vault
  +-- tool_registry
  +-- agent_adapters
          ^       ^       ^
          +-------+-------+
              workspace_service
                     ^
                  apps/api
```

`architecture/python-packages.toml` is the source of truth for roots, import names, approved direct edges, package metadata, forbidden runtime modules, and temporary migration exceptions. `tests/test_import_boundaries.py` parses all production Python files, including local and dynamic imports, validates graph acyclicity, and rejects source/metadata drift.

## Ownership

- `core` owns side-effect-neutral domain identifiers, values, errors, redaction, and telemetry contracts.
- `data_vault` owns SQLite lifecycle and repositories plus local secret storage implementations.
- `tool_registry` owns catalog, safety, runners, and gateway/lifecycle capabilities.
- `agent_adapters` owns provider runtime and context/configuration adapters.
- `workspace_service` owns workspace application use cases and their host adapters.
- `apps/api` constructs the graph and translates HTTP/WebSocket requests and results.

Ports are defined by the lowest-level consumer that needs the capability. Concrete adapters depend inward on those ports. A use case receives repositories, file/path, Git, process, agent-context, secret, clock, and notification capabilities explicitly; it does not select global implementations.

## Changing the graph

Before allocating new workflow, review, validation, or external-action behaviour,
apply the [workflow platform vision](../design/workflow-platform-vision.md).
Vendor-specific application/device implementation belongs in an independent,
installed integration reached through public capability contracts. Catalog
metadata and example bindings can name a vendor without implementing its
protocol. Generic engineering-format readers and evaluators can remain in their
existing Wright ownership; vendor-specific native readers belong externally.
Existing vendor adapters require explicit migration plans rather than copying
their coupling into new features. The
[workflow platform refactoring plan](workflow-platform-refactoring-plan.md) maps
the shared process interaction/UI foundation and supporting prototype migration
without changing the package manifest or claiming migration is complete. Prefer
existing providers; the [process UI design](../design/process-apps.md) keeps
generated views on public contracts and existing execution services.

1. Decide which package owns the behavior and why the dependency points inward.
2. Update the manifest and the consuming package metadata together.
3. Add a seeded fitness test if the new edge introduces an import form not already covered.
4. Update the relevant package README.
5. Run `uv run pytest -q tests/test_import_boundaries.py` and the affected package tests.

Temporary exceptions must name one file, one edge, the reason, and the feature that removes it. Wildcards are forbidden; Feature 045 completes only after its migration exceptions are empty.

## Compatibility and rollback

Ownership moves do not change the state schema, workspace layout, authentication contract, or HTTP shapes. A compatibility entry point may remain for one release only when a repository-wide caller search proves it is live; it must adapt inputs and delegate to the same use case without separate business logic.

For rollback, stop the upgraded process and start the prior reviewed image or commit against the unchanged state. Use the documented database backup/restore procedure for normal deployment protection; no reverse migration is required.
