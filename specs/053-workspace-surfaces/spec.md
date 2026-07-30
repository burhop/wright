# Feature Specification: Workspace Surfaces

**Feature Branch**: `053-workspace-surfaces`

**Created**: 2026-07-30

**Status**: Approved requirements; implementation pending

**Input**: User description: "Build a professional way for Wright to host and interact with Python graphics, MCP-provided user interfaces, BREP, WebMCP, and other managed web applications inside the workspace or in the user's browser. Keep chat usable beside a maximized surface, make graph creation approachable to engineers with little programming experience, and provide complete security, testing, documentation, and examples."

## Clarifications

### Session 2026-07-30

- Q: When Wright did not launch an application itself, which endpoints may become managed Workspace Surfaces? → A: Any URL may be opened after explicit approval only as a direct-navigation, view-only surface; managed capabilities require a verified declaration.
- Q: What scope should Wright use when remembering Open in panel versus Open in browser? → A: Remember it per user, workspace, and surface source, with source policy overriding an invalid choice.
- Q: What should happen to a Wright-owned managed app after its last presentation becomes inactive? → A: Prefer the app's declared lifetime policy; when omitted, keep it running until workspace closure.
- Q: How should wright.display(...) handle HTML and JavaScript produced by Python? → A: Sanitize ordinary HTML by default, use typed data for interactive renderers such as Plotly, and require explicit isolated unprivileged mode for active HTML; declared web apps retain full JavaScript support.
- Q: How long may approval for a privileged surface capability persist? → A: Use risk-tiered persistence: low-risk declared capabilities may be remembered for the exact user, workspace, source, and source version; high-risk or mutating capabilities default to one operation or instance.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Vibe-Code a Graph in the Workspace (Priority: P1)

An engineer with little programming experience asks Wright to create a graph, or copies a short documented Python example, runs it, and sees the result in a workspace tab without learning browser programming or building a web server. The engineer can keep chatting, change the data or graph description, rerun the program, and see the same surface update.

**Why this priority**: This is the most accessible, frequently demonstrated path to visual output and establishes the minimum useful surface experience.

**Independent Test**: Starting from a standard Wright installation and a new workspace, follow the beginner graph example to render a labeled line graph, change one data value, rerun it, and verify that the visible result updates without any undocumented setup.

**Acceptance Scenarios**:

1. **Given** a new workspace and a supported Python environment, **When** the engineer runs the documented beginner line-graph example, **Then** Wright opens a labeled graph in a workspace surface and leaves chat usable.
2. **Given** an open graph surface, **When** the engineer changes the source data and reruns the program, **Then** Wright updates the existing logical output or clearly opens a new revision according to the user's chosen behavior.
3. **Given** ordinary Python collections or common tabular data, **When** the engineer requests a line, bar, scatter, or histogram view, **Then** the supported display interface accepts the data without requiring browser-language code.
4. **Given** invalid data or display options, **When** rendering fails, **Then** the engineer sees an actionable error that identifies the failing input and links to a working example.
5. **Given** no live interaction is requested, **When** the graph is rendered, **Then** the result remains viewable after the Python process exits.

---

### User Story 2 - Open an Application in the Panel or Browser (Priority: P1)

An engineer starts BREP or another web-based application through Wright or an MCP server and chooses whether to show it in a workspace panel or open it in the system browser. Both presentations connect to the same authorized application instance, and the engineer can change presentation without relaunching or losing application state when the application supports it.

**Why this priority**: BREP and comparable engineering applications require a full interactive UI, while different workflows need either in-context viewing or the space and tooling of a browser.

**Independent Test**: Start a reference managed application, open it in the panel, perform an interaction, open the same instance in the system browser, and verify that both presentations remain authorized and reflect the same application state.

**Acceptance Scenarios**:

1. **Given** a healthy application surface, **When** the engineer chooses **Open in workspace**, **Then** the UI opens in a Wright tab with a clear title, status, and close control.
2. **Given** the same application surface, **When** the engineer chooses **Open in browser**, **Then** Wright opens the system browser at an authorized URL for that instance.
3. **Given** a surface already open in one presentation, **When** the engineer chooses the other presentation, **Then** Wright reuses the application instance unless the surface explicitly requires an isolated instance.
4. **Given** an application that is starting, unhealthy, stopped, or unavailable, **When** the engineer attempts to open it, **Then** Wright shows the current state and offers only valid recovery actions.
5. **Given** a workspace is reloaded, **When** Wright restores an open application tab, **Then** it reconnects to a valid instance or presents a deliberate restart action rather than a blank or misleading frame.

---

### User Story 3 - Use a Surface Without Crossing Security Boundaries (Priority: P1)

An engineer can interact with first-party, MCP-provided, and workspace-authored UIs without granting them implicit access to Wright credentials, another workspace, local files, tools, devices, or unrestricted network destinations. When a surface requests a sensitive capability, Wright explains the request and applies the engineer's scoped decision.

**Why this priority**: Hosted pages can execute active content and call tools. Safe isolation and explicit authority are release-blocking, not follow-up enhancements.

**Independent Test**: Open a deliberately hostile reference surface and verify that attempts to read Wright credentials, access another workspace, traverse files, navigate to a prohibited origin, call an unauthorized tool, or retain a revoked grant all fail and create redacted audit evidence.

**Acceptance Scenarios**:

1. **Given** an untrusted surface, **When** it attempts to access Wright application state, credentials, or another surface directly, **Then** the attempt is blocked by isolation boundaries.
2. **Given** a surface requests a protected capability, **When** no matching grant exists, **Then** Wright asks for narrowly scoped consent or denies the request according to policy.
3. **Given** a capability was granted only for the current surface instance, **When** that instance closes or the grant is revoked, **Then** later requests fail without affecting unrelated surfaces.
4. **Given** a surface follows redirects or opens a new destination, **When** the resolved destination violates workspace or network policy, **Then** Wright blocks it before protected data is sent.
5. **Given** a rejected request or runtime failure, **When** diagnostics are recorded, **Then** secrets, tokens, sensitive query values, and protected content are redacted.

---

### User Story 4 - Focus on the UI While Continuing the Conversation (Priority: P1)

An engineer expands the active surface to use all workspace space except the chat area, continues giving instructions, and watches the UI update. The engineer can resize chat, leave focus mode, switch tabs, and use keyboard navigation without losing application state.

**Why this priority**: The product value comes from the feedback loop between conversation and visible engineering work; hiding either side breaks that loop.

**Independent Test**: Open a graph or managed app, enter surface focus mode, send a chat instruction that updates the UI, resize the chat area, switch away and back, and exit focus mode while verifying continuity and keyboard accessibility.

**Acceptance Scenarios**:

1. **Given** an active surface, **When** the engineer enters surface focus mode, **Then** the surface uses the available non-chat area and chat remains visible and operable.
2. **Given** focus mode is active, **When** the engineer sends a request that changes the artifact or app, **Then** the surface can show the update without leaving focus mode.
3. **Given** the available window becomes too narrow for both areas, **When** responsive layout activates, **Then** Wright preserves access to chat and the surface through an explicit, reversible layout rather than clipping essential controls.
4. **Given** a keyboard-only user, **When** focus moves between chat, surface controls, and embedded content, **Then** the focus order is visible, reversible, and does not trap the user inside the surface.

---

### User Story 5 - Run and Recover Managed Web Applications (Priority: P2)

An engineer or integration starts a workspace-declared web application without manually choosing ports or managing processes. Wright reports startup and health, carries ordinary page loads and live connections, and stops the complete application process tree when its ownership ends.

**Why this priority**: Interactive Python tools, BREP, and local web applications need dependable lifecycle and transport behavior before they can feel native to the workspace.

**Independent Test**: Launch reference applications exercising ordinary requests, nested assets, redirects, streaming events, and bidirectional live connections; then restart and stop each app and verify bounded recovery with no leaked process or port.

**Acceptance Scenarios**:

1. **Given** an approved application definition with no fixed port, **When** it starts, **Then** Wright assigns an available endpoint, waits for declared readiness, and opens it only after it is ready.
2. **Given** an app uses nested routes, query strings, redirects, streamed events, or bidirectional live connections, **When** it is used through Wright, **Then** those interactions preserve their intended semantics within policy.
3. **Given** an app fails before readiness or becomes unhealthy, **When** Wright detects the failure, **Then** the surface shows a redacted cause and offers retry, restart, logs, or close as applicable.
4. **Given** two applications or two isolated instances of one application, **When** they run concurrently, **Then** their identity, authorization, routes, logs, and lifecycle controls do not collide.
5. **Given** Wright owns an application and its workspace closes or Wright shuts down, **When** the cleanup bound expires, **Then** the entire owned process tree is stopped or the remaining failure is reported for recovery.

---

### User Story 6 - Use MCP-Provided and Web-Integrated UIs (Priority: P2)

An MCP server can advertise a UI associated with a tool or resource, and Wright can render that UI as a workspace surface. The UI receives only the host context and scoped operations it is entitled to use. Web-integrated applications can request supported Wright actions through a panel-scoped compatibility layer even when a particular browser integration standard is unavailable.

**Why this priority**: MCP applications and WebMCP are primary integration paths for BREP and future engineering tools, and must use the same security and presentation model as other surfaces.

**Independent Test**: Connect a reference MCP server that exposes a UI resource and a reference web-integrated app, render each in a panel, exchange authorized host messages, deny an unauthorized action, and verify a useful fallback in a browser without native WebMCP support.

**Acceptance Scenarios**:

1. **Given** an MCP result or tool declares an associated UI, **When** the result is shown, **Then** Wright preserves the declaration, resolves the UI resource, and offers the valid presentation choices.
2. **Given** an MCP-provided UI is active, **When** it requests an authorized tool call, resource, host-context update, or user message, **Then** Wright routes the operation through the bound workspace and surface identity.
3. **Given** an MCP-provided UI requests an operation outside its declared or granted capabilities, **When** Wright evaluates it, **Then** the operation is denied with a stable error and audit decision.
4. **Given** native web-agent integration is absent or differs by browser, **When** a supported web-integrated app loads in Wright, **Then** a feature-detected compatibility path provides the documented subset without exposing global cross-panel channels.
5. **Given** an integration uses an unsupported protocol feature, **When** negotiation occurs, **Then** Wright reports the unsupported capability without silently broadening authority or breaking unrelated UI behavior.

---

### User Story 7 - Build and Diagnose a Surface Integration (Priority: P3)

An application or MCP developer uses a stable, documented surface contract, reference applications, and diagnostics to add an integration. They can inspect lifecycle state, presentation details, health, scoped messages, permission decisions, and redacted logs without depending on private Wright internals.

**Why this priority**: A professional extension point needs a supportable contract and fast diagnosis so each new app does not become a one-off UI patch.

**Independent Test**: Implement the documented minimal application from the developer quickstart, run its contract suite, deliberately fail readiness and request a denied capability, and use the diagnostics view to identify both outcomes.

**Acceptance Scenarios**:

1. **Given** the minimal developer example, **When** a developer follows the documented steps, **Then** the app can be launched, shown in either presentation, and stopped without private APIs.
2. **Given** a surface is selected, **When** diagnostics are opened, **Then** the developer can see its non-secret identity, source, lifecycle state, presentation, health history, capabilities, recent errors, and correlation identifiers.
3. **Given** a public surface contract changes incompatibly, **When** an older integration connects, **Then** Wright either negotiates a supported version or returns an actionable compatibility error.

### Edge Cases

- The preferred port is already in use, becomes occupied during startup, or is reported incorrectly by the child application.
- An application exits before readiness, hangs during shutdown, forks descendants, restarts itself, or leaves an orphan after Wright crashes.
- The UI loads its root page but a nested asset, deep link, redirect, event stream, or bidirectional connection uses an incorrect base path or origin.
- A surface repeatedly redirects, changes from a permitted name to a prohibited address, uses an unsupported URL scheme, or tries to escape through a newly opened window.
- A third-party page refuses embedding, requires browser features unavailable in a sandbox, or depends on cross-site cookies.
- The same app is opened more than once, requested simultaneously by chat and the user, or declared single-instance while an instance is already starting.
- A tab closes while a request is in flight, the active chat session changes, the user changes workspaces, the page reloads, the machine sleeps, or the network connection drops.
- A surface sends malformed, oversized, excessively frequent, duplicated, late, or out-of-order messages.
- A graph contains no data, non-finite values, unsupported objects, extremely large data, rapid updates, or inaccessible labels and colors.
- A Python process exits immediately, cannot import the display helper, lacks an optional plotting package, or runs outside the active workspace.
- A surface requests clipboard, file, download, camera, microphone, location, notification, pop-up, external navigation, or tool access that it did not declare.
- A local URL attempts path traversal, symbolic-link escape, header spoofing, DNS rebinding, cross-workspace token reuse, or access to Wright's own privileged service endpoints.
- A runtime is inside a container or remote environment where its listen address is not directly reachable from the user's browser.
- The operating system refuses or cannot resolve the default browser action.
- Native WebMCP support is absent, experimental, incompatible, or disabled.
- Wright is offline and a surface depends on an undeclared remote asset.

## Requirements *(mandatory)*

### Functional Requirements

#### Surface Model and Presentation

- **FR-001**: Wright MUST represent static display results, workspace files, managed web applications, and MCP-provided UIs through one workspace-surface model with stable identity, source, title, lifecycle state, capabilities, presentation options, and owning workspace.
- **FR-002**: Every surface instance MUST be bound to exactly one workspace and MUST NOT be addressable with authority from another workspace or unaffiliated chat session.
- **FR-003**: A surface MUST expose explicit `declared`, `starting`, `ready`, `unhealthy`, `stopping`, `stopped`, and `failed` states where those states apply; the UI MUST NOT present a non-ready surface as healthy.
- **FR-004**: Wright MUST support opening an eligible declared surface in a workspace panel, the system browser, or both, subject to source policy and capability support. An undeclared URL MAY be opened after explicit per-instance user approval only as a direct-navigation, view-only presentation, subject to browser embedding controls.
- **FR-005**: The panel and browser presentations of the same shareable surface MUST refer to the same authorized application instance; a surface that cannot safely share MUST declare isolated-instance behavior.
- **FR-006**: Users MUST be able to open the alternate presentation or return focus to an existing presentation without an unnecessary application restart.
- **FR-007**: Closing a presentation or surface tab, detaching to a browser, stopping an underlying runtime, and deleting a durable output MUST be distinct commands with the consequence and recovery/retention disclosure defined in `ux-contract.md`; no close/detach action may imply stop/delete, and no destructive delete may imply recovery when none exists.
- **FR-008**: Wright MUST store the preferred presentation as non-secret state keyed by user, workspace, and surface source. On every open or restore, Wright MUST revalidate workspace authority, source availability, runtime identity, and presentation eligibility, and MUST use an available safe fallback with an explanation when the preference is no longer valid.
- **FR-009**: Existing file viewers and editor tabs MUST continue to resolve and operate through the established viewer behavior unless they opt into additional surface capabilities.

#### Beginner Python and Display Results

- **FR-010**: Wright MUST provide a supported Python display interface that can produce a labeled line, bar, scatter, or histogram graph from ordinary sequences and common tabular data without requiring browser-language code.
- **FR-011**: The beginner graph path MUST require no user-authored web server, port selection, HTML document, or client-side event loop.
- **FR-012**: The display interface MUST support durable non-interactive results, typed interactive results rendered by approved host renderers, and optional interactive applications that use the managed application lifecycle.
- **FR-013**: The display interface MUST carry a media type, metadata, dimensions, accessibility description, logical output identity, and revision so Wright can choose a renderer and update predictably.
- **FR-014**: Wright MUST support at least text, table, raster image, vector image, typed Plotly-compatible interactive data, and safe web-document display results in addition to the required graph helpers. Raw Python-supplied HTML MUST be sanitized by default; active HTML or JavaScript MUST require explicit opt-in and run in an isolated surface with no privileged Wright bridge.
- **FR-015**: Repeated display of the same logical output MUST follow the deterministic `display_id`, revision, idempotency, stale-update, history, and new-output rules in `ux-contract.md`; it MUST update atomically and MUST NOT leave a partially rendered or ambiguously replaced result.
- **FR-016**: Unsupported, empty, non-finite, mismatched, or oversized data, optional dependency failures, serialization limits, and rendering failures MUST follow the bounded input/error behavior in `ux-contract.md` and produce actionable example-linked messages in both the Python process and the associated Wright task or surface.
- **FR-017**: Wright MUST ship runnable beginner examples for static graphs and a documented progression to interactive applications, with expected results that work offline after normal installation.

#### Managed Application Lifecycle and Transport

- **FR-018**: A managed application definition MUST declare its identity, executable and arguments, working directory, environment references, readiness check, startup bound, ownership policy, presentation support, and requested capabilities; it MAY also declare health behavior and a bounded lifetime policy.
- **FR-019**: Wright MUST start managed applications without interpreting user-controlled shell expressions and MUST resolve executable, arguments, working directory, and environment within workspace policy.
- **FR-020**: Wright MUST allocate or validate endpoints using the race-safe reservation, bounded retry, listener/process ownership proof, concurrent-instance isolation, and failure semantics in `policy-defaults.md`; users MUST NOT resolve ordinary port collisions, and Wright MUST never probe, expose, stop, or proxy a different process that acquired an expected endpoint.
- **FR-021**: Surface routing MUST preserve permitted request methods, paths, queries, headers, bodies, cookies, redirects, streaming events, and bidirectional live connections needed by the declared app.
- **FR-022**: Wright MUST wait for declared readiness before presenting a surface as ready, monitor declared health without starting unrelated services, and distinguish transport failure from application failure.
- **FR-023**: Users and authorized integrations MUST be able to start, retry, restart, stop, and inspect a managed app according to its lifecycle state and ownership policy. An explicit app lifetime policy, including a bounded lease or idle timeout when declared, MUST take precedence; when it is omitted, a Wright-owned app MUST remain available until its owning workspace closes. Idle lifetime MUST be based on defined application/presentation activity and MUST NOT be extended by unrelated workspace traffic.
- **FR-024**: Wright MUST stop and reconcile the complete owned process tree and its listeners/authority within the signal, escalation, total cleanup, platform-adapter, and unresolved-leak semantics in `policy-defaults.md` when its declared lifetime ends, its owning workspace closes, Wright shuts down, or an authorized user stops it. Unknown ownership MUST NOT be killed or adopted, and incomplete cleanup MUST be reported as failure rather than success.
- **FR-025**: Managed runtimes and transports MUST apply every applicable resource, process, restart, log, connection, header/body/frame, message/rate, first-byte/idle/total-time, and buffering bound from an approved declaration or the versioned defaults in `policy-defaults.md`; omission MUST NOT mean unlimited, effective enforcement/degradation MUST be observable, and exceeding a bound MUST fail predictably.
- **FR-026**: Concurrent runtimes MUST have isolated identity, authorization, endpoints, routing, logs, health, and lifecycle operations.
- **FR-027**: The runtime-to-presentation contract MUST work for supported native, containerized, and remote workspace deployments without assuming that an application listen address is directly reachable from the user's browser.

#### MCP and Web Integration

- **FR-028**: Wright's MCP path MUST preserve server-declared UI associations and metadata across discovery, tool execution, result handling, and surface creation.
- **FR-029**: Wright MUST resolve authorized MCP UI resources through the bound MCP session and workspace, including resource content, metadata, version, and failure state.
- **FR-030**: An MCP-provided UI MUST receive only the documented host context and message operations for which it is compatible and authorized.
- **FR-031**: Tool calls, resource reads, host-context changes, user-message requests, and other privileged actions originating from a surface MUST pass through the same workspace authorization, validation, approval, cancellation, and audit policies as equivalent non-UI operations.
- **FR-032**: Web-integrated surfaces MUST use feature detection and a versioned compatibility contract for supported WebMCP-style operations; lack of native browser support MUST NOT create a global or cross-panel communication channel.
- **FR-033**: Messages from a web-integrated surface MUST be scoped to its surface instance, source origin, workspace, protocol version, and correlation identity, and late messages from a disposed instance MUST be ignored.
- **FR-034**: Unsupported or malformed protocol operations MUST return stable, actionable errors without granting fallback authority or destabilizing the host page.

#### Security and Policy

- **FR-035**: Untrusted active content MUST run in an isolated browsing context that cannot directly access Wright application memory, credential storage, privileged cookies, another surface, or the host document.
- **FR-036**: Each active runtime or equivalently isolated trust boundary MUST have a distinct effective origin so one app cannot impersonate or read another app through shared browser authority.
- **FR-037**: Embedded surfaces MUST start with a least-privilege sandbox and content policy; scripts, forms, downloads, pop-ups, navigation, device access, and same-origin privileges MUST be enabled only when policy permits them.
- **FR-038**: Protected capabilities MUST be declared, risk-tiered, evaluated by server-side policy, and represented by a grant with an expiry. Consent MUST disclose the source/version, operation and bounded data, risk, reason, effective policy, duration/persistence, denial consequence, and distinct allow/deny/cancel choices defined in `ux-contract.md`. Low-risk declared capabilities MAY be remembered only for the exact user, workspace, surface source, and source version; high-risk, sensitive, or mutating capabilities MUST default to one operation or one surface instance. Standard engineers MAY create displays, present surfaces, run administrator-approved workspace manifests, and grant their own policy-eligible capabilities; only administrators MAY approve attached targets, change source/deployment policy, or broaden organization-level eligibility. User revocation and stricter administrator policy MUST override remembered grants.
- **FR-039**: Surface endpoints and credentials MUST be unguessable, time-bounded, revocable, excluded from logs and user-visible error details, and prevented from leaking through referrers or unapproved redirects.
- **FR-040**: URL and redirect validation MUST reject unsupported schemes, prohibited origins, ambiguous host representations, DNS rebinding, credential-bearing URLs, and access to privileged local services outside the declared runtime.
- **FR-041**: File and workspace resource access from surfaces MUST use canonical workspace-scoped identifiers and MUST reject traversal, symbolic-link escape, and cross-workspace references.
- **FR-042**: Opening a system browser for a declared surface MUST use a freshly authorized presentation URL for the resolved surface; remote or changed-trust destinations MUST require policy approval and clear user disclosure. An approved undeclared URL MUST be loaded directly, MUST NOT pass through Wright's application proxy, and MUST receive no Wright credentials, tool bridge, managed lifecycle authority, or privileged host context.
- **FR-043**: Wright MUST apply size, rate, concurrency, timeout, and recursion limits to surface messages and proxied requests before they can exhaust the host or another workspace.
- **FR-044**: Security and lifecycle decisions MUST produce structured, correlated, redacted audit records without capturing secrets, protected content, or full sensitive URLs.
- **FR-045**: Revocation, logout, workspace closure, surface disposal, and runtime replacement MUST invalidate applicable grants and presentation credentials within a bounded period.

#### Workspace Experience, Accessibility, and Operations

- **FR-046**: Wright MUST provide the versioned normal/focus/narrow layouts in `ux-contract.md`: focus assigns the available non-chat workspace area to the active surface while keeping chat visible and fully operable, and an explicit reversible switcher preserves both destinations when their minimum sizes cannot fit.
- **FR-047**: Users MUST be able to resize the chat/surface boundary, restore the normal layout, switch surfaces, and use all host controls with keyboard and assistive technology according to the container-relative sizing, retention, semantic tabs/separator, focus restoration/escape, zoom, accessible-name, stable-test-ID, and manual/automated acceptance rules in `ux-contract.md`.
- **FR-048**: Surface controls and status MUST identify the app or output, owning workspace, presentation, trust state, health, and meaningful recovery actions without exposing internal identifiers as the only explanation.
- **FR-049**: Surface diagnostics MUST show redacted source, version, state transitions, readiness and health history, presentation state, capabilities, permission decisions, recent errors, and trace correlation identifiers. For every generated display artifact, its authorized verification view MUST also expose the exact originating prompt (or an explicit direct-execution/no-prompt marker), effective constraints, and exact Python script or script revision used to produce it; this provenance MUST be access-controlled and MUST NOT be copied into general logs.
- **FR-050**: Surface lifecycle, routing, security, and display operations MUST emit structured telemetry correlated across the UI, Wright service boundary, managed runtime, MCP operation, and every associated SQLite or file-vault read/write where applicable.
- **FR-051**: The implementation MUST remain offline-first: core panel hosting, browser presentation, Python graphs, lifecycle management, and reference examples MUST NOT require a hosted Wright service or undeclared internet access.
- **FR-052**: Supported behavior MUST be equivalent on Linux, macOS, and Windows except for explicitly documented operating-system limitations, which MUST have deterministic detection and user guidance.
- **FR-053**: Public surface and display contracts MUST be versioned, documented, covered by conformance fixtures, and changed incompatibly only with an explicit migration or compatibility path.
- **FR-054**: The UI MUST expose stable automation identifiers for primary actions and states, including open-in-panel, open-in-browser, focus, restore, start, restart, stop, permission decisions, status, and diagnostics.
- **FR-055**: Wright MUST provide reference fixtures for a static Python graph, an updating graph, a managed Python app, an MCP-provided UI, a WebMCP-style integration, and a hostile surface used to verify isolation.
- **FR-056**: User, developer, security, troubleshooting, and example documentation MUST be versioned with the feature and MUST distinguish supported contracts from experimental compatibility behavior.

### Key Entities *(include if feature involves data)*

- **Workspace Surface**: The durable, workspace-owned description of something Wright can present. It has stable identity, source kind, display metadata, trust classification, supported presentations, capabilities, persistence behavior, and contract version.
- **Surface Instance**: One active realization of a workspace surface. It has an instance identity, owner, state generation, presentation credentials, grants, health, diagnostics, and optional managed runtime.
- **Surface Source**: The origin of display content or application behavior, such as a display result, workspace resource, managed app definition, or MCP UI resource, including provenance and version.
- **Managed Runtime**: An owned or externally managed application process and endpoint with launch definition, readiness, health, resource bounds, lifecycle generation, optional declared lifetime policy, workspace-lifetime fallback, and cleanup status.
- **Presentation**: A panel or system-browser view bound to a surface instance through an authorized, revocable endpoint.
- **Presentation Preference**: A non-secret user choice keyed by user, workspace, and surface source that selects panel or browser when permitted and never overrides current security or compatibility policy.
- **Display Result**: A typed, optionally revisioned output from Python or another producer with content, metadata, accessibility description, size, logical identity, and durability policy.
- **Capability Grant**: A revocable policy decision that permits a specific surface source or instance to perform a bounded action in a workspace for a bounded duration, including risk tier, user, source version, operation, persistence scope, expiry, and decision provenance.
- **Surface Message**: A versioned, validated, correlated operation exchanged between a surface and Wright, including origin, instance, workspace, operation, payload limits, and terminal outcome.
- **Surface Diagnostic Event**: A structured and redacted lifecycle, health, routing, display, policy, or protocol event linked by correlation identity.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: At least four of five engineers who self-identify as having little programming experience can use the beginner guide to create and revise a labeled graph in under 10 minutes without undocumented assistance.
- **SC-002**: The shipped beginner static-graph example uses no more than one import and ten executable lines, requires no user-managed server or port, and remains viewable after the Python process exits.
- **SC-003**: Under the recorded reference profile and exact timing marks in `policy-defaults.md`, a static display result becomes visible within 2 seconds of accepted producer ingestion, and a healthy managed reference app becomes interactive within 5 seconds after its own readiness condition succeeds, in at least 95 of 100 measured trials following one unmeasured warm-up.
- **SC-004**: Every shipped reference surface can be opened in each presentation it declares, and switching presentation reuses or isolates instances exactly as declared in 100 repeated trials.
- **SC-005**: Chat remains operable throughout surface focus mode, and all focus, resize, presentation, lifecycle, permission, diagnostics, and recovery journeys meet the keyboard, focus, zoom, high-contrast, accessible-name, manual screen-reader spot-check, and automated accessibility criteria in `ux-contract.md` with zero critical or serious violations.
- **SC-006**: Using the concurrency protocol in `policy-defaults.md`, the managed-app conformance suite preserves ordinary requests, nested assets, queries, redirects, streaming events, and bidirectional live messages with zero cross-instance routing errors across 100 simultaneously scheduled reference interactions.
- **SC-007**: For every supported process adapter, one hundred repeated start, restart, stop, workspace-close, and application-shutdown cycles leave zero owned child processes, occupied endpoints, active target pins, presentation credentials, instance-scoped grants, pending streams/messages, or surface registrations after the applicable cleanup bound in `policy-defaults.md`.
- **SC-008**: The hostile-surface suite records zero successful cross-workspace, cross-surface, credential, path-escape, prohibited-origin, unauthorized-tool, stale-grant, or privileged-local-service accesses on every supported deployment mode.
- **SC-009**: The MCP UI conformance fixtures preserve all declared UI associations and complete authorized context, resource, message, and tool interactions while denying every undeclared operation with a stable audited result.
- **SC-010**: Linux, macOS, and Windows tests pass the static graph, managed app, panel, browser, lifecycle, reconnect, and cleanup journeys with no undocumented platform-specific steps.
- **SC-011**: Existing viewer and editor contract tests pass unchanged, and all previously supported file-viewing journeys remain available after surface support is enabled.
- **SC-012**: A developer unfamiliar with Wright internals can follow the integration quickstart, launch the minimal reference app in both presentations, diagnose one readiness failure, and identify one denied capability in under 30 minutes.
- **SC-013**: Every release-blocking functional requirement maps to at least one automated or explicitly identified environment-dependent test and to completion evidence in the final audit.

## Assumptions

- "Open in browser" means the user's system-default browser, while "open in workspace" means a sandboxed tab in Wright's existing central viewer area.
- Wright's existing local authentication, role policy, workspace identity, viewer registry, and MCP gateway remain authoritative and are extended rather than bypassed.
- Core use is local and offline-first. A managed app may declare remote dependencies, but Wright does not silently grant or fetch them.
- Applications provide web-compatible content and a valid launch or discovery definition; Wright does not reimplement BREP or other application-specific UIs.
- Declared managed apps and MCP Apps, including BREP-style applications, may run full JavaScript and declared live transports within their isolated origin and approved capabilities; Python display sanitization does not restrict those app sources.
- A user-approved undeclared URL is view-only and direct-navigation; it is not promoted to a managed application and receives no privileged Wright integration.
- Normal installation includes the supported Python display helper and its beginner graph path. Optional third-party plotting packages may add adapters but are not required for the beginner example.
- Dependency installation and arbitrary package execution are explicit development actions, not an implicit side effect of viewing a surface.
- Browser-native WebMCP behavior is treated as a feature-detected integration; Wright's stable security and message contract does not depend on an experimental browser API being present.
- Persisted tabs remember intent and safe metadata, not reusable secrets or an assumption that a previous process is still alive.
- Resource and timing targets are measured on a documented reference environment and exclude an application's own work before it reports readiness.

## Dependencies

- The existing workspace/session identity and local authorization model.
- The existing viewer registry, tabs, panel host, and workspace layout.
- The existing workspace service boundary for workspace-scoped execution and file access.
- The MCP gateway's session, tool, resource, policy, and audit behavior.
- Supported operating-system facilities for starting a process and opening a default browser.

## Out of Scope

- Providing general-purpose browsing features such as unrestricted link traversal, history, saved credentials, extensions, or public internet hosting; the explicitly approved view-only URL presentation is the bounded exception.
- Publishing workspace applications directly to the public internet.
- Replacing application-specific UIs such as BREP, or defining their domain operations.
- Implicit installation of arbitrary Python, JavaScript, or system dependencies requested by a surface.
- Multi-user collaborative surface sessions or remote desktop streaming.
- Making an experimental browser standard the sole path for web-agent integration.
- A low-level, chatty per-pixel Python canvas protocol as the beginner API; specialized renderers may be added later through the versioned surface contract.
