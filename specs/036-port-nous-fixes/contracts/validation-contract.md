# Validation Contract

## Backend and Package Validation

Run targeted Python tests for accepted backend/package areas when practical:

```powershell
uv run pytest apps/api/tests packages/agent_adapters/tests packages/tool_registry/tests
```

Narrower invocations are acceptable when the touched files map to specific tests.

## Frontend Validation

Run targeted frontend tests for accepted UI/service areas when practical:

```powershell
npm run test --workspace=apps/web
```

Focused test filters are acceptable when available.

## MCP Catalog Validation

If accepted changes affect MCP server validation or catalog behavior:

1. Follow `docs/mcp-catalog/mcp-server-testing-process.md`.
2. Use clean-container validation for engineering MCP servers.
3. Do not add MCP-specific host software to the base Docker image just to make validation pass.
4. Update problem logs or setup recipes only when the accepted change requires it.

## Completion Criteria

- Targeted tests pass, or failures/blockers are documented.
- Final diff contains no excluded prototype files.
- Final diff can be traced back to reviewed candidates.
