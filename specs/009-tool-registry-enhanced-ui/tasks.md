# Tasks: Enhanced Tool Registry UI

**Input**: Design documents from `/specs/009-tool-registry-enhanced-ui/`

**Prerequisites**: [plan.md](plan.md) ✅ | [spec.md](spec.md) ✅ | [research.md](research.md) ✅ | [data-model.md](data-model.md) ✅ | [contracts/mcp-version-check.md](contracts/mcp-version-check.md) ✅

**Organization**: Tasks grouped by user story. Each story is independently implementable and testable.

> [!IMPORTANT]
> **Browser Constraint**: Antigravity runs on the local PC and SSHes into the GB10. The dev server, API, repo, and **Playwright all run on the GB10** — Playwright tests execute as terminal commands and hit `http://localhost:5173` on the GB10 directly. The existing `playwright.config.ts` (`baseURL: 'http://localhost:5173'`) is already correct. Do NOT override the baseURL. The constraint is that Antigravity's own `browser_subagent` tool cannot be used for visual inspection — every UI checkpoint must instead be encoded as a `npx playwright test` command run in the terminal.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no shared dependencies)
- **[Story]**: Which user story this task belongs to (US1–US5)
- All file paths are relative to the repository root
- All UI verification = `npx playwright test <spec> --reporter=list` (runs on GB10 against `localhost:5173`)

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Ensure branch is current, DB migration utility is in place, and no existing tests break before feature work begins.

- [ ] T001 Verify active branch is `009-tool-registry-enhanced-ui` via `git branch --show-current`
- [ ] T002 Run existing backend MCP tests to establish a green baseline: `cd apps/api && PYTHONPATH=src uv run pytest tests/test_mcp_api.py -v --tb=short`
- [ ] T003 Run existing Playwright MCP test to establish a green baseline against the remote dev server: `npx playwright test tests/ui-integration/mcp-directory.spec.ts --reporter=list` (config must point to `http://promaxgb10-9666:5173`)

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Extend the core data model, add the DB migration, and expose the new fields through the full backend stack. ALL user stories depend on this phase.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete.

- [ ] T004 [P] Add `image_url`, `description`, `source_url`, `installed_version` optional fields to `McpServer` and `McpServerCreate` models in `packages/tool_registry/src/tool_registry/models.py`
- [ ] T005 [P] Add idempotent SQLite migration for the 4 new columns in `packages/tool_registry/src/tool_registry/db.py` — wrap each `ALTER TABLE mcp_servers ADD COLUMN ...` in `try/except OperationalError`; call migration at startup; update `_row_to_server`, `insert_server`, and `update_server` to read/write new fields; replace `import logging` with `structlog.get_logger()`
- [ ] T006 Create `packages/tool_registry/src/tool_registry/version_check.py` — async `check_server_version(server: McpServer) -> dict` and `update_server(server: McpServer) -> dict` using `asyncio.create_subprocess_exec` with a 10-second timeout; dispatch by command prefix (`uvx`, `npx`, `pip`); return `{"error": "unsupported_package_manager"}` for unknown prefixes; return `{"error": "not_applicable"}` for non-stdio types
- [ ] T007 Extend `GET /api/mcp/servers` response and `POST /api/mcp/servers` request in `apps/api/src/api/routers/mcp.py` to include the four new optional fields; update `McpServerCreate` Pydantic model inline
- [ ] T008 Add `GET /api/mcp/servers/{server_id}/version-check` endpoint in `apps/api/src/api/routers/mcp.py` — 404 if not found, 400 if `sse`/`webmcp` type, delegates to `version_check.check_server_version()`; decorated with `@traced("mcp.server.version_check")`
- [ ] T009 Add `POST /api/mcp/servers/{server_id}/update` endpoint in `apps/api/src/api/routers/mcp.py` — 404 if not found, 400 if non-stdio; calls `version_check.update_server()`; on success updates `installed_version` in DB via `update_server()`; decorated with `@traced("mcp.server.update")`
- [ ] T010 Update existing seeded server entries (CalculiX Simulation, OpenSCAD Geometry) in the DB seed/init logic to populate `image_url`, `description`, and `source_url` values — locate the seed location and add the values there
- [ ] T011 Extend `McpServer` TypeScript interface in `apps/web/src/services/mcp-service.ts` to add `image_url?: string`, `description?: string`, `source_url?: string`, `installed_version?: string`; add `checkServerVersion(serverId: string): Promise<VersionCheckResult>` and `updateServer(serverId: string): Promise<{installed_version: string}>` methods with `VersionCheckResult` type exported
- [ ] T012 Add `checkServerVersion()` and `updateServerState()` to `apps/web/src/store/tools.tsx` — `checkServerVersion` returns result directly (no global state mutation, keeps version state per-card); `updateServerState` dispatches `UPDATE_SERVER` with new `installed_version` on success

**Checkpoint**: Validate foundation with: `cd apps/api && PYTHONPATH=src uv run pytest tests/test_mcp_api.py -v --tb=short` — all existing tests must still pass and the API must return the four new fields in `GET /api/mcp/servers`.

---

## Phase 3: User Story 1 — Browse the MCP Server Catalog (Priority: P1) 🎯 MVP

**Goal**: Every server card displays a logo/avatar, name, description, and a Local/Network type badge. Search and type filtering work in real time.

**Independent Test (Playwright — runs on GB10)**: `npx playwright test tests/ui-integration/tool-registry.spec.ts --grep "@US1" --reporter=list`
Assertions: CalculiX card has `data-testid="server-card-logo-*"` visible; `data-testid="server-type-badge-stdio"` present with amber style; description element visible; typing "calc" in search input reduces visible cards; clicking "local" filter hides non-stdio cards.

### Implementation for User Story 1

- [ ] T013 [P] [US1] Create `apps/web/src/components/tools/ServerTypeBadge.tsx` — atomic badge component accepting `type: 'stdio' | 'sse' | 'webmcp'`; renders amber "⬡ Local" for stdio, cyan "⚡ Network" for sse/webmcp; include HTML `title` tooltip explaining the type; `data-testid="server-type-badge-{type}"`
- [ ] T014 [US1] Add server logo/avatar rendering to `apps/web/src/components/tools/ToolCard.tsx` — 48×48 rounded `<img src={server.image_url}>` at card top-left; add `imgError` local state; `onError` handler sets `imgError=true` → renders styled `<div>` with first letter of server name as fallback avatar; `data-testid="server-card-logo-{server_id}"`
- [ ] T015 [US1] Add `<ServerTypeBadge>` and description block to `apps/web/src/components/tools/ToolCard.tsx` — import and render badge beneath server name; render `server.description` in `0.85rem` muted text with CSS `line-clamp` (max 3 lines); `data-testid="server-card-description-{server_id}"`
- [ ] T016 [US1] Update filter sidebar in `apps/web/src/components/pages/ToolRegistryPage.tsx` — add "local" and "network" as filter options; update `filteredServers` logic so "local" maps to `server.type === 'stdio'` and "network" maps to `['sse', 'webmcp'].includes(server.type)`; add `data-testid="tool-registry-category-{cat}"` on each filter button, `data-testid="tool-registry-search-input"` on search field, `data-testid="tool-registry-register-btn"` on register button
- [ ] T016a [US1] Write and run US1 Playwright assertions in `tests/ui-integration/tool-registry.spec.ts` (tagged `@US1`) covering: card logo visible or fallback visible; Local badge present on stdio cards; Network badge present on sse cards; description text visible; search box filters cards; category filter shows/hides cards; empty state on no-match. Run: `npx playwright test tests/ui-integration/tool-registry.spec.ts --grep "@US1" --reporter=list`

**Checkpoint**: `npx playwright test tests/ui-integration/tool-registry.spec.ts --grep "@US1" --reporter=list` — all US1 assertions green.

---

## Phase 4: User Story 2 — Install a Local MCP Server (Priority: P2)

**Goal**: Local (stdio) server cards clearly label the Install button, show a progress state, and display the installed version on success. Install failures show an inline per-card error message.

**Independent Test (Playwright — runs on GB10)**: `npx playwright test tests/ui-integration/tool-registry.spec.ts --grep "@US2" --reporter=list`
Assertions: `data-testid="server-card-install-btn-*"` present on uninstalled stdio card; button text changes to "Installing…" during operation (mocked slow response); after mocked success the `data-testid="server-card-error-*"` is absent; after mocked 500 response error banner appears and install button is re-enabled.

### Implementation for User Story 2

- [ ] T017 [US2] Add per-card `cardError` and `cardSuccess` local state to `apps/web/src/components/tools/ToolCard.tsx` — replace the global `SET_ERROR` dispatch for install/uninstall errors with local `cardError` state; render dismissible inline error banner at card bottom with `data-testid="server-card-error-{server_id}"`
- [ ] T018 [US2] Update install button in `apps/web/src/components/tools/ToolCard.tsx` — rename button to "Install" for stdio servers with `data-testid="server-card-install-btn-{server_id}"`; show installed version string from `server.installed_version` in the "Installed" badge (e.g., "✓ Installed v1.2.3"); update uninstall button with `data-testid="server-card-uninstall-btn-{server_id}"`; update delete/remove button with `data-testid="server-card-remove-btn-{server_id}"`
- [ ] T018a [US2] Write and run US2 Playwright assertions in `tests/ui-integration/tool-registry.spec.ts` (tagged `@US2`) using `page.route()` to mock install endpoint: test install button present; test "Installing…" state; test version shown after mocked success; test error banner after mocked 500; test error banner is dismissible. Run: `npx playwright test tests/ui-integration/tool-registry.spec.ts --grep "@US2" --reporter=list`

**Checkpoint**: `npx playwright test tests/ui-integration/tool-registry.spec.ts --grep "@US2" --reporter=list` — all US2 assertions green.

---

## Phase 5: User Story 3 — Check for Updates & Update (Priority: P3)

**Goal**: Installed stdio server cards show a "Check for Updates" button. On click, a spinner shows while the version check runs. If an update is available, an amber banner with version info and an "Update Now" button appears. Clicking Update runs the upgrade.

**Independent Test (Playwright — runs on GB10)**: `npx playwright test tests/ui-integration/tool-registry.spec.ts --grep "@US3" --reporter=list`
Assertions (all using `page.route()` mocks): Check for Updates button visible on mocked-installed card; spinner/disabled state during check; "✓ Up to date" shown when `update_available: false`; update banner with version appears when `update_available: true`; Update Now button triggers update endpoint; banner disappears after mocked success.

### Implementation for User Story 3

- [ ] T019 [US3] Add update-check UI to `apps/web/src/components/tools/ToolCard.tsx` — add local state: `isCheckingUpdate`, `updateAvailable: { installed: string; latest: string } | null`, `isUpdating`; render "↻ Check for Updates" button beside Installed badge only for stdio+installed servers; on click call `checkServerVersion()` from tools store; set `isCheckingUpdate` during call; on result set `updateAvailable` state or show inline "✓ Up to date" transient message; `data-testid="server-card-check-update-btn-{server_id}"`
- [ ] T020 [US3] Add update banner to `apps/web/src/components/tools/ToolCard.tsx` — when `updateAvailable` is set render amber-colored inline banner showing "Update available: v{installed} → v{latest}"; include "Update Now" button that calls `updateServerState()` from store; on success clear `updateAvailable` state; show in-progress state on button during update; `data-testid="server-card-update-banner-{server_id}"`, `data-testid="server-card-update-btn-{server_id}"`
- [ ] T020a [US3] Write and run US3 Playwright assertions in `tests/ui-integration/tool-registry.spec.ts` (tagged `@US3`) using `page.route()` to mock `/version-check` and `/update` endpoints: test check button present; test spinner; test up-to-date message; test update banner appears; test Update Now triggers update route; test banner clears on success. Run: `npx playwright test tests/ui-integration/tool-registry.spec.ts --grep "@US3" --reporter=list`

**Checkpoint**: `npx playwright test tests/ui-integration/tool-registry.spec.ts --grep "@US3" --reporter=list` — all US3 assertions green.

---

## Phase 6: User Story 4 — Connect to a Network MCP Server (Priority: P2)

**Goal**: Network (sse/webmcp) server cards display a "Connect" button (not "Install") and "Disconnect" (not "Uninstall"). The card copy makes clear no local software installation is required.

**Independent Test (Playwright — runs on GB10)**: `npx playwright test tests/ui-integration/tool-registry.spec.ts --grep "@US4" --reporter=list`
Assertions: sse/webmcp card shows `data-testid="server-type-badge-sse"` or `"-webmcp"`; "Connect" button present (not "Install"); no "Install" button on Network cards; after mocked connect, card shows "Connected" / "Disconnect" button.

### Implementation for User Story 4

- [ ] T021 [US4] Update action button copy in `apps/web/src/components/tools/ToolCard.tsx` — derive `isLocalServer` from `server.type === 'stdio'`; render "Install"/"Uninstall" for local servers and "Connect"/"Disconnect" for network servers; update button `data-testid` accordingly: `data-testid="server-card-connect-btn-{server_id}"` for network not-installed and `data-testid="server-card-disconnect-btn-{server_id}"` for network installed; the underlying `onInstall`/`onUninstall` handlers are unchanged (reuse existing install/uninstall API endpoints)
- [ ] T021a [US4] Write and run US4 Playwright assertions in `tests/ui-integration/tool-registry.spec.ts` (tagged `@US4`) using `page.route()` to seed an sse-type server: test Network badge visible; test Connect button present; test Install button absent; test after mocked connect server shows Disconnect. Run: `npx playwright test tests/ui-integration/tool-registry.spec.ts --grep "@US4" --reporter=list`

**Checkpoint**: `npx playwright test tests/ui-integration/tool-registry.spec.ts --grep "@US4" --reporter=list` — all US4 assertions green.

---

## Phase 7: User Story 5 — Uninstall a Local MCP Server (Priority: P3)

**Goal**: Installed stdio server cards show an "Uninstall" button. Clicking it prompts a confirmation dialog. On confirm, the server is marked not-installed and the card reverts to the "Install" state, but the entry remains in the catalog.

**Independent Test (Playwright — runs on GB10)**: `npx playwright test tests/ui-integration/tool-registry.spec.ts --grep "@US5" --reporter=list`
Assertions: Uninstall button present on mocked-installed stdio card; `page.on('dialog', d => d.accept())` listener fires on click; after mocked uninstall card shows Install button and no Installed badge; card entry still present in DOM.

### Implementation for User Story 5

- [ ] T022 [US5] Verify existing uninstall flow works end-to-end in `apps/web/src/components/tools/ToolCard.tsx` — confirm `handleUninstall` calls `onUninstall`, server entry stays in catalog (`DELETE_SERVER` is only triggered by Remove, not Uninstall), card renders "Install" button after uninstall; update `data-testid` to `server-card-uninstall-btn-{server_id}` (may already be done in T018)
- [ ] T022a [US5] Write and run US5 Playwright assertions in `tests/ui-integration/tool-registry.spec.ts` (tagged `@US5`) using `page.route()` to mock uninstall endpoint and `page.on('dialog')` to accept confirmation: test Uninstall button visible; test dialog fires; test card reverts to Install state; test card still in DOM. Run: `npx playwright test tests/ui-integration/tool-registry.spec.ts --grep "@US5" --reporter=list`

**Checkpoint**: `npx playwright test tests/ui-integration/tool-registry.spec.ts --grep "@US5" --reporter=list` — all US5 assertions green.

---

## Phase 8: Polish & Cross-Cutting Concerns

**Purpose**: Backend API tests, full regression suite, and final Playwright QA pass targeting the remote dev server.

- [ ] T023 [P] Add backend API tests in `apps/api/tests/test_mcp_api.py` — add: `test_version_check_success`, `test_version_check_not_found`, `test_version_check_network_server_returns_400`, `test_update_server_success`, `test_update_server_not_found`, `test_register_server_with_image_and_description`
- [ ] T024 [P] Finalize `tests/ui-integration/tool-registry.spec.ts` — consolidate all `@US1`–`@US5` tagged tests into a single coherent file; do NOT override `baseURL` — the existing `playwright.config.ts` (`baseURL: 'http://localhost:5173'`) is already correct since Playwright runs on the GB10; add a `@smoke` test that navigates to `/tool-registry` and asserts the page heading is visible as a basic health check
- [ ] T025 Run the full new Playwright tool-registry suite: `npx playwright test tests/ui-integration/tool-registry.spec.ts --reporter=list`
- [ ] T026 Run existing Playwright suite to confirm no regressions: `npx playwright test tests/ui-integration/ --ignore=tests/ui-integration/tool-registry.spec.ts --reporter=list`
- [ ] T027 Run full backend test suite to confirm no regressions: `cd apps/api && PYTHONPATH=src uv run pytest tests/ -v --tb=short`

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 1 (Setup)**: No dependencies — run immediately
- **Phase 2 (Foundational)**: Depends on Phase 1 — BLOCKS all user stories
- **Phase 3 (US1 — Browse)**: Depends on Phase 2 — can start as soon as T011+T012 complete
- **Phase 4 (US2 — Install)**: Depends on Phase 2 — can start in parallel with Phase 3 (different files)
- **Phase 5 (US3 — Updates)**: Depends on Phase 2 + T012 (`checkServerVersion` in store) — after T012
- **Phase 6 (US4 — Network Connect)**: Depends on Phase 2 — independent of US1/US2/US3
- **Phase 7 (US5 — Uninstall)**: Depends on Phase 2 — largely verifying existing behavior
- **Phase 8 (Polish)**: Depends on all user story phases + their Playwright tasks complete

### User Story Dependencies

- **US1 (Browse)**: Needs T004, T005, T011 — drives `ToolCard` visual additions
- **US2 (Install)**: Needs T004, T005, T007, T011 — per-card error + version in badge
- **US3 (Check Updates)**: Needs T006, T008, T009, T011, T012 — full version-check backend chain
- **US4 (Network Connect)**: Needs T004, T011 — purely UI label changes to `ToolCard`
- **US5 (Uninstall)**: Needs T004, T007, T011 — verify existing uninstall path

### Within Each User Story

- Backend changes (T004–T010) before frontend types (T011)
- Frontend types (T011) before store (T012)
- Store (T012) before components (T013–T022)
- Implementation tasks before Playwright assertion tasks (`T016a`, `T018a`, `T020a`, `T021a`, `T022a`)

### Parallel Opportunities

```
Phase 2 parallel group (all can run simultaneously after T001-T003):
  T004 (models.py)
  T005 (db.py)
  T006 (version_check.py)              — depends only on T004 completing
  T007 (router: new fields)
  T008 (router: version-check endpoint) — depends on T006
  T009 (router: update endpoint)        — depends on T006
  T010 (seed data)
  T011 (mcp-service.ts)
  T012 (tools.tsx store)               — depends on T011

User Story phase parallel groups:
  T013 (ServerTypeBadge.tsx) ← independent new file, start immediately after T011
  T023 (backend API tests)   ← fully parallel with all frontend work in Phase 8
  T024 (finalize spec file)  ← parallel with T023
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup (T001–T003)
2. Complete Phase 2 minimum: T004, T005, T010, T011 (skip T006–T009 for MVP)
3. Complete Phase 3: User Story 1 (T013–T016)
4. **STOP and VALIDATE** (terminal command on GB10): `npx playwright test tests/ui-integration/tool-registry.spec.ts --grep "@US1" --reporter=list`
5. All US1 assertions pass = MVP delivered

### Incremental Delivery

1. Setup + Foundational (T001–T012) → Full stack ready
2. US1 (T013–T016 + T016a) → Rich catalog browsing ✅ Playwright verified
3. US2 (T017–T018 + T018a) → Install with per-card errors + version display ✅ Playwright verified
4. US4 (T021 + T021a) → Network connect UX (quick win — label changes only) ✅ Playwright verified
5. US5 (T022 + T022a) → Uninstall verification ✅ Playwright verified
6. US3 (T019–T020 + T020a) → Check for updates + update banner ✅ Playwright verified
7. Phase 8 (T023–T027) → Backend tests + full regression suite

### Parallel Team Strategy

With two developers after Phase 2 is complete:
- **Developer A**: T013 → T014 → T015 → T016 → T016a (US1 visual work + Playwright)
- **Developer B**: T006 → T008 → T009 (version_check backend) → T019 → T020 → T020a (US3 + Playwright)

---

## Notes

- **No browser_subagent** — Antigravity's browser tool can't be used (it would open a browser on the local PC which can't reach the GB10's localhost). Instead, all UI verification is done by running `npx playwright test` as a **terminal command on the GB10**, where Playwright hits `localhost:5173` directly. This already works.
- The existing `playwright.config.ts` (`baseURL: 'http://localhost:5173'`) is correct as-is — do not change it.
- All story-specific tests use `page.route()` to mock API responses — this ensures tests are deterministic and don't depend on real package manager installs or network version checks.
- `[P]` tasks touch different files or have no shared dependencies — safe to run simultaneously.
- `[Story]` label maps each task to a specific user story for traceability.
- Per-card error state (T017) intentionally breaks from the current global `SET_ERROR` pattern — this is scoped to version-check/update operations only; install/uninstall/delete errors keep their current global behavior.
- The `version_check.py` subprocess approach may need adjustment if the seeded servers use package managers other than `uvx`/`npx`/`pip` — check actual CalculiX + OpenSCAD commands before implementing T006.
