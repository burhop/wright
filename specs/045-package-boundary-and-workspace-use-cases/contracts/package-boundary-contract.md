# Package Boundary Contract

## Approved direct graph

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

The public `wright_engineering` package and integration plugins consume public protocols and must not import private package internals.

## Ownership rules

- `core`: domain values, identifiers, error taxonomy, redaction, and side-effect-neutral contracts only.
- `data_vault`: SQLite policy, migrations/recovery, repositories, and local secret storage implementations.
- `tool_registry`: catalog, tool metadata/safety, runners, and gateway/lifecycle capabilities.
- `agent_adapters`: provider-neutral runtime interface and provider-specific context/config adapters.
- `workspace_service`: application workflows coordinating explicit ports.
- `apps/api`: composition and transport translation.

## Enforcement behavior

The checker must:

1. cover every production Python file beneath declared roots;
2. resolve absolute and relative imports to owned surfaces;
3. inspect imports nested in functions, classes, and conditional blocks;
4. recognize literal `importlib.import_module()` and `__import__()` targets;
5. reject non-literal dynamic imports in owned production code unless precisely exempted;
6. compare discovered edges with the manifest and distribution metadata;
7. reject cycles, unknown owners, missing roots, and stale exceptions;
8. report owner, dependency, file, line, and import form.

Seeded tests must prove rejection for direct, from, relative, aliased, local, and dynamic forbidden imports.

## Completion invariant

The production manifest contains no temporary violation exception. Compatibility shims may exist only on approved edges and may not contain alternate business logic.
