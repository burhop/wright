# Feature Specification: Capability Library and MCP Onboarding

**Feature Branch**: `068-capability-library`

**Created**: 2026-08-12

**Status**: Draft

**Input**: User description: "Create an engineering Capability Library that preserves Wright's existing catalog and install state while adding evidence-backed catalog updates, current-machine compatibility, guided MCP configuration import and install preflight, structured missing-server reporting, validation, and workspace enablement. Use the official Onshape Labs FeatureScript MCP as the data-only acceptance case, keep a complete offline bundled snapshot, preserve local custom entries and user disablement, and do not install or enable anything merely because catalog metadata changed."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Find a Compatible Engineering Capability (Priority: P1)

An engineer searches the global Capability Library by engineering domain, application, task, platform, maturity, locality, risk, host requirement, or installed state. Every result explains whether it can work on the current machine and distinguishes authoritative evidence from unverified or unavailable claims.

**Why this priority**: Engineers must be able to make a trustworthy selection before Wright asks them to install software, provide credentials, or change a workspace.

**Independent Test**: Starting from the bundled offline catalog, an engineer can find a suitable CAD capability, inspect its evidence and compatibility reasons, and identify a usable alternative without network access.

**Acceptance Scenarios**:

1. **Given** Wright is offline with no prior catalog update, **When** an engineer opens the Capability Library and filters for a domain, **Then** the complete bundled catalog remains searchable and each result shows evidence, compatibility, requirements, and installed state.
2. **Given** a capability is incompatible, uncertain, blocked, failed, or not yet a public MCP, **When** the engineer opens its details, **Then** Wright keeps it visible, states the exact reason, and offers actionable recovery or a clearly labeled alternative without presenting it as installable.
3. **Given** two entries share an alias or source identity, **When** the library is loaded, **Then** Wright presents one unambiguous canonical identity and preserves provenance for the source records.

---

### User Story 2 - Preview and Apply a Trusted Catalog Update (Priority: P1)

An administrator checks for a catalog update, sees who supplied it and exactly what it changes, and deliberately activates or rolls back that data without installing, enabling, deleting, or reconfiguring any capability.

**Why this priority**: New official servers must reach users without a Wright code release, but a catalog refresh is a supply-chain event and cannot silently change executable state.

**Independent Test**: A deterministic approved update adds the distinct official-preview Onshape Labs FeatureScript MCP entry, survives restart, and can be rolled back while existing custom entries, installed state, workspace enablement, aliases, and user disablement remain unchanged.

**Acceptance Scenarios**:

1. **Given** a valid newer catalog snapshot from an approved channel, **When** an administrator previews and activates it, **Then** Wright verifies authenticity, integrity, freshness, schema, identity rules, and provenance before atomically making it active.
2. **Given** an update is unsigned, altered, expired, older than the active snapshot, schema-invalid, identity-ambiguous, or from an unapproved source, **When** Wright evaluates it, **Then** activation fails closed and the prior catalog remains active and usable.
3. **Given** a valid update has been activated, **When** an administrator rolls back, **Then** the prior snapshot is restored atomically and user-owned state remains unchanged.
4. **Given** the Onshape Labs FeatureScript MCP has vendor-authoritative release evidence, **When** the approved data update is activated, **Then** it appears as an official preview remote capability with its source, account/subscription prerequisite, and not-locally-validated limitation, without Wright subscribing, accepting a license, or contacting the endpoint.

---

### User Story 3 - Add an MCP Through a Guided Flow (Priority: P1)

An engineer adds an MCP from the Wright catalog, a pasted standard client configuration, a remote endpoint, or a local command. Wright converts the choice into an exact preflight plan before anything is installed or connected.

**Why this priority**: A unified, understandable flow removes configuration guesswork while keeping executable and credential changes deliberate.

**Independent Test**: Deterministic fixtures complete the guided preflight path for one local package, one remote endpoint, and one host-application bridge, including blocked and failed paths, without paid credentials or proprietary applications.

**Acceptance Scenarios**:

1. **Given** a supported catalog entry, **When** an engineer starts onboarding, **Then** Wright shows the exact source, pinned version or revision, transport, commands or endpoint, dependencies, storage and network effects, host requirements, credentials, approvals, validation steps, rollback, and unresolved risks before execution.
2. **Given** a common MCP client configuration, **When** an engineer pastes it, **Then** Wright identifies the supported format, previews every server, maps secret-bearing values to credential references, and reports precise field-level errors without persisting secret values in catalog or workflow data.
3. **Given** an unsupported, ambiguous, or partially valid configuration, **When** it is parsed, **Then** no server is installed or registered and the engineer receives a stable explanation for each rejected or ignored field.
4. **Given** a host bridge, **When** an engineer requests preflight, **Then** Wright checks application presence, supported version, add-on state, local handshake availability, and read-only probe support, but does not install the proprietary host application.

---

### User Story 4 - Validate and Enable for a Workspace (Priority: P2)

After approving an install or connection plan, an engineer validates the MCP and explicitly enables it for one workspace. Installation, validation, workspace enablement, and later invocation approval remain distinct decisions.

**Why this priority**: Discovery is only useful when a capability can be safely made available where engineering work occurs without granting broader authority.

**Independent Test**: A deterministic MCP initializes, reports its tools, passes a read-only probe, and is enabled for one workspace while remaining unavailable to another workspace and unapproved for destructive invocation.

**Acceptance Scenarios**:

1. **Given** an approved preflight, **When** the engineer proceeds, **Then** Wright executes only the displayed plan, records lifecycle evidence, and stops with actionable recovery if any step differs or fails.
2. **Given** credentials are required, **When** the engineer supplies them, **Then** they cross the existing secret boundary and only opaque references appear in capability, catalog, workspace, log, and workflow records.
3. **Given** initialization, discovery, and any advertised read-only health probe pass, **When** the engineer enables the capability, **Then** only the chosen workspace receives availability and invocation still requires the applicable run-time approvals.
4. **Given** validation is stale or failed, **When** an engineer attempts enablement, **Then** Wright blocks enablement or clearly limits it according to policy and explains the recovery action.

---

### User Story 5 - Report a Missing Capability (Priority: P2)

An engineer who cannot find a needed server submits a structured report from within Wright rather than responding to browser prompts or losing their search context.

**Why this priority**: Structured reports turn gaps into reviewable catalog candidates without falsely representing them as available software.

**Independent Test**: An engineer submits a source URL, vendor, engineering domain, expected task, platform need, and optional notes; the report is stored separately from trusted catalog entries and can be exported for review.

**Acceptance Scenarios**:

1. **Given** a search has no usable result, **When** the engineer chooses Report missing capability, **Then** a structured in-app form preserves the search context and validates the report before submission.
2. **Given** a report exists, **When** the library is refreshed, **Then** the report remains user-owned and is not promoted to trusted or installable status without review evidence.

---

### User Story 6 - Preserve Existing User State (Priority: P1)

An existing Wright user upgrades to the Capability Library without losing custom MCPs, installation records, credentials, workspace choices, aliases, or explicit disablement.

**Why this priority**: Catalog improvements cannot be allowed to surprise existing users or activate software they previously disabled.

**Independent Test**: A legacy catalog and user-state fixture migrates forward, activates and rolls back a catalog update, restarts, and produces the same user-owned state with no automatic installation or enablement.

**Acceptance Scenarios**:

1. **Given** existing catalog-derived and custom MCP records, **When** the feature first starts, **Then** migration is reversible, idempotent, and preserves user-owned values and explicit choices.
2. **Given** updated metadata for an installed or disabled entry, **When** a catalog update is activated, **Then** metadata changes are visible but process state, credentials, installation state, and enablement do not change.

### Edge Cases

- The update download is interrupted, duplicated, or replaced between preview and activation.
- The update is correctly signed but expires, targets a future schema, reuses an existing alias, or omits a previously active entry.
- The active or previous snapshot is corrupted on disk, storage is read-only, or the process stops during activation.
- A pasted document contains several supported wrappers, duplicate names, unknown fields, shell metacharacters, inline tokens, environment placeholders, or mixed valid and invalid servers.
- A local command exists but resolves to a different executable, version, platform, or architecture than the catalog plan describes.
- A remote endpoint redirects, requires authentication, is unreachable, or exposes a changed tool schema.
- A host application is installed in multiple versions, is running in an unsupported state, or has no safe read-only probe.
- Validation succeeds and then becomes stale before workspace enablement.
- A catalog entry disappears while a custom, installed, disabled, or workspace-enabled record still refers to it.
- The engineer has insufficient role permissions to update the global catalog, install software, manage credentials, or enable workspace capabilities.
- Concurrent administrators attempt catalog activation or rollback while an engineer is viewing an older preview.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Wright MUST provide a global Capability Library distinct from workspace enablement and workflow execution.
- **FR-002**: The library MUST search names, vendors, aliases, capabilities, engineering domains, applications, tasks, requirements, and authoritative source records.
- **FR-003**: The library MUST filter by domain, lifecycle stage, current platform and architecture, maturity, evidence class, risk, locality, host-software need, validation state, and installed state.
- **FR-004**: Every capability MUST expose a stable canonical identity, aliases, source and field provenance, license facts or unknown status, data touched, credentials, approvals, dependencies, supported platforms, validation history, examples, and alternatives where available.
- **FR-005**: Wright MUST preserve distinct evidence classes for official production, official preview, verified community, community candidate, user-reported/source-needed, API-or-wrapper candidate without a public MCP, documentation-only MCP, blocked validation, and excluded or stale entries.
- **FR-006**: Wright MUST require vendor-authoritative evidence before labeling a capability official and MUST NOT infer official status from popularity, naming, or branding.
- **FR-007**: Wright MUST ship a complete schema-valid bundled catalog that remains usable when no network or update history is available.
- **FR-008**: Optional catalog updates MUST identify an approved channel, snapshot version, issue and expiry times, schema version, content digest, signer, signature, and provenance.
- **FR-009**: Wright MUST verify update authenticity, integrity, expiry, monotonic version, schema, identities, aliases, and evidence rules before preview or activation.
- **FR-010**: Wright MUST reject replay, rollback, freeze, tampering, unapproved signer, ambiguous identity, and partial-download conditions without replacing the active snapshot.
- **FR-011**: Update activation and rollback MUST be atomic, retain a known-good prior snapshot, survive interruption, and recover deterministically after restart.
- **FR-012**: Catalog preview MUST show added, removed, changed, and unchanged identities and field-level provenance before administrator activation.
- **FR-013**: Catalog refresh, activation, and rollback MUST NOT install, start, stop, connect, enable, disable, delete, or alter credentials for a capability.
- **FR-014**: Catalog reconciliation MUST preserve custom entries, installed state, explicit user disablement, workspace enablement, credential references, and unresolved legacy identities.
- **FR-015**: The Onshape Labs FeatureScript MCP MUST be accepted through a signed data-only update as a distinct official-preview remote capability using vendor-authoritative release evidence and an explicit unvalidated/subscription-required limitation.
- **FR-016**: Wright MUST provide guided onboarding choices for a catalog entry, pasted common-client configuration, remote endpoint, local command or development server, and missing-capability report.
- **FR-017**: Configuration import MUST support documented common forms used by major MCP clients, identify the detected form, preserve multiple server definitions, and produce stable field-level errors for unsupported or ambiguous input.
- **FR-018**: Import MUST treat inline secret-like values as sensitive input, convert supported values to credential requirements, redact diagnostics, and prevent raw secrets from entering catalog, workspace, workflow, history, or log records.
- **FR-019**: Import MUST never execute commands, expand shell expressions, contact endpoints, or register servers during parsing or preview.
- **FR-020**: Before installation or connection, Wright MUST produce an immutable Install Plan with source and pin, transport, executable or endpoint, arguments, environment requirements, credentials, host dependencies, platform checks, network and storage effects, approvals, validation steps, rollback, and blocking reasons.
- **FR-021**: Install Plans MUST be bound to the capability revision, current-machine observation, requested scope, and approving user so a material change requires a new review.
- **FR-022**: Compatibility checks MUST report observed operating system, architecture, required runtime or package manager, executable resolution, version range, container support, network need, credential need, and host-application prerequisites without changing the machine.
- **FR-023**: Wright MUST expose deterministic installer lifecycle behavior for local packages, remote endpoints, and host bridges with isolated, idempotent prepare, apply, validate, rollback, and remove boundaries.
- **FR-024**: Host-bridge onboarding MUST detect but MUST NOT install proprietary host applications; it MUST separately report supported version, required add-on, local handshake, and read-only probe availability.
- **FR-025**: Installation MUST execute only a still-current approved plan and MUST stop closed with recorded evidence when observed inputs or effects differ from the plan.
- **FR-026**: Validation MUST record initialization, discovered capability schema, optional read-only probe, environment, platform, architecture, server version or revision, outcome, limitations, and timestamp.
- **FR-027**: Validation states MUST distinguish not checked, queued, running, passed, partially passed, failed, blocked, stale, and unavailable, with explicit transition reasons.
- **FR-028**: Workspace enablement MUST be a deliberate action after installation or connection and validation, scoped to exactly one workspace, and distinct from invocation or destructive-action approval.
- **FR-029**: Credentials MUST be collected and resolved only through Wright's existing secret boundary and represented elsewhere only by opaque references and requirements.
- **FR-030**: Unknown, blocked, failed, stale, excluded, and no-public-MCP entries MUST remain discoverable with actionable reasons and MUST NOT expose misleading install or enable actions.
- **FR-031**: Wright MUST replace browser prompts for missing servers with a structured in-product report containing source, vendor, domain, use case, platform, and notes, stored separately from trusted catalog data.
- **FR-032**: Catalog updates, onboarding, validation, workspace enablement, and rollback MUST enforce existing role and approval boundaries and record auditable, redacted decisions.
- **FR-033**: Existing catalog and custom-entry data MUST migrate idempotently with a tested rollback path and no loss of user-owned state.
- **FR-034**: Normal acceptance tests MUST use deterministic local fixtures and require no paid account, license acceptance, proprietary host, external credential, GPU, or physical hardware.
- **FR-035**: The Capability Library journey MUST have component-state coverage, mocked page-level journey coverage, and a local system smoke path using stable interactive control identifiers.

### Key Entities

- **Capability Record**: A stable identity for a discoverable MCP or related candidate, including user-owned state separately from catalog-owned metadata.
- **Evidence Record**: A source-backed claim with evidence class, publisher, URL, observation time, validation environment, limitations, and field provenance.
- **Catalog Snapshot**: An immutable, versioned set of capability records plus schema, signing, freshness, digest, and provenance metadata.
- **Catalog Update Preview**: A review-bound comparison between active and candidate snapshots, including identity and field changes and verification outcomes.
- **Install Plan**: An immutable preflight describing exact requested effects, requirements, approvals, checks, validation, and rollback for one capability revision and machine observation.
- **Machine Compatibility Observation**: A time-bounded, read-only account of the current platform, architecture, runtimes, executables, host applications, and blocking or uncertain reasons.
- **Imported MCP Draft**: A non-executing normalized preview of one or more pasted server definitions, sensitive-field requirements, warnings, and errors.
- **Validation Evidence**: An immutable result for initialize, discovery, and optional read-only probes on a named environment and capability revision.
- **Workspace Capability Grant**: An explicit association between one workspace and one validated installed or connected capability; it does not grant invocation approval.
- **Missing Capability Report**: User-owned structured information about an absent or unusable capability, kept outside trusted catalog records until reviewed.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: In offline acceptance testing, an engineer can search and filter every bundled catalog entry, inspect compatibility and evidence, and identify a usable or honestly blocked result in under two minutes.
- **SC-002**: A valid approved catalog update adds the Onshape Labs FeatureScript MCP without a code change, while 100% of custom entries, explicit disablement, install state, workspace grants, and credential references remain unchanged through activation, restart, and rollback.
- **SC-003**: 100% of altered, expired, replayed, downgraded, unapproved, schema-invalid, alias-conflicting, and interrupted catalog fixtures fail closed while the previous catalog remains readable.
- **SC-004**: An engineer can reach an exact preflight in under three minutes for each supported onboarding path: catalog selection, pasted configuration, remote endpoint, local command, and host bridge.
- **SC-005**: Deterministic acceptance journeys complete installation or connection, validation, and single-workspace enablement for one local package, one remote endpoint, and one host bridge with no paid service or proprietary application.
- **SC-006**: Every incompatible, uncertain, blocked, failed, stale, or non-public capability shown in acceptance tests includes at least one specific reason and either a recovery step or an honest no-action explanation.
- **SC-007**: Secret scanning and adversarial import tests find zero raw credentials in catalog snapshots, imports after preview, install plans, validation evidence, workspace grants, workflows, histories, or logs.
- **SC-008**: 100% of material plan changes invalidate prior approval, and zero catalog updates cause an install, connection, process-state, credential, or workspace-enablement change.
- **SC-009**: At least 90% of representative engineering users in a five-person moderated usability study can distinguish discovery, installation, workspace enablement, and invocation approval and complete the primary guided path without assistance; until that study occurs, the release evidence MUST label this outcome unvalidated.
- **SC-010**: All new interactive states pass component, page-journey, local system smoke, keyboard navigation, and serious-or-critical accessibility checks required by the repository.

## Assumptions

- Catalog update administration uses Wright's existing local roles and audit identity; no external identity provider is introduced.
- The bundled snapshot remains the recovery root and is never deleted by catalog update or rollback operations.
- The safest reversible Gate A choice is a Wright-pinned signing root with versioned, expiring snapshot metadata, atomic active/previous activation, and fail-closed rollback protection; the implementation plan will choose the smallest auditable mechanism that meets those behaviors.
- Standard import compatibility initially covers the documented JSON shapes used by Claude-family clients and Visual Studio Code-family clients, plus a plain single-server JSON form; additional formats remain explicit follow-up candidates unless research proves a stable common grammar.
- The official Onshape Labs FeatureScript MCP endpoint and release are catalog evidence only in this loop. Wright will not subscribe, accept an app-store license, supply credentials, or claim live validation.
- Package installation is limited to already approved runtime or package-manager backends and pinned sources; Wright does not accept third-party licenses on the user's behalf.
- Existing MCP registration, credential, workspace, and lifecycle boundaries remain authoritative and are extended rather than replaced.
- Physical actuation, paid services, proprietary application installation, model downloads, and Rivet MCP execution are outside this feature.
