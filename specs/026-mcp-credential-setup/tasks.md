# Tasks: MCP Credential & Secret Setup

**Input**: Design documents from `/specs/026-mcp-credential-setup/`

**Prerequisites**: plan.md ✅, spec.md ✅, research.md ✅, data-model.md ✅, quickstart.md ✅

**Tests**: Included — the spec explicitly requires test cases to verify the OnShape MCP works correctly.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: No new project initialization needed — this feature extends the existing Wright monorepo.

- [ ] T001 Verify feature branch `026-mcp-credential-setup` is checked out and clean

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core credential store module and model evolution that ALL user stories depend on.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete.

- [ ] T002 Create credential store module at packages/tool_registry/src/tool_registry/secrets.py — implement `read_secrets()`, `write_secrets()`, `delete_secrets()`, `has_credentials()` with `fcntl.flock` advisory locking and `0600` file permissions. Use `WRIGHT_SECRETS_PATH` env var override for testing.
- [ ] T003 Add `EnvVarDefinition` Pydantic model to packages/tool_registry/src/tool_registry/models.py — fields: name, label, description, required, secret. Evolve `McpServer.env_vars` from `Optional[dict[str, str]]` to `Optional[list[EnvVarDefinition]]`. Add `credentials_configured: Optional[dict[str, bool]]` dynamic field. Update `McpServerCreate.env_vars` similarly. Maintain backward compatibility in `McpServerUpdate.env_vars`.
- [ ] T004 Update packages/tool_registry/src/tool_registry/db.py — modify `_row_to_server()` to detect and deserialize both old `dict` format and new `list[EnvVarDefinition]` format from the `env_vars` JSON column. Update `insert_server()` and `update_server()` to serialize `list[EnvVarDefinition]` as JSON.
- [ ] T005 Export new symbols from packages/tool_registry/src/tool_registry/__init__.py — export `EnvVarDefinition`, `read_secrets`, `write_secrets`, `delete_secrets`, `has_credentials`.

**Checkpoint**: Foundation ready — credential store module exists, models are evolved, DB layer handles both formats.

---

## Phase 3: User Story 1 — Configure an MCP Server Requiring Credentials (Priority: P1) 🎯 MVP

**Goal**: Engineers can configure API keys/secrets for MCP servers through the UI. Credentials are passed to the server process as environment variables at startup.

**Independent Test**: Register an MCP server with required env vars, enter credentials via API, verify the server starts with those credentials injected as env vars.

### Tests for User Story 1

- [ ] T006 [P] [US1] Write credential store unit tests in apps/api/tests/test_mcp_credentials.py — test `write_secrets()`, `read_secrets()`, `delete_secrets()`, `has_credentials()`, file permissions (`0600`), missing file handling, concurrent access, and `WRIGHT_SECRETS_PATH` env var override.
- [ ] T007 [P] [US1] Write credential API endpoint tests in apps/api/tests/test_mcp_credentials.py — test `GET /credentials` (returns definitions + configured flags), `PUT /credentials` (saves values, returns updated flags), `DELETE /credentials` (removes values), and validation of non-existent servers.

### Implementation for User Story 1

- [ ] T008 [US1] Update McpEngine.start_server() in packages/tool_registry/src/tool_registry/manager.py — before creating StdioRunner, call `read_secrets(server_id)` to load saved credentials. Merge saved credentials into env_vars dict. Add validation: if server has required env var definitions and required credentials are missing, raise descriptive ValueError.
- [ ] T009 [US1] Add credential management endpoints to apps/api/src/api/routers/mcp.py — implement `GET /servers/{server_id}/credentials` (returns env var definitions and configured booleans), `PUT /servers/{server_id}/credentials` (saves credentials to secrets store), `DELETE /servers/{server_id}/credentials` (removes credentials). Add Pydantic request/response models: `CredentialStatusResponse`, `SaveCredentialsRequest`.
- [ ] T010 [US1] Update `list_servers()` in apps/api/src/api/routers/mcp.py — add `credentials_configured` field to each server response by calling `has_credentials()` for servers with env_var definitions. Ensure no secret values are ever included.
- [ ] T011 [US1] Update `install_server_endpoint()` in apps/api/src/api/routers/mcp.py — before starting the server, validate that all required credentials are configured. Return HTTP 400 with descriptive error message if not.
- [ ] T012 [US1] Update `delete_server_endpoint()` in apps/api/src/api/routers/mcp.py — call `delete_secrets(server_id)` to clean up credentials when a server is removed.

**Checkpoint**: Backend credential management is fully functional. Credentials can be saved, loaded, and injected into MCP server processes. Install is blocked when required credentials are missing.

---

## Phase 4: User Story 2 — Secure Secret Storage Outside Repository (Priority: P1)

**Goal**: All MCP secrets are stored in `~/.config/wright/mcp-secrets.json` with restricted file permissions. No secrets in the database, git-tracked files, or API responses.

**Independent Test**: Save credentials via the API, then verify: secrets file exists with `0600` permissions, SQLite `env_vars` column contains only definitions (not values), `GET /api/mcp/servers` does not return secret values.

### Tests for User Story 2

- [ ] T013 [P] [US2] Write security validation tests in apps/api/tests/test_mcp_credentials.py — test that `GET /api/mcp/servers` response never contains credential values, that `env_vars` column in SQLite contains only definitions, and that secrets file has `0600` permissions after write operations.

### Implementation for User Story 2

- [ ] T014 [US2] Audit and sanitize the `list_servers()` response in apps/api/src/api/routers/mcp.py — ensure the serialized server response maps `env_vars` to definitions only (no values). Add a response sanitization step that strips any accidental value leakage.
- [ ] T015 [US2] Ensure the secrets file directory `~/.config/wright/` is created with `0700` permissions in packages/tool_registry/src/tool_registry/secrets.py — verify parent directory permissions on every write operation.

**Checkpoint**: Security guarantees verified — secrets never leak into DB, API responses, or repo files.

---

## Phase 5: User Story 3 — Pre-configured OnShape MCP in Wright Catalog (Priority: P2)

**Goal**: The Jarvis OnShape MCP is pre-registered in the catalog with env_var definitions and can be installed after credentials are configured.

**Independent Test**: Open the Tool Registry, find "Jarvis OnShape MCP", configure credentials, install, verify tools are discovered.

### Tests for User Story 3

- [ ] T016 [P] [US3] Write OnShape catalog entry tests in apps/api/tests/test_mcp_credentials.py — verify the catalog entry exists with correct server_id, name, type, command, category, and env_var definitions after migration.

### Implementation for User Story 3

- [ ] T017 [US3] Add Jarvis OnShape MCP to ENGINEERING_CATALOG in apps/api/src/api/database/migrate.py — add catalog entry with server_id `jarvis-onshape-mcp`, type `stdio`, command `["uv", "run", "--with", "jarvis-onshape-mcp", "onshape-mcp"]`, category `cad`, and env_vars definitions for `ONSHAPE_API_KEY` (label: "Access Key", required, not secret) and `ONSHAPE_API_SECRET` (label: "Secret Key", required, secret).
- [ ] T018 [US3] Update the catalog seed loop in apps/api/src/api/database/migrate.py — include `env_vars` in both the `INSERT OR IGNORE` and `UPDATE` SQL statements so env_var definitions are seeded and kept current.
- [ ] T019 [US3] Run database migration and verify the OnShape MCP entry is seeded — execute `uv run python -m api.database.migrate` and confirm the entry exists with correct env_vars.

**Checkpoint**: OnShape MCP is in the catalog and ready for credential configuration.

---

## Phase 6: User Story 4 — Credential Configuration for Any MCP Type (Priority: P2)

**Goal**: The credential UI works generically for any MCP server that declares env_var definitions, not just OnShape.

**Independent Test**: Register a custom MCP server with env_var definitions, verify the credential UI renders correct fields and saves/loads credentials.

### Implementation for User Story 4

- [ ] T020 [P] [US4] Update McpServer interface in apps/web/src/services/mcp-service.ts — add `EnvVarDefinition` interface, add `env_vars?: EnvVarDefinition[]` and `credentials_configured?: Record<string, boolean>` fields to `McpServer` interface. Add `RegisterServerPayload.env_vars` field. Add `getCredentialStatus()`, `saveCredentials()`, `deleteCredentials()` API methods to `McpService` class.
- [ ] T021 [P] [US4] Add credential state management to apps/web/src/store/tools.tsx — add `saveCredentials` and `deleteCredentials` actions to `ToolsContextProps` and `ToolsProvider`. Wire through to `mcpService` methods. Update `fetchServersAndTools` to handle servers with `credentials_configured`.
- [ ] T022 [US4] Add credential configuration panel to apps/web/src/components/tools/ToolCard.tsx — add collapsible "Configure Credentials" section below server description. Render labeled input fields for each env var definition (password type for `secret: true`, text for others). Add "Required" indicator. Add "Save Credentials" and "Clear Credentials" buttons. Show configured/not-configured status indicators (green check / red X). Block install button when required credentials are missing with tooltip. Add "Requires Configuration" badge. All new elements include `data-testid` attributes.

**Checkpoint**: Any MCP server with env_var definitions gets a working credential configuration panel.

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Final validation, documentation, and regression checks.

- [ ] T023 Run existing MCP API test suite for regression — execute `uv run pytest apps/api/tests/test_mcp_api.py -v` and verify no regressions.
- [ ] T024 Run full credential test suite — execute `uv run pytest apps/api/tests/test_mcp_credentials.py -v` and verify all tests pass.
- [ ] T025 Run quickstart.md manual verification steps — follow specs/026-mcp-credential-setup/quickstart.md end-to-end.
- [ ] T026 Verify OnShape MCP end-to-end — configure real OnShape credentials (already stored at `~/.config/wright/mcp-secrets.json`), install the server via the UI, verify it starts and discovers tools.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — verify branch state
- **Foundational (Phase 2)**: Depends on Setup — BLOCKS all user stories
- **US1 (Phase 3)**: Depends on Foundational — backend credential management
- **US2 (Phase 4)**: Depends on US1 — security hardening on top of working credential flow
- **US3 (Phase 5)**: Depends on Foundational — catalog entry only needs model evolution
- **US4 (Phase 6)**: Depends on US1 (API endpoints must exist for frontend to call)
- **Polish (Phase 7)**: Depends on all user stories being complete

### User Story Dependencies

- **US1 (P1)**: Can start after Foundational (Phase 2) — no dependencies on other stories
- **US2 (P1)**: Can start after US1 — adds security validation on existing credential flow
- **US3 (P2)**: Can start after Foundational (Phase 2) — only needs model evolution for env_vars format. **Can run in parallel with US1**
- **US4 (P2)**: Depends on US1 API endpoints — frontend needs working backend

### Within Each User Story

- Tests written first (where included)
- Models/services before endpoints
- Backend before frontend
- Core implementation before integration

### Parallel Opportunities

- **Phase 2**: T002, T003, T004 are sequential (model → db depends on model). T005 depends on T002.
- **Phase 3**: T006 and T007 are parallel (test files). T008-T012 are sequential.
- **Phase 5 and Phase 3**: T017 (catalog entry) can run in parallel with Phase 3 backend work
- **Phase 6**: T020 and T021 are parallel (different files: mcp-service.ts vs tools.tsx). T022 depends on both.

---

## Parallel Example: User Story 4 (Frontend)

```bash
# Launch parallel frontend foundation work:
Task: "Update McpServer interface in apps/web/src/services/mcp-service.ts"
Task: "Add credential state management to apps/web/src/store/tools.tsx"

# Then sequential UI work (depends on both):
Task: "Add credential configuration panel to apps/web/src/components/tools/ToolCard.tsx"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (secrets module + model evolution)
3. Complete Phase 3: User Story 1 (backend credential management)
4. **STOP and VALIDATE**: Test credential save/load/inject via curl
5. Credentials work end-to-end via API

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready
2. Add US1 (credential backend) → Test via API → Working credential management (MVP!)
3. Add US2 (security hardening) → Verify no secret leaks
4. Add US3 (OnShape catalog) → OnShape MCP available in catalog
5. Add US4 (frontend UI) → Full UI credential configuration
6. Polish → Regression tests, end-to-end validation

### Recommended Sequential Order

For a single developer, the recommended order is:
1. Phase 1 → Phase 2 → Phase 3 (US1) → Phase 5 (US3) → Phase 4 (US2) → Phase 6 (US4) → Phase 7

US3 (catalog entry) is placed before US2 (security) because it's a quick catalog addition that enables end-to-end testing with real OnShape credentials.

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- OnShape credentials already stored at `~/.config/wright/mcp-secrets.json` from the specify phase
- The `WRIGHT_SECRETS_PATH` env var override enables isolated testing without touching the real secrets file
