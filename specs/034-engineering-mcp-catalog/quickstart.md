# Quickstart: Engineering MCP Catalog

## 1. Validate Speckit Context

```powershell
git status --short --branch
Get-Content .specify/feature.json
```

Expected:

- Branch is `034-engineering-mcp-catalog`.
- Active feature directory is `specs/034-engineering-mcp-catalog`.

## 2. Run Python Tests

```powershell
uv run pytest hermes-plugin-wright/tests packages/tool_registry/tests apps/api/tests
```

Expected:

- Catalog schema validation passes.
- Platform metadata and safety default tests pass.
- API returns extended catalog metadata.
- Validation/follow-up classification tests pass.

## 3. Run Web Tests

```powershell
npm run test --workspace=apps/web
npm run build --workspace=apps/web
```

Expected:

- Tool registry cards render verification state, installability tier, platform support, dependencies, risk, and follow-up links.
- Search and sorting preserve tested -> might work -> blocked -> non-working ordering.

## 4. Run UI Integration Smoke

```powershell
npm run test:ui --workspace=apps/web -- tests/ui-integration/tool-registry.spec.ts
```

If the repo does not expose this exact script, run the existing Playwright command documented in `package.json`.

Expected:

- Registry page loads.
- Tier controls and card metadata are visible.
- No card text overlaps or breaks at desktop viewport.

## 5. Run Ubuntu Container Validation

```powershell
docker compose -f docker-compose.test.yml build agent
docker compose -f docker-compose.test.yml run --rm agent uv run pytest packages/tool_registry/tests apps/api/tests
```

Expected:

- The base Intel Ubuntu container starts as a clean Wright runtime and validation harness.
- The base image does not preload MCP-specific host software such as OpenSCAD, FreeCAD, Blender, vendor CAD systems, simulation solvers, or hardware drivers.
- Fully local catalog metadata validation runs in the Ubuntu container.
- Blocked URL-needed entries are skipped with clear reasons.

## 6. Run Per-MCP Validation Loop

Follow the process in `docs/mcp-catalog/mcp-server-testing-process.md`.

For each MCP server, start from a clean container, print the catalog metadata,
install only that server and the dependencies needed to test that server, run the
smallest safe probe, and write the result back to the catalog metadata. If a
dependency is unavailable, expensive, proprietary, unsafe, licensed, or requires
hardware, record the expected diagnostic instead of installing it.

Expected:

- The first MCP server is tested from catalog metadata through install/start/probe.
- Per-MCP dependency installs are recorded as validation evidence.
- Host dependency gaps produce clear messages such as "OpenSCAD not installed",
  "license required", "credentials missing", or "hardware unavailable".
- Problems are added to `docs/mcp-catalog/testing-problem-log.md`.

## 7. Inspect Follow-Up Records

```powershell
Get-ChildItem docs/mcp-catalog/followups
```

Expected:

- Any non-working validation result has a stable follow-up markdown record.
- Existing records are reused rather than duplicated.
