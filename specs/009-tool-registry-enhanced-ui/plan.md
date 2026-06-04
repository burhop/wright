# Implementation Plan: Enhanced Tool Registry UI

**Branch**: `009-tool-registry-enhanced-ui` | **Date**: 2026-06-04 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `/specs/009-tool-registry-enhanced-ui/spec.md`

## Summary

Elevate the Tool Registry page from a plain list of cards into a rich, marketplace-style catalog. Each MCP server card will display a logo/avatar, a detailed description, and a clear visual badge distinguishing **Local** servers (require local install: `stdio` type) from **Network** servers (require only a URL connection: `sse` / `webmcp` types). Installed Local servers gain a **Check for Updates** button backed by a new backend version-check endpoint; when an update is available an inline banner with an **Update** button appears. All install/uninstall/update/connect operations show in-progress states and inline error messages. The backend adds two new endpoints: `GET /api/mcp/servers/{id}/version-check` and `POST /api/mcp/servers/{id}/update`. The data model gains four new fields on `McpServer`: `image_url`, `description`, `source_url` (GitHub / origin URL), and `installed_version`.

## Technical Context

**Language/Version**: Python 3.13 (backend), TypeScript 6.0, React 19 (frontend)

**Primary Dependencies**: FastAPI ≥0.115, Pydantic v2, structlog ≥24.1, React 19, react-router-dom v6, Vanilla CSS design tokens (no Tailwind)

**Storage**: SQLite with WAL mode (existing `mcp_servers` table — schema migration adds 4 columns)

**Testing**: pytest (backend API tests), Playwright (Tier 2 UI integration), Vitest (Tier 1 component tests)

**Target Platform**: Linux local host. Target UI URL: `http://promaxgb10-9666:5173/tool-registry`

**Project Type**: Modular Monorepo web application (FastAPI backend + React frontend)

**Performance Goals**: Card renders (including image load with fallback) must not delay main content. Version-check calls are on-demand (user-triggered), not automatic on page load.

**Constraints**: Offline-first — image loading must degrade gracefully (fallback placeholder). No new background database servers. Version checks use subprocess calls (e.g., `uvx`, `pip`, `npm`) on the local machine, so network timeouts are acceptable for `sse`/`webmcp` type version checks.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| # | Gate | Status | Evidence |
|---|------|--------|----------|
| 1 | FastAPI backend, zero business logic in routes | ✅ Pass | New version-check logic extracted to `tool_registry` package. Router handlers stay thin. |
| 2 | Modular Monorepo with strict boundaries | ✅ Pass | New fields added to `packages/tool_registry`. New endpoints added to `apps/api` router. Frontend changes in `apps/web`. |
| 3 | Offline-First Mandate | ✅ Pass | Image URLs stored in DB. Fallback placeholder shown on load error. Version checks are local subprocess calls. |
| 4 | Agent Abstraction (Adapter Pattern) | ✅ Pass | No changes to BaseAgentEngine. |
| 5 | Zero-server databases | ✅ Pass | SQLite only — 4 columns added via migration, no new tables/servers. |
| 6 | Local authentication | ⚠️ Out of scope | Authentication is a separate feature. |
| 7 | Template Method for tools | ✅ Pass | No changes to tool patterns. |
| 8 | Atomic design (Tokens → Primitives → Components) | ✅ Pass | All new UI uses existing CSS token variables. New `ServerTypeBadge` component follows atomic pattern. |
| 9 | Tier 1/2/3 testing pyramid | ✅ Will Fix | New Vitest tests for `ToolCard` (enhanced), new Playwright tests for install/update/connect flows. |
| 10 | OpenTelemetry tracing + structured JSON logging | ✅ Pass | New endpoints use `@traced` decorator and `structlog`. |
| 11 | Phase isolation + branch discipline | ✅ Pass | Working on `009-tool-registry-enhanced-ui`; plan approved before implementation. |

## Project Structure

### Documentation (this feature)

```text
specs/009-tool-registry-enhanced-ui/
├── spec.md              # Feature specification
├── plan.md              # This file
├── research.md          # Phase 0 research output
├── data-model.md        # Phase 1 data model output
├── contracts/           # Phase 1 API contracts
│   └── mcp-version-check.md
└── checklists/
    └── requirements.md  # Quality validation checklist
```

### Source Code (repository root)

```text
# Backend — packages/tool_registry (core data model + business logic)
packages/tool_registry/src/tool_registry/
├── models.py                  # [MODIFY] Add image_url, description, source_url, installed_version fields
├── db.py                      # [MODIFY] Update insert_server/update_server, add migration for 4 new columns; add structlog
└── version_check.py           # [NEW] Version-check + update logic for stdio servers

# Backend — API layer
apps/api/src/api/routers/
└── mcp.py                     # [MODIFY] Add McpServerCreate fields, GET /{id}/version-check, POST /{id}/update endpoints

# Frontend — Services
apps/web/src/services/
└── mcp-service.ts             # [MODIFY] Add image_url/description/source_url/installed_version to McpServer; add checkVersion(), updateServer() methods

# Frontend — Store
apps/web/src/store/
└── tools.tsx                  # [MODIFY] Add checkServerVersion(), updateServerState() actions; UPDATE_SERVER handles new fields

# Frontend — Components
apps/web/src/components/
├── tools/
│   ├── ToolCard.tsx           # [MODIFY] Add logo, description, Local/Network badge, Check for Updates, Update banner, per-card error state
│   └── ServerTypeBadge.tsx    # [NEW] Atomic badge component: "Local" (stdio) vs "Network" (sse/webmcp)
└── pages/
    └── ToolRegistryPage.tsx   # [MODIFY] Update filter tabs to include "Local"/"Network" type filter; add data-testid attributes

# Frontend — Tests (Tier 1 — Vitest)
apps/web/src/test/components/
└── ToolCard.test.tsx          # [MODIFY] Add tests for new logo, badge, update check, update banner, per-card error

# Playwright — Tests (Tier 2)
tests/ui-integration/
└── tool-registry.spec.ts      # [NEW] Full flow: browse, install, check-for-updates, update, network-connect, uninstall
```

**Structure Decision**: Follows the existing modular monorepo layout. Business logic for version-checking is placed in `packages/tool_registry` so it is accessible outside the API layer if needed. The API router stays thin. No new packages are required.

## Complexity Tracking

No constitution violations requiring justification.

---

## Proposed Changes (by Component)

### Component 1: Data Model — `packages/tool_registry`

#### [MODIFY] [models.py](file:///home/burhop/repos/wright/packages/tool_registry/src/tool_registry/models.py)

Add four optional fields to `McpServer` and `McpServerCreate`:

- `image_url: Optional[str] = None` — URL to the server's logo/avatar (GitHub avatar, project logo, etc.)
- `description: Optional[str] = None` — Human-readable description of what the server does and what installing it means
- `source_url: Optional[str] = None` — Origin URL (GitHub repo, npm package page, etc.) used to derive `image_url` if not set explicitly
- `installed_version: Optional[str] = None` — Version string of the currently installed package (e.g., `"1.2.3"`)

The `type` field already encodes deployment type (`stdio` = Local, `sse`/`webmcp` = Network) — no new field needed.

#### [MODIFY] [db.py](file:///home/burhop/repos/wright/packages/tool_registry/src/tool_registry/db.py)

- Add SQLite migration in `_get_conn` (or a dedicated `migrate_db` function called at startup): `ALTER TABLE mcp_servers ADD COLUMN image_url TEXT`, `ADD COLUMN description TEXT`, `ADD COLUMN source_url TEXT`, `ADD COLUMN installed_version TEXT` — each wrapped in a `try/except` to be idempotent.
- Update `_row_to_server` to read the four new columns.
- Update `insert_server` and `update_server` to write the four new fields.
- Replace `import logging` with `structlog.get_logger()`.

#### [NEW] [version_check.py](file:///home/burhop/repos/wright/packages/tool_registry/src/tool_registry/version_check.py)

Business logic for checking and performing updates on `stdio`-type servers:

```python
async def check_server_version(server: McpServer) -> dict:
    """
    Returns {"installed": "1.2.3", "latest": "1.4.0", "update_available": True}
    Dispatches based on command prefix: uvx → uvx, npx → npm, python/pip → pip
    Returns {"error": "..."} on failure or unsupported type.
    """

async def update_server(server: McpServer) -> dict:
    """
    Runs the appropriate package manager upgrade command.
    Returns {"installed_version": "1.4.0", "success": True} or {"error": "..."}
    """
```

- Uses `asyncio.create_subprocess_exec` for subprocess calls (non-blocking).
- 10-second timeout enforced with `asyncio.wait_for`.
- Only supports `stdio` type; returns `{"error": "not_applicable"}` for `sse`/`webmcp`.

---

### Component 2: Backend API — `apps/api/src/api/routers/mcp.py`

#### [MODIFY] [mcp.py](file:///home/burhop/repos/wright/apps/api/src/api/routers/mcp.py)

**Extend `McpServerCreate`** to include `image_url`, `description`, `source_url` optional fields (passed through to `insert_server`).

**Add two new endpoints**:

```python
# GET /api/mcp/servers/{server_id}/version-check
@router.get("/servers/{server_id}/version-check")
@traced("mcp.server.version_check")
async def version_check_endpoint(server_id: str, engine: McpEngine = Depends(get_mcp_engine)):
    """
    Returns: {"installed": "1.2.3", "latest": "1.4.0", "update_available": True}
    Returns 400 for non-stdio servers (not applicable).
    Returns 404 if server not found.
    """

# POST /api/mcp/servers/{server_id}/update
@router.post("/servers/{server_id}/update")
@traced("mcp.server.update")
async def update_server_endpoint(server_id: str, engine: McpEngine = Depends(get_mcp_engine)):
    """
    Runs package manager upgrade. On success:
    - Updates installed_version in database
    - Returns ServerInstallResponse with new version in metadata
    Returns 400 for non-stdio servers.
    Returns 404 if server not found.
    """
```

Both endpoints use `@traced` for OTel and `structlog` for logging (consistent with existing endpoints).

---

### Component 3: Frontend Service — `apps/web/src/services/mcp-service.ts`

#### [MODIFY] [mcp-service.ts](file:///home/burhop/repos/wright/apps/web/src/services/mcp-service.ts)

- Extend `McpServer` interface with: `image_url?: string`, `description?: string`, `source_url?: string`, `installed_version?: string`
- Add `checkServerVersion(serverId: string): Promise<VersionCheckResult>` method
- Add `updateServer(serverId: string): Promise<{ installed_version: string }>` method
- `VersionCheckResult: { installed: string | null; latest: string | null; update_available: boolean; error?: string }`

---

### Component 4: Frontend Store — `apps/web/src/store/tools.tsx`

#### [MODIFY] [tools.tsx](file:///home/burhop/repos/wright/apps/web/src/store/tools.tsx)

- Add two new actions to `ToolsAction`: `SET_SERVER_VERSION_CHECK` and `UPDATE_SERVER_VERSION`
- Add `checkServerVersion(serverId: string): Promise<VersionCheckResult>` — calls service, does **not** mutate global state (returns result directly for card-local state management; per-card state avoids global loading conflicts)
- Add `updateServerState(serverId: string): Promise<void>` — calls service, dispatches `UPDATE_SERVER` with new `installed_version`

---

### Component 5: Frontend Components

#### [NEW] [ServerTypeBadge.tsx](file:///home/burhop/repos/wright/apps/web/src/components/tools/ServerTypeBadge.tsx)

Atomic primitive component:

```tsx
interface ServerTypeBadgeProps {
  type: 'stdio' | 'sse' | 'webmcp';
}
```

- `stdio` → renders **"⬡ Local"** badge in amber/orange: `rgba(251, 146, 60, 0.15)` background, `#fb923c` border/text
- `sse` / `webmcp` → renders **"⚡ Network"** badge in cyan: `rgba(56, 189, 248, 0.15)` background, `var(--color-secondary)` border/text
- Includes tooltip (HTML `title` attribute) explaining what each type means
- `data-testid="server-type-badge-{type}"`

#### [MODIFY] [ToolCard.tsx](file:///home/burhop/repos/wright/apps/web/src/components/tools/ToolCard.tsx)

Major UI enhancement to each server card:

**Header row** — Add server logo/avatar:
- Render `<img src={server.image_url} ... />` in a 48×48 rounded container at card top-left
- `onError` handler sets `imgError` state → renders a fallback `<div>` containing the first letter of the server name in a styled circle
- `data-testid="server-card-logo-{server_id}"`

**Type badge** — Insert `<ServerTypeBadge type={server.type} />` beneath the server name

**Description** — Render `server.description` below the badge in a `0.85rem` muted text block (max 3 lines, `line-clamp` via CSS)

**Per-card error state** — Replace global `SET_ERROR` dispatch for per-card errors with local `cardError` state. Inline error banner at card bottom (dismissible).

**Check for Updates button** (Local servers only, when `is_installed === true`):
- Renders "↻ Check for Updates" button beside the Installed badge
- On click: sets `isCheckingUpdate` local state → calls `checkServerVersion()` → shows result
- Result states: `{ update_available: false }` → shows "✓ Up to date" toast; `{ update_available: true }` → shows update banner

**Update banner** (shown when `updateAvailable` local state is set):
- Amber-colored inline banner: "Update available: vX.Y.Z → vA.B.C"
- "Update Now" button → calls `updateServerState()` → on success clears banner, shows new version
- `data-testid="server-card-update-banner-{server_id}"`
- `data-testid="server-card-update-btn-{server_id}"`

**Network server Connect flow** (`sse`/`webmcp` when `!is_installed`):
- Renders "Connect" button instead of "Install"
- Connect calls the existing `installServerState` (the backend semantics are the same)
- Card copy changes from "Install" to "Connect" and from "Uninstall" to "Disconnect"
- `data-testid="server-card-connect-btn-{server_id}"`

**New `data-testid` attributes**:
- `server-card-logo-{id}`
- `server-type-badge-{type}`
- `server-card-description-{id}`
- `server-card-check-update-btn-{id}`
- `server-card-update-banner-{id}`
- `server-card-update-btn-{id}`
- `server-card-connect-btn-{id}`
- `server-card-install-btn-{id}` (renamed from unlabelled button)
- `server-card-uninstall-btn-{id}`
- `server-card-remove-btn-{id}`

#### [MODIFY] [ToolRegistryPage.tsx](file:///home/burhop/repos/wright/apps/web/src/components/pages/ToolRegistryPage.tsx)

- **Filter sidebar** — Add "Local" and "Network" as filter options alongside existing categories. Update `categories` array and `filteredServers` logic to support type-based filtering (`server.type === 'stdio'` for Local, `['sse', 'webmcp']` for Network).
- **data-testid** — Add:
  - `data-testid="tool-registry-register-btn"` on the "+ Register Custom Tool" button
  - `data-testid="tool-registry-search-input"` on the search field
  - `data-testid="tool-registry-category-{cat}"` on each filter button
  - `data-testid="tool-registry-server-card-{id}"` (delegates to ToolCard's existing `data-testid`)

---

### Component 6: Backend Tests (pytest)

#### [MODIFY] [test_mcp_api.py](file:///home/burhop/repos/wright/apps/api/tests/test_mcp_api.py)

Add:
- `test_version_check_success` — GET `/servers/{id}/version-check` returns `update_available` field
- `test_version_check_not_found` — returns 404
- `test_version_check_network_server_returns_400` — `sse` type server returns 400
- `test_update_server_success` — POST `/servers/{id}/update` returns updated version
- `test_update_server_not_found` — returns 404
- `test_register_server_with_image_and_description` — new fields persist and are returned in list

---

### Component 7: Playwright Tests (Tier 2)

#### [NEW] [tool-registry.spec.ts](file:///home/burhop/repos/wright/tests/ui-integration/tool-registry.spec.ts)

```typescript
test.describe('Tool Registry Enhanced UI', () => {
  test('should display server cards with logo, badge, and description')
  test('should show Local badge for stdio servers')
  test('should show Network badge for sse servers')
  test('should filter servers by Local/Network type')
  test('should search and filter simultaneously')
  test('should show fallback image on logo error')
  test('should register and show new server with description')
  test('should install a local server (shows Install → Installing → Installed)')
  test('should show Check for Updates for installed local server')
  test('should show update banner when update is available (mocked)')
  test('should show error on install failure (mocked API 500)')
  test('should uninstall a local server with confirmation')
  test('should show Connect button for network servers')
  test('should show empty state when search yields no results')
})
```

Uses Playwright `page.route()` to mock API responses for error states and update-available scenarios.

---

## Verification Plan

### Automated Tests

1. **Backend API tests**: `cd apps/api && PYTHONPATH=src uv run pytest tests/test_mcp_api.py -v --tb=short`
   - All existing + 6 new tests must pass

2. **Frontend component tests**: `cd apps/web && npx vitest run src/test/components/ToolCard.test.tsx`
   - Covers: logo render, fallback render, badge render, check-updates click, update banner display

3. **Playwright UI integration**: `npx playwright test tests/ui-integration/tool-registry.spec.ts --headed`
   - All 14 test cases must pass
   - Existing `mcp-directory.spec.ts` must continue passing unchanged

4. **Line count check**: Confirm `mcp.py` router stays under 400 lines after additions

### Manual Verification

1. Open `http://promaxgb10-9666:5173/tool-registry`
   - Verify CalculiX Simulation card shows logo (or fallback), description, and "Local" amber badge
   - Verify any `sse`-type server shows cyan "Network" badge
2. Click "+ Register Custom Tool" → fill in description field → verify card shows description text
3. Install a server → verify "Installed" badge with version appears
4. Click "Check for Updates" → verify spinner → verify result state
5. Uninstall → confirm dialog → verify card returns to "Not Installed" with Install button
6. Search "calc" → verify only matching cards shown
7. Click "Local" filter → verify only `stdio` servers shown
8. Load the page, kill network for an image URL → verify fallback placeholder renders without layout break
