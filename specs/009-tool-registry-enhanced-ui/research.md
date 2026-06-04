# Research: Enhanced Tool Registry UI

**Feature**: `009-tool-registry-enhanced-ui`
**Date**: 2026-06-04
**Status**: Complete — all questions resolved

---

## 1. Deployment Type Differentiation (Local vs. Network)

**Decision**: Use the existing `type` field (`stdio` = Local, `sse`/`webmcp` = Network). No new DB column needed.

**Rationale**: The `stdio` type always means a local subprocess. The `sse` and `webmcp` types always mean a remote endpoint. The mapping is already in the data model and is semantically correct.

**Alternatives considered**: A separate `deployment_type` column was considered but rejected as redundant.

---

## 2. Image / Logo Strategy

**Decision**: Store `image_url` and `source_url` as optional text columns in `mcp_servers`. Frontend uses `image_url` directly in an `<img>` tag. On load error, renders a styled single-letter fallback avatar.

**Rationale**:
- GitHub avatar URLs follow a predictable pattern: `https://github.com/{owner}.png?size=64`
- Pre-seeded servers (CalculiX, OpenSCAD) will have their `image_url` values set during DB seed
- User-registered custom servers can optionally provide `source_url`; if it is a GitHub URL, the avatar can be derived on the frontend with a simple regex
- Fetching GitHub API at register time would require network access and API rate limits — unacceptable for offline-first

**Fallback**: CSS-styled `<div>` showing first character of server name in a gradient circle. Never shows a broken `<img>` tag.

---

## 3. Version Check Strategy

**Decision**: Backend `version_check.py` dispatches subprocess calls based on the command prefix:
- `uvx` command prefix → `uvx {package} --version`
- `npx` prefix → `npm show {package} version` (latest) vs `npm list {package} --depth=0` (installed)
- `python` / `uv run` prefix → `pip show {package}` (installed) + `pip index versions {package}` (latest)
- Unknown prefix → returns `{"error": "unsupported_package_manager"}`

**Rationale**: These are the package managers already in use by the existing seeded servers (CalculiX uses uvx, OpenSCAD uses npm/uvx). Subprocess approach is offline-capable for local version reads; the latest-version check may need internet access.

**Alternatives considered**: A registry of known server versions stored in SQLite was considered but rejected — it would require manual maintenance and go stale.

**Timeout**: 10-second `asyncio.wait_for` timeout to prevent blocking the API.

---

## 4. Network Server Connect Semantics

**Decision**: Reuse the existing `POST /servers/{id}/install` endpoint for Network servers. The backend already handles `sse`/`webmcp` server types. The UI renames "Install" → "Connect" and "Uninstall" → "Disconnect" based on `server.type`.

**Rationale**: The backend install operation for `sse`/`webmcp` servers simply marks `is_installed=True` and runs `engine.start_server()` which initiates the SSE connection. The semantics are identical — no new endpoint needed.

---

## 5. Per-Card vs. Global Error State

**Decision**: Version-check errors and update errors use **per-card local state** (`useState` in `ToolCard`). Install/uninstall/delete errors continue using the global `tools.tsx` dispatch (existing behavior).

**Rationale**: Per-card state for version checks prevents one card's check-for-updates failure from disrupting the entire registry view. Install errors are already surfaced globally and this behavior is preserved to avoid regressions.

---

## 6. Update Mechanism

**Decision**: The `POST /api/mcp/servers/{id}/update` endpoint calls `version_check.update_server()` which re-runs the install command (e.g., `uvx install --upgrade {package}`). On success, `installed_version` in the DB is updated and the new version is returned to the frontend.

**Rationale**: Package managers already handle upgrade idempotently. Re-running install with `--upgrade` is the standard pattern for uvx/pip/npm.

---

## 7. `data-testid` Naming Convention

**Decision**: Follow the `{component}-{element}-{qualifier}` convention established in the 008 plan:
- `server-card-logo-{id}`
- `server-type-badge-{type}`
- `server-card-description-{id}`
- `server-card-check-update-btn-{id}`
- `server-card-update-banner-{id}`
- `server-card-update-btn-{id}`
- `tool-registry-register-btn`
- `tool-registry-search-input`
- `tool-registry-category-{cat}`
