# Feature Specification: Native Hermes Installation

**Feature Branch**: `050-native-hermes-install`

**Created**: 2026-07-28

**Status**: Ready for Planning

**Input**: User description: "Deliver a production-ready native Hermes installation for Wright that Hermes installs, manages, updates, rolls back, and removes without requiring Git, Docker, Node.js, npm, a Wright source checkout, WRIGHT_REPO_DIR, or manual Python package commands. Preserve the Docker path, provider-neutral MCP behavior, and all production release gates."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Install and Start Wright from Hermes (Priority: P1)

A Hermes user installs Wright through Hermes' supported plugin mechanism and runs `/wright start`. Hermes obtains the compatible Wright runtime, starts it, and presents the Wright UI without asking the user to locate source code or install development tools.

**Why this priority**: This is the intended path for most Wright users and is the minimum viable product experience.

**Independent Test**: Begin with a clean supported Hermes environment that has no Git, Docker, Node.js, npm, Wright checkout, `WRIGHT_REPO_DIR`, or preinstalled Wright package; install the candidate plugin through the third-party interface, run `/wright start`, and verify the UI, Wright health, Hermes connectivity, MCP transport, and catalog.

**Acceptance Scenarios**:

1. **Given** a supported clean Hermes installation, **When** the user installs Wright through the supported plugin interface, **Then** Hermes automatically installs a compatible, complete Wright runtime without requiring a source checkout or manual package command.
2. **Given** a newly installed Wright plugin, **When** the user runs `/wright start`, **Then** Wright starts from installed artifacts, reports healthy Wright and Hermes connections, and provides a usable UI URL.
3. **Given** Git, Docker, Node.js, npm, `WRIGHT_REPO_DIR`, and Wright source files are unavailable, **When** install and start are exercised, **Then** neither operation attempts to invoke or locate any of them.
4. **Given** a runtime cannot be installed or started, **When** the operation fails, **Then** the user receives a safe, actionable error and no partially active installation is reported as healthy.

---

### User Story 2 - Operate Wright Reliably from Hermes (Priority: P1)

A Hermes user controls and diagnoses the native Wright runtime with `/wright start`, `/wright status`, `/wright doctor`, and `/wright stop`, while continuing to use the existing engineering MCP catalog and workspace experience.

**Why this priority**: A native installation is usable only if ordinary lifecycle and diagnostics work without repository knowledge.

**Independent Test**: From a completed clean installation, exercise start, repeated start, status, doctor, catalog discovery, MCP communication, workspace creation and reopening, stop, repeated stop, and restart while verifying honest state and retained data.

**Acceptance Scenarios**:

1. **Given** Wright is stopped, **When** the user runs `/wright start`, **Then** Hermes starts exactly one isolated compatible runtime and reports its health and UI location.
2. **Given** Wright is already healthy, **When** the user runs `/wright start` again, **Then** the existing runtime is reused rather than duplicated.
3. **Given** Wright is installed in any supported lifecycle state, **When** the user runs `/wright status` or `/wright doctor`, **Then** the result distinguishes plugin, runtime, API, UI, Hermes, MCP, catalog, configuration, and workspace health with actionable remediation.
4. **Given** Wright is running, **When** the user runs `/wright stop`, **Then** the Wright-owned runtime stops cleanly without stopping Hermes or unrelated processes.
5. **Given** an engineering MCP server is selected through the existing catalog, **When** it is used through native Wright, **Then** the provider-neutral launch, discovery, progress, authorization, and workspace behavior remains unchanged.

---

### User Story 3 - Upgrade and Roll Back Safely (Priority: P1)

A Hermes user receives a compatible Wright update without losing workspaces or configuration and can return to the previously working version when an update fails.

**Why this priority**: Native installation becomes the primary path only when routine updates are safe and recoverable.

**Independent Test**: Install the previous stable public version, create representative workspaces and user configuration, upgrade to the candidate, verify retained data and compatibility, induce a failed update, and exercise the supported rollback path.

**Acceptance Scenarios**:

1. **Given** the previous stable Wright installation with user data, **When** a compatible update is applied through Hermes, **Then** plugin and runtime versions become compatible and all user-owned workspaces and configuration remain usable.
2. **Given** an update fails before activation, **When** recovery completes, **Then** the last known-good runtime remains available and the failed candidate is not reported as active.
3. **Given** an activated update fails its health verification, **When** rollback is requested or automatically required by the documented policy, **Then** the prior compatible runtime is restored without reverting or deleting user data.
4. **Given** a plugin/runtime version combination is unsupported, **When** start or update is attempted, **Then** activation fails closed with the compatible version range and remediation shown to the user.

---

### User Story 4 - Uninstall Without Accidental Data Loss (Priority: P2)

A Hermes user removes Wright cleanly while preserving their work by default and may separately request deletion of Wright-owned data with clear scope and confirmation.

**Why this priority**: Uninstall behavior must be predictable and safe before the native path can be offered broadly.

**Independent Test**: Create user data, uninstall through Hermes, prove plugin and runtime removal while data remains, reinstall and recover the data, then perform an explicit purge and verify that only Wright-owned data is deleted.

**Acceptance Scenarios**:

1. **Given** an installed Wright runtime with user workspaces, **When** the plugin is uninstalled normally, **Then** Wright processes, runtime artifacts, and plugin integration are removed while user data and user-authored workspace files remain.
2. **Given** a preserved data set after uninstall, **When** Wright is reinstalled, **Then** the user can reopen compatible workspaces and configuration.
3. **Given** the user explicitly requests data purge, **When** the purge scope is confirmed, **Then** only documented Wright-owned data is deleted and unrelated Hermes or user files remain untouched.
4. **Given** Wright is running during uninstall, **When** removal begins, **Then** the runtime is stopped safely before removable artifacts are deleted.

---

### User Story 5 - Publish a Complete Native Release (Priority: P1)

A release owner publishes a Wright version only when the native Hermes plugin and compatible runtime are distributed and verified alongside the existing Python, container, documentation, and release artifacts.

**Why this priority**: A release is incomplete for the majority installation path if its native Hermes artifacts cannot be installed by a third party.

**Independent Test**: Rehearse with locally built candidate artifacts, then verify a production release contract that consumes published plugin and runtime artifacts rather than repository source and blocks final completion on any native lifecycle failure.

**Acceptance Scenarios**:

1. **Given** a feature or pull-request build, **When** native installation tests run, **Then** they use local candidate artifacts or an isolated test channel and perform no stable public publication.
2. **Given** a production release candidate, **When** release gates run, **Then** native plugin distribution, runtime distribution, clean install, start, upgrade, rollback, uninstall, and public-install verification are mandatory.
3. **Given** native verification fails or a required artifact is missing, **When** release completion is evaluated, **Then** the release remains incomplete and downstream final-release claims do not publish.
4. **Given** all gates pass, **When** public verification runs, **Then** it installs exactly the published artifacts without a source checkout and records their versions and immutable identities in release evidence.
5. **Given** the existing Docker installation path, **When** the same release is verified, **Then** required Docker images and registries remain available and pass their existing production checks.

---

### User Story 6 - Understand Installation and Package Roles (Priority: P2)

A user or operator can select the native Hermes or Docker path, understand what each distributed artifact does, and follow concise install, upgrade, rollback, uninstall, and troubleshooting guidance.

**Why this priority**: The current helper-package description and repository-based plugin instructions make the primary path ambiguous.

**Independent Test**: Have a new evaluator follow only the public installation documentation for each supported path and verify that every command, prerequisite, package role, data-retention rule, and recovery instruction matches executable behavior.

**Acceptance Scenarios**:

1. **Given** a Hermes user, **When** they read the installation guide, **Then** the primary native path contains one supported plugin-install operation followed by `/wright start`, with no development prerequisites.
2. **Given** a Docker user, **When** they read the installation guide, **Then** the turnkey isolated path remains complete and is clearly distinguished from native Hermes installation.
3. **Given** any public Wright package or plugin artifact, **When** its documentation and metadata are inspected, **Then** it has one unambiguous role, lifecycle owner, compatibility contract, and supported installation audience.
4. **Given** troubleshooting or removal needs, **When** the user follows the documentation, **Then** commands and expected data effects agree with automated lifecycle tests.

### Edge Cases

- Network interruption, insufficient disk space, or permission failure during first install, update download, activation, rollback, or uninstall.
- Concurrent `/wright start`, update, stop, or uninstall requests from multiple Hermes sessions.
- Hermes restarts or crashes while the Wright runtime is running or while a lifecycle transition is in progress.
- A stale runtime process, stale lifecycle lock, port collision, or health endpoint that accepts a connection but is not the expected Wright instance.
- Plugin and runtime versions are individually valid but outside their declared compatibility ranges.
- The previous stable version has a data format that requires migration, and migration fails or cannot be safely reversed.
- User configuration contains provider credentials, API keys, tokens, unusual paths, or non-ASCII characters.
- A workspace lives outside Wright's default data directory and must never be deleted by uninstall or purge.
- The current version is already installed, a requested update is older, or rollback artifacts are unavailable.
- Public package or plugin service is unavailable after release while other release artifacts succeed.
- A supported operating system lacks one optional MCP host application; core Wright installation must still succeed and catalog status must remain honest.
- Native and Docker Wright installations coexist on one machine and contend for ports or data directories.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Wright MUST provide one supported Hermes plugin installation interface for third-party users.
- **FR-002**: Installing the plugin MUST automatically obtain and configure a compatible complete Wright runtime.
- **FR-003**: The native installation and start paths MUST NOT require or invoke Git, Docker, Node.js, npm, a Wright source checkout, `WRIGHT_REPO_DIR`, or user-issued Python package commands.
- **FR-004**: The installed native runtime MUST include the Wright API, internal runtime capabilities, data migrations, MCP gateway and catalog capabilities, and the prebuilt web UI required for ordinary operation.
- **FR-005**: `/wright start` MUST launch only installed runtime artifacts and MUST NOT perform a frontend build.
- **FR-006**: Hermes MUST own plugin-triggered install, activation, health verification, update, rollback, stop, uninstall, and purge orchestration while the Wright runtime remains isolated from the Hermes process.
- **FR-007**: `/wright start` MUST be idempotent and prevent duplicate Wright runtime instances for the same installation and configuration.
- **FR-008**: `/wright stop` MUST stop only the Wright-owned runtime and MUST be idempotent.
- **FR-009**: `/wright status` MUST report the installed plugin version, installed and active runtime versions, lifecycle state, compatibility state, API and UI health, Hermes connection, MCP transport, catalog availability, and relevant data location without exposing secrets.
- **FR-010**: `/wright doctor` MUST diagnose installation integrity, version compatibility, process ownership, ports, configuration, data access, Wright health, Hermes health, MCP transport, catalog health, and available recovery actions.
- **FR-011**: Existing `/wright catalog`, catalog search, catalog information, and catalog installation commands MUST continue to work through the native runtime.
- **FR-012**: A successful start MUST provide a usable Wright UI location and the UI MUST accurately report Wright API and Hermes connectivity.
- **FR-013**: Native Wright MUST preserve provider-neutral MCP discovery, launch, authorization, progress, cancellation, timeout, workspace binding, and concurrent-session behavior.
- **FR-014**: Lifecycle operations MUST coordinate concurrent requests so that each requested transition has one truthful terminal result and cannot corrupt runtime or user state.
- **FR-015**: Lifecycle state MUST distinguish not installed, installing, stopped, starting, healthy, degraded, updating, rolling back, stopping, uninstalling, failed, and recovery-required conditions where applicable.
- **FR-016**: A failed install or update MUST NOT be presented as active or healthy and MUST leave either a recoverable incomplete state or the last known-good version.
- **FR-017**: The plugin and runtime MUST publish an explicit, machine-verifiable compatibility contract and fail closed on unsupported combinations.
- **FR-018**: Updating from the previous stable public version to the candidate version MUST preserve compatible workspaces, user configuration, catalog choices, and Wright-owned state.
- **FR-019**: Data migrations MUST be ordered, durable, diagnosable, safe to retry, and prevented from silently downgrading incompatible user data.
- **FR-020**: The supported rollback behavior MUST restore the previous compatible runtime without deleting or reverting user-owned data.
- **FR-021**: Normal uninstall MUST remove the plugin integration, managed runtime artifacts, and active Wright processes while preserving user data by default.
- **FR-022**: Explicit purge MUST require a distinct, deliberate request, disclose its scope, and delete only documented Wright-owned data.
- **FR-023**: Uninstall and purge MUST NOT delete external workspaces, unrelated Hermes data, credentials owned by other applications, or files outside the resolved Wright-owned scope.
- **FR-024**: Reinstallation after a normal uninstall MUST discover and reuse preserved compatible Wright user data.
- **FR-025**: Credentials, tokens, passwords, and user secrets MUST NOT be bundled in artifacts, copied into release evidence, written to command output, or exposed in logs or health results.
- **FR-026**: Lifecycle logs and diagnostics MUST identify operations and failures without recording secret values or unbounded user content.
- **FR-027**: Every public Wright distribution artifact MUST have one documented purpose, owner, compatibility relationship, update path, and uninstall behavior.
- **FR-028**: Exactly one public artifact MUST be designated as the complete managed native Wright runtime; the existing ambiguous helper-only positioning of `wright-engineering` MUST either be replaced or explicitly superseded by a clearly named runtime artifact.
- **FR-029**: The native runtime distribution MUST contain only approved runtime files and dependencies and MUST work without imports from a repository or undeclared private packages.
- **FR-030**: Candidate native plugin and runtime artifacts MUST be buildable and installable in an isolated test channel without publishing unreleased content to stable public channels.
- **FR-031**: Automated clean-install validation MUST begin without Git, Docker, Node.js, npm, a Wright checkout, `WRIGHT_REPO_DIR`, or preinstalled Wright packages.
- **FR-032**: Clean-install validation MUST use the same supported plugin installation interface offered to third parties and MUST prove automatic runtime installation.
- **FR-033**: Native acceptance validation MUST cover install, start, health, UI, Hermes connection, MCP transport, catalog, workspace creation and reopening, stop, restart, update from previous stable, rollback, uninstall, reinstall with preserved data, and explicit purge.
- **FR-034**: Native acceptance validation MUST exercise failure recovery for interrupted install, failed activation, failed migration, incompatible versions, concurrent lifecycle requests, stale process state, and unavailable rollback artifacts.
- **FR-035**: Validation MUST cover every operating-system and architecture combination publicly claimed as supported by both Wright native installation and Hermes; unvalidated combinations MUST NOT be newly claimed.
- **FR-036**: Production release orchestration MUST distribute the compatible native Hermes plugin and managed runtime and MUST block release completion unless published-artifact native install, start, update, rollback, and uninstall verification succeeds.
- **FR-037**: Public-install verification MUST consume published immutable plugin and runtime artifacts rather than repository source or locally substituted files.
- **FR-038**: Native release evidence MUST record source version, plugin and runtime versions, compatibility decision, immutable artifact identities, tested platforms, lifecycle results, and any unsupported platform exclusions without secrets.
- **FR-039**: Required PyPI, GHCR, Docker Hub, GitHub Release, documentation, Docker build, Docker verification, and existing security and release-contract gates MUST remain mandatory.
- **FR-040**: A production release MUST NOT be reported complete when any required native Hermes or Docker distribution, lifecycle, or public-install gate is missing, skipped, or failing.
- **FR-041**: Feature-branch and pull-request validation MUST use local candidate artifacts or an isolated non-production channel and MUST NOT mutate production PyPI, Docker registries, GitHub Releases, documentation channels, or the stable Hermes channel.
- **FR-042**: Installation, upgrade, rollback, uninstall, purge, troubleshooting, compatibility, package-role, platform-support, and release documentation MUST match the executable contracts.
- **FR-043**: Docker MUST remain a supported turnkey isolated installation path and its existing runtime and provider-neutral MCP integration MUST not regress.
- **FR-044**: Native installation MUST NOT add MCP-specific host software to Wright's base installation merely to make catalog validation pass.
- **FR-045**: All required unit, integration, packaging, plugin, frontend, MCP, clean-install, lifecycle, security, and release-contract tests and both repository merge gates MUST pass without native-acceptance skip flags before the feature is complete.

### Key Entities

- **Hermes Plugin Installation**: The Hermes-visible integration, its installed version, declared compatible runtime range, lifecycle commands, and installation status.
- **Managed Wright Runtime**: The complete native Wright artifact selected for a plugin version, including its immutable identity, installed location, active state, health, and retained rollback predecessor.
- **Compatibility Contract**: Machine-verifiable rules that map plugin, runtime, Hermes, platform, and data-format versions to supported or rejected combinations.
- **Lifecycle Operation**: A uniquely identified install, start, stop, update, rollback, uninstall, or purge request with a requested state, current state, terminal result, diagnostics, and recovery guidance.
- **Wright-Owned Data Scope**: Documented directories and records managed by Wright, separated from user-authored external workspaces and unrelated Hermes data.
- **Release Evidence**: The immutable plugin/runtime identities, compatibility result, platform matrix, native lifecycle verification, existing artifact verification, and completion decision for one product release.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A new user on every supported native platform completes plugin installation and reaches a healthy Wright UI using no more than one supported plugin-install operation followed by `/wright start`.
- **SC-002**: One hundred percent of clean-install tests pass in environments containing none of Git, Docker, Node.js, npm, Wright source files, `WRIGHT_REPO_DIR`, or preinstalled Wright packages.
- **SC-003**: On the supported reference environments, 95 percent of successful first starts reach a healthy API and usable UI within two minutes after runtime installation completes, and every slower or failed start reports actionable status.
- **SC-004**: Repeated start and stop tests create zero duplicate Wright instances and leave zero unintended Wright processes after stop or uninstall.
- **SC-005**: One hundred percent of status and doctor test scenarios report the correct plugin, runtime, compatibility, process, API, UI, Hermes, MCP, catalog, and recovery state without exposing secret values.
- **SC-006**: Upgrade tests from the previous stable public version retain 100 percent of representative workspaces, configuration, catalog choices, and user-owned files.
- **SC-007**: Every injected pre-activation or post-activation update failure ends with either the prior healthy runtime restored or an explicit recovery-required state; zero failures are reported as healthy.
- **SC-008**: Normal uninstall preserves 100 percent of representative user data, and explicit purge deletes 100 percent of in-scope Wright-owned test data while deleting zero out-of-scope files.
- **SC-009**: One hundred percent of plugin/runtime incompatibility combinations in the contract suite fail before activation and identify a supported remediation.
- **SC-010**: Automated artifact inspection and log scanning detect zero bundled credentials, tokens, user secrets, repository-only imports, or undeclared runtime dependencies.
- **SC-011**: Native provider-neutral MCP and existing Docker regression suites pass with no provider-specific exceptions introduced for the native install path.
- **SC-012**: Every production release reports one native plugin identity and one compatible runtime identity, and all required published-artifact lifecycle checks pass before the release is declared complete.
- **SC-013**: One hundred percent of publicly claimed native platform combinations have clean-install and lifecycle evidence; no untested platform appears in public support claims.
- **SC-014**: A third-party evaluator can select native Hermes or Docker installation and complete the documented path without consulting repository-development instructions.
- **SC-015**: All required local suites, the development merge gate, the production merge gate, and all required pull-request checks complete successfully with zero native-install acceptance skips.

## Assumptions

- Production availability depends on a future released Hermes version exposing a
  supported Python package-plugin lifecycle for versioned artifacts. Until that
  released interface passes the public acceptance suite, native Wright remains
  release-blocked and the Git-only interface is not a substitute.
- The native runtime may use a public package repository internally, but that mechanism is hidden behind Hermes installation and lifecycle commands.
- The implementation plan will choose whether `wright-engineering` becomes the complete native runtime or a new clearly named runtime artifact replaces it; two overlapping public runtime packages are not acceptable.
- The previous stable public Wright version is the required upgrade baseline for release acceptance.
- User data is preserved across normal upgrades, rollback, and uninstall unless the user issues a separate explicit purge request.
- User-authored workspaces outside a Wright-owned data directory are never purge targets.
- Docker remains the turnkey isolated option and is released and verified for every platform Wright currently claims for Docker.
- Optional proprietary or host-specific engineering applications remain separate MCP prerequisites and are not bundled into the native runtime.
- Internet access may be required to obtain public plugin and runtime artifacts, but installed Wright core operation retains the project's offline-first behavior and provides documented offline installation or caching guidance where the underlying Hermes plugin mechanism supports it.
- The operator's attached goal grants approval to proceed continuously through all Spec Kit phases on the feature branch; separate authorization is still required before merging into `dev` or `main`.
