# Contract: Rivet Editor Bootstrap and Host Adapters

**Owner slices**: `rivet-editor-host-adapters`, then `rivet-workspace-tab` for presentation lifecycle

**Depends on**: workspace storage contract and existing Workspace Surfaces contracts

## Boundary

The Rivet editor is untrusted active content running on a Wright-managed isolated origin. It receives only short-lived capabilities needed to edit one workspace. Wright owns the surface, workspace binding, storage, runtime generation, policy, and external navigation.

## Bootstrap Sequence

1. Authenticated Wright UI requests/open the Workflows surface for the active workspace.
2. `workspace_service` creates or resumes a retained `LiveAppSurface` intent and starts/attaches the pinned editor runtime/build.
3. The preview origin serves a bootstrap document with an opaque, single-surface presentation identity.
4. The editor requests bootstrap data through the bound origin/channel.
5. Wright validates user, session, workspace, surface, origin, editor build, expiry, and runtime generation.
6. Wright returns only typed configuration for the active workspace and selected workflow.
7. The editor initializes Wright IO/dataset/native adapters and reports ready/dirty/diagnostic state.

## Bootstrap Response Shape

The owning slice will publish an exact schema. It must include at least:

- contract version;
- workspace and surface opaque identities;
- runtime generation and editor build compatibility ID;
- selected workflow identity/revision, if authorized;
- storage API base/capability reference scoped to the presentation;
- dataset API capability;
- permitted editor operations and effective limits;
- optional remote-debugger capability for the current generation;
- locale/theme/accessibility preferences safe to disclose;
- trace/correlation identity;
- expiry and renewal behavior.

It must not include filesystem roots, reusable bearer tokens, raw secrets, approval grants, unrestricted MCP endpoints, arbitrary upstream authorities, or credentials valid beyond the surface/generation/session.

## Host Adapter Responsibilities

### `WrightIOProvider`

- List/open/create/save/save-as/rename/delete through workflow IDs and revisions.
- Surface structured conflicts and recoverable states to the editor.
- Never expose a native absolute path or browser file handle as authority.
- Reject unsupported editor/project compatibility before modification.

### `WrightDatasetProvider`

- Bind all dataset operations to the selected workflow and workspace.
- Apply row/value/count/size limits and version validation.
- Return revisions and conflicts consistently with project saves.
- Keep browser IndexedDB non-authoritative; a local cache may be disposable only.

### `WrightNativeApi`

- Implement only approved functions such as safe external-open requests, clipboard/file dialogs if policy permits, bounded file selection/import, and diagnostics.
- Delegate external navigation to Wright's host adapter.
- Deny process execution, unrestricted filesystem paths, global plugin directories, arbitrary shell commands, and credential access.
- Return explicit unsupported errors for unimplemented upstream native calls.

## Message Security

- Check source window, exact origin, contract version, correlation ID, workspace, surface, session, and runtime generation on every bridge message.
- Use schema-validated request/response envelopes with size and rate limits.
- Ignore/reject stale, duplicate, unsolicited, cross-surface, or cross-workspace messages.
- Do not put capabilities in query strings, logs, referrers, workflow files, or recoverable editor state.
- Renew capabilities through the authenticated control plane; editor heartbeat alone is not authorization.

## Retention and Dirty State

- Switching tabs keeps the editor DOM/runtime mounted within existing retention limits.
- The editor emits `clean`, `dirty`, `autosaving`, `conflicted`, and `recoverable` state transitions.
- Close/eviction/stop consults dirty state and provides save, discard, cancel, or recovery behavior according to the slice UX contract.
- Eviction under pressure never silently drops the sole copy of an unsaved change; bounded recovery must complete or the user must make an explicit choice.
- Closing a presentation and stopping its runtime remain separate exact-once operations.

## Remote Debugger

- The editor receives only a Wright-created debugger capability for the active workspace/runtime generation.
- The endpoint cannot select a host or port supplied by the project or browser.
- The backend/runner rejects stale generations and cross-workspace connections.
- Debug output is bounded/redacted and does not expand execution authority.
- Loss of the debugger does not cancel a production run unless the user explicitly cancels it; loss of the runner produces a reconciled run outcome.

## Build and Compatibility

- Exact upstream commit, package versions, lockfile, patch set, build command, asset manifest, checksums, and licenses are recorded.
- No runtime CDN, npm registry, font, plugin, or source-map dependency is required.
- Base path, CSP, isolated origin, browser cache, upgrade/downgrade, and unsupported-build behavior are tested.
- If a maintained patch is required, CI proves it applies cleanly only to the pinned source and fails closed on drift.

## Required Contract Tests

- Valid and invalid bootstrap across workspace/user/session/origin/generation/build boundaries.
- All adapters against the real pinned editor build.
- Save conflict, autosave, recovery, read-only, moved/deleted workspace, and unsupported format.
- Cross-frame/cross-origin/stale/replayed/oversized bridge messages.
- Retained 100-switch flow, dirty eviction, close versus stop, focus/keyboard/resize/accessibility.
- No-network/offline assets and clean degraded state when editor or runner is absent/incompatible.
- Browser and Hermes external-navigation policy.
