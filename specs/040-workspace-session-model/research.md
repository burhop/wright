# Research: Workspace Session Model

## Decision: Workspace owns many agent sessions through an explicit association

**Rationale**: The current `engineering_workspaces.session_id` field creates a one-to-one relationship and forces session creation or selection to rewrite workspace identity. A separate association allows session lists, history, and active chat selection to vary while workspace settings and tool configuration remain stable.

**Alternatives considered**:

- Continue overwriting `engineering_workspaces.session_id`: rejected because it loses discoverability of previous sessions and causes workspace state resets.
- Store sessions only in browser localStorage: rejected because sessions must survive browser changes and backend/Hermes state must remain authoritative.
- Derive workspace sessions solely from agent backend workspace path: useful as a reconciliation fallback, but insufficient because Wright needs local metadata, migration, archive/deletion handling, and stable workspace scoping when the agent backend is temporarily unavailable.

## Decision: Keep workspace tool enablement on workspace identity

**Rationale**: Tool enablement describes what the workspace is allowed to use, not what a particular chat transcript is allowed to use. Every session in a workspace should inherit the same MCP set.

**Alternatives considered**:

- Per-session tools: rejected because it would make session switching change engineering capabilities unexpectedly.
- Global installed-server status only: rejected because unrelated installed tools must not be reported as current-workspace failures.

## Decision: Preserve legacy `session_id` while migrating to association table

**Rationale**: Existing code and local databases currently depend on `engineering_workspaces.session_id`. Keeping it temporarily as `last_active_session_id` compatibility data reduces migration risk while new code moves to workspace-scoped lookups.

**Alternatives considered**:

- Drop or rename the field immediately: rejected because it increases migration blast radius and can break existing dashboard flows.
- Leave field untouched forever as the source of truth: rejected because it preserves the bug.

## Decision: Session switching is chat-only UI state

**Rationale**: The user's workspace context includes file tree, open tabs, viewer state, settings, and enabled tools. Changing the selected chat session should not trigger the same reset behavior as changing workspaces.

**Alternatives considered**:

- Keep layout keyed by session: rejected because it causes the middle panel to reset during normal chat selection.
- Keep one active session globally across all workspaces: rejected because workspaces need independent recent session state.

## Decision: MCP status should be workspace-scoped and gateway-aware

**Rationale**: The Wright gateway exposes tools for the active workspace. Status must answer whether the current workspace's enabled tools are available through that path, not whether every installed registry row is active.

**Alternatives considered**:

- Report all installed inactive servers: rejected because it creates false warnings for tools not enabled in the workspace.
- Ignore server runner state entirely: rejected because users need clear errors when required MCPs cannot start.
