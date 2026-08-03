# Research: Incremental Rivet Workflow Integration

**Branch**: `054-rivet-workflow-integration`

**Date**: 2026-08-03

**Purpose**: Record umbrella architecture decisions and isolate questions that the compatibility spike must answer with executable evidence.

## Upstream Baseline

Ironclad Rivet is an MIT-licensed TypeScript monorepo. Its public architecture separates the visual editor from reusable `@ironclad/rivet-core` and Node-oriented `@ironclad/rivet-node` packages. Rivet documents host-provided external functions, a dataset-provider interface, abort signals and process events, and remote debugging over a WebSocket server. Those seams make the proposed integration feasible, but the exact editor-host injection points and package compatibility must be proven at one pinned commit before Wright adopts production contracts.

The upstream project, editor, core package, and application package do not share a single version line. The integration therefore pins an exact source commit plus every consumed package and built-asset checksum; it does not infer compatibility from a floating `main`, `latest`, or matching-looking semantic version.

Primary upstream references:

- Repository and MIT license: <https://github.com/Ironclad/rivet>
- Host integration and `runGraphInFile`: <https://rivet.ironcladapp.com/docs/api-reference/getting-started-integration>
- External Call node: <https://rivet.ironcladapp.com/docs/node-reference/external-call>
- Remote debugging: <https://rivet.ironcladapp.com/docs/user-guide/remote-debugging>
- Plugin model: <https://rivet.ironcladapp.com/docs/user-guide/plugins/creating-plugins>
- Dataset provider behavior: <https://rivet.ironcladapp.com/docs/node-reference/load-dataset>

## Decision 1: Host the Editor as an Isolated Managed Surface

**Decision**: Build and serve a pinned Rivet editor distribution as a Wright-managed `LiveAppSurface` with its own effective origin and retained DOM lifecycle.

**Rationale**:

- Wright already has process supervision, preview routing, isolated origins, retained tabs, focus behavior, diagnostics, and close/stop semantics.
- Rivet's editor is a complete React application with its own state, design system, bundler, native abstraction, and dependency versions. Importing its components into Wright's React 19 tree would couple internal application state and make upgrades fragile.
- A managed surface preserves the requested workspace-tab experience while isolating CSS, dependencies, active content, and upstream changes.

**Alternatives rejected**:

- **Direct React component embedding**: no stable public editor-component API and high React/dependency collision risk.
- **Launch the Rivet desktop application**: loses Wright tab retention, workspace identity, browser/Docker parity, and unified policy.
- **Model Rivet as an MCP App**: Rivet is a general authoring application, not a packaged `ui://` resource attached to one MCP tool result.

## Decision 2: Replace Browser Persistence With Wright Host Adapters

**Decision**: The workspace filesystem is authoritative. The editor uses Wright-provided IO and dataset adapters backed by authenticated, revision-aware APIs.

**Rationale**:

- Browser file pickers require user gestures and expose paths/handles inconsistently.
- Browser-profile storage such as IndexedDB is not portable with a workspace, is awkward to back up or source-control, and can leak the notion of a global project catalog across workspaces.
- Host adapters permit atomic saves, conflict detection, path confinement, read-only behavior, migration, audit, and consistent browser/desktop/Docker behavior.

**Alternatives rejected**:

- **Use upstream browser storage unchanged**: violates the workspace ownership requirement.
- **Store project bodies only in SQLite/vault**: makes authored workflow review and source control opaque; workspace files are the appropriate author-owned format.
- **Mount the workspace directly into the browser/runner**: bypasses Wright path, symlink, permission, and audit controls.

**Compatibility risk**: Upstream may instantiate providers through application-global modules rather than a supported runtime injection interface. Slice 0 must prove injection. If a patch is required, it must be small, isolated, reproducible, tested against the pin, and proposed upstream when practical.

## Decision 3: Use a Supervised Node Runner

**Decision**: Run production graphs in an optional Node sidecar using pinned `@ironclad/rivet-node`; do not execute them inside the editor browser process or Wright's Python interpreter.

**Rationale**:

- The documented Node API supports project-file execution, process events, abort signals, native APIs, external functions, and remote debugger attachment.
- Node avoids browser CORS and browser-lifecycle coupling and provides the broadest official executor compatibility.
- Wright's existing process supervisor can impose generation identity, time/resource limits, health checks, and full process-tree cleanup across native and Docker environments.

**Alternatives rejected**:

- **Browser executor as production runtime**: tied to a visible editor, weaker lifecycle control, CORS differences, and no reliable headless operation.
- **Embed JavaScript in Python**: adds an unofficial compatibility layer and moves process isolation into the control plane.
- **Shell out to an ungoverned Rivet CLI**: insufficient typed lifecycle/event/authorization integration.

## Decision 4: Integrate Wright Through External Calls or an Approved Plugin

**Decision**: Wright engineering operations enter through a deliberately small Rivet surface, backed by a runner bridge that always calls Wright's `GatewayService`. Slice 0 chooses between built-in External Call nodes, a Wright plugin, or a thin combination based on editor ergonomics and runtime evidence.

**Rationale**:

- External functions are an official host integration seam and work with remote debugging.
- A Wright plugin can provide better typed node editors and output ports but expands compatibility, packaging, and supply-chain surface.
- Both can be implemented so the graph contains only a logical operation and inputs; Wright server-side context supplies authority.

**Non-negotiable boundary**: Rivet project MCP configuration, node metadata, plugin settings, or client messages never authorize an engineering call. Direct Rivet MCP is disabled by default; all approved tool execution is rediscovered and authorized by Wright at call time.

## Decision 5: Keep Authored Files Separate From Operational Records

**Decision**:

- Authored project: `workflows/<slug>/workflow.rivet-project`
- Authored datasets/attachments: below `workflows/<slug>/`
- Private recoverable editor metadata: `.wright/rivet/` through the workspace metadata service
- Run artifacts/recordings: existing workspace artifact/vault conventions, indexed by run ID
- Secrets: Wright secret provider only

**Rationale**: Users can review and source-control authored intent, while large/immutable outputs and operational indexes keep existing Wright retention and access behavior. Ephemeral PIDs, ports, debugger endpoints, approvals, and credentials are never restored as durable truth.

## Decision 6: Split Authoring, Execution, and Publication

**Decision**: The editor, runner, lightweight workflow operations, and optional agent publication are separate slices and contracts.

**Rationale**:

- Headless execution is valuable and testable without the editor.
- The editor can be disabled while storage and execution remain sound.
- Routine users should not load a full IDE to run a reviewed workflow.
- Agent publication changes the attack surface and deserves a separate P2 approval, typed schema, and revocation model.

## Decision 7: Pin and Vendor for Offline Reproducibility

**Decision**: Wright packages a reproducible editor build and approved runtime dependencies from exact inputs. Runtime downloads of npm plugins, CDN assets, fonts, or editor code are prohibited on the supported offline path.

**Rationale**: Wright promises offline/native/Docker parity. Rivet supports arbitrary npm plugins and a large dependency graph; accepting floating installs would defeat supply-chain review and deterministic packaging.

**Update policy**: Every pin change reruns the compatibility suite, adapter patch application, license/SBOM scan, schema fixtures, remote debugger tests, Node execution tests, offline network-denial tests, and native/Docker package checks. A failed update remains on the previous supported pin.

## Decision 8: Treat Risky Nodes as Independent Policy Capabilities

**Decision**: Administrators can independently disable code, arbitrary HTTP, direct MCP, unapproved plugins, filesystem nodes, project references, graph upload, and agent publication. Safe defaults disable capabilities that bypass Wright mediation.

**Rationale**: Rivet's flexibility includes arbitrary HTTP methods, code execution with hang risk, file operations, plugins, project references, and MCP. Editor isolation alone does not govern actions performed by the Node executor.

## Questions Assigned to Slice 0

The umbrella plan is not blocked by these questions because slice 0 exists specifically to answer them before production implementation:

1. Which exact upstream editor commit and published core/node package versions form one tested compatibility set?
2. Can IO, dataset, native API, plugin registry, and debugger configuration be injected without patching? If not, what is the smallest stable patch?
3. Can the editor be built for a non-root base path and strict Wright CSP without runtime network access?
4. Which editor operations still assume Tauri, native file dialogs, global directories, or browser IndexedDB?
5. Does the remote debugger protocol provide the event, pause, user-input, binary-data, reconnect, and abort behavior Wright needs, or must Wright use a separate runner event channel?
6. Are External Call nodes sufficient for typed Wright operations and editor discovery, or is a pinned Wright plugin justified?
7. What are the transitive license, vulnerability, bundle-size, memory, startup, and platform impacts?
8. What upstream contribution or maintained-fork strategy minimizes long-term patch burden?

## Feasibility Conclusion

The integration is technically feasible because Rivet exposes reusable core/Node execution, host external functions, dataset providers, native APIs, events/abort, and remote debugging, while Wright already supplies the missing workspace, UI-surface, process, policy, approval, artifact, and observability foundations. The largest uncertainty is not graph execution; it is how cleanly the complete editor application accepts host-owned persistence and native abstractions. The compatibility spike is therefore the mandatory first implementation slice and the go/no-go gate for the rest of the program.
