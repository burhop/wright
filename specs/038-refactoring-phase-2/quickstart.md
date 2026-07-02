# Quickstart: Wright Architecture Refactoring Phase 2

## Default Verification

Run after implementation:

```bash
uv run pytest packages/agent_adapters packages/tool_registry packages/workspace_service packages/core apps/api/tests
```

Run frontend tests if generated contracts or frontend code changed:

```bash
npm run test --workspace=apps/web
```

Run contract generation check:

```bash
uv run python scripts/generate-frontend-contracts.py --check
```

## Opt-In Validation CLI

Mock executor for fast local development:

```bash
uv run python -m tool_registry.validation_cli validate <server-id> --executor mock --evidence-dir docs/mcp-catalog/evidence
```

Clean-container validation is operator-invoked only:

```bash
uv run python -m tool_registry.validation_cli validate <server-id> --container ubuntu-x64 --executor docker --evidence-dir docs/mcp-catalog/evidence
```

Do not interpret a skipped/follow-up-required Docker evidence file as a passing clean-container validation.

## Expected Offline Behavior

The default pytest and frontend tests must not require:

- Docker
- network access
- credentials
- hosted agents
- package registries
- proprietary CAD/CAE/CAM software
- hardware-bound tools
