# Quickstart: Architecture Refactoring Audit Implementation

## Targeted Fast Checks

Run package and API checks for touched areas:

```bash
uv run pytest packages/agent_adapters/tests apps/api/tests/test_agent_health.py apps/api/tests/test_config.py
uv run pytest apps/api/tests/test_mcp_api.py apps/api/tests/test_mcp_credentials.py apps/api/tests/test_gateway_api.py
uv run pytest packages/tool_registry/tests hermes-plugin-wright/tests
uv run pytest tests/e2e
```

Run frontend checks only when frontend files or Playwright smoke behavior are touched:

```bash
npm run test --workspace=apps/web
npx playwright test tests/ui-integration/tool-registry.spec.ts
```

## Opt-In Validation Checks

Clean-container validation is opt-in and should follow `docs/mcp-catalog/mcp-server-testing-process.md`.

Do not add MCP-specific host software to the base Docker image just to make validation pass.

```bash
# Example shape only; concrete runner command is introduced by implementation.
uv run python -m tool_registry.validation_runner --server <server-id> --clean-container
```

## Review Checkpoints

After each phase:

1. Verify targeted tests for touched contracts.
2. Confirm API response shapes did not change.
3. Confirm Hermes remains functional.
4. Confirm offline-first defaults remain intact.
5. Commit the phase as a small coherent group.

## Rollback Checklist

- Phase 1: restore previous API engine wiring if registry selection fails.
- Phase 2: disable new gateway adapters and keep existing Hermes sync service.
- Phase 3: route a moved MCP operation back to prior route-local logic for that operation.
- Phase 4: keep existing plugin/API catalog loaders if shared normalization parity fails.
- Phase 5: keep metadata classification preflight and disable new runner execution.
- Phase 6: isolate smoke fixture issues from product regressions before marking tests optional.

