# Feature Specification: Rivet Compatibility Spike

**Feature Branch**: `055-rivet-compatibility-spike`

**Created**: 2026-08-03

**Status**: Draft - investigation and reproducibility evidence only; no production workflow capability is enabled by this slice

**Input**: User description: "Prove the pinned Rivet editor, Node runner, host-adapter, remote-debugger, offline-build, licensing, and maintenance compatibility required before production integration."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Decide Whether Rivet Can Be Safely Adopted (Priority: P1)

A Wright maintainer needs an evidence-backed decision on whether a specific Rivet release can provide the visual editor and headless execution foundations without violating Wright's workspace, security, packaging, or offline requirements.

**Why this priority**: Every later slice depends on a stable upstream baseline. Choosing a version or architecture based only on documentation risks hardening contracts against an incompatible editor or runner.

**Independent Test**: From a clean, isolated development environment, reproduce the selected source/build inputs and run the reference compatibility checks. The resulting evidence identifies one supported baseline and its known limitations, or records an explicit no-go decision.

**Acceptance Scenarios**:

1. **Given** the approved umbrella integration plan, **When** the maintainer executes the documented compatibility procedure, **Then** the procedure identifies the exact upstream source, packages, licenses, checksums, and build inputs used for the result.
2. **Given** a candidate Rivet baseline, **When** its editor and runner are evaluated, **Then** the maintainer receives a clear go, conditional-go, or no-go decision with evidence and unresolved risks.
3. **Given** an unavailable or incompatible candidate, **When** the checks fail, **Then** no production Wright feature is enabled and the failure is recorded with a safe recommended next action.

---

### User Story 2 - Prove the Required Host Boundaries (Priority: P1)

A Wright maintainer needs to verify that the visual editor can use workspace-owned persistence and that graph execution can be governed by Wright, rather than relying on browser profiles, unrestricted local files, or independent tool authority.

**Why this priority**: Workspace ownership and Wright-controlled execution are the two non-negotiable boundaries of the program.

**Independent Test**: Exercise a reference project through the candidate editor and runner, documenting the exact open/save, dataset, native capability, external-call, cancellation, and debugger seams. Demonstrate whether host injection is available or identify the smallest isolated compatibility patch.

**Acceptance Scenarios**:

1. **Given** the candidate editor, **When** its project and dataset operations are traced, **Then** the report identifies every browser, native, global-directory, and persistent-storage assumption that must be replaced or disabled for Wright.
2. **Given** the candidate runner, **When** it executes a reference graph and receives cancellation, **Then** the report records the lifecycle and event/abort behavior required by the later runner slice.
3. **Given** a graph that requests a host operation, **When** the candidate integration invokes it, **Then** the report establishes whether the official external-call mechanism can provide the required governed bridge or whether a Wright-owned approved plugin is needed.

---

### User Story 3 - Preserve Offline and Release Viability (Priority: P1)

A release maintainer needs confidence that a supported Rivet baseline can be built, packaged, and operated without downloading code, plugins, fonts, or assets at runtime and without requiring a Wright or Rivet source checkout.

**Why this priority**: Offline operation and installed-artifact support are constitutional requirements, not later optimizations.

**Independent Test**: Build the candidate editor and runner from recorded inputs, serve or execute the reference fixture with outbound network access denied, and inventory all shipped dependencies and licenses.

**Acceptance Scenarios**:

1. **Given** the selected baseline and its recorded build inputs, **When** the compatibility build runs in an isolated environment, **Then** it completes reproducibly and identifies every output asset/checksum.
2. **Given** the packaged compatibility fixture, **When** outbound package/CDN access is unavailable, **Then** the supported editor and runner path either works without a network request or fails with an explicitly documented unsupported dependency.
3. **Given** the dependency inventory, **When** it is reviewed, **Then** every direct and transitive license, security finding, platform limitation, and update responsibility has an owner or a no-go rationale.

---

### User Story 4 - Hand Off a Safe Contract to Later Slices (Priority: P2)

A maintainer beginning persistence, runner, or editor work needs a small set of verified compatibility decisions and fixtures without inheriting experimental implementation as a production dependency.

**Why this priority**: The requested incremental delivery model requires later slices to consume stable conclusions rather than rediscovering upstream behavior independently.

**Independent Test**: Review the completed spike documents and fixtures to confirm that each umbrella question has an answer, an owner, a constraint, and a follow-up contract or a documented stop condition.

**Acceptance Scenarios**:

1. **Given** a successful or conditional spike, **When** a later slice starts, **Then** it can identify the selected upstream pin, required patch status, supported capabilities, prohibited capabilities, and reusable fixture/evidence.
2. **Given** an unresolved critical compatibility issue, **When** the spike concludes, **Then** the program stops before production code and presents the smallest viable umbrella-plan amendment for approval.

### Edge Cases

- The upstream source, published package, release asset, or source map disappears or changes after a candidate is selected.
- Editor build succeeds but fetches an undeclared CDN asset, font, plugin, telemetry endpoint, or runtime package.
- The editor opens a project only through native dialogs, browser handles, IndexedDB, or a global application directory.
- A candidate provider seam is global, mutable, or incompatible with two concurrently opened Wright workspaces.
- The Node runner can execute a graph but cannot cancel, bound resources, surface events, or reject stale debugger connections.
- Remote debugging exposes an unrestricted host/port, leaks a token, or cannot operate through Wright's isolated-origin policy.
- A required upstream patch is broad, unmaintained, license-incompatible, or fails to apply cleanly to the selected pin.
- A plugin or direct MCP feature is needed to make the demo work but cannot be allowlisted, bundled, or governed by Wright.
- Native and Docker results disagree, or a claimed platform lacks evidence.
- A dependency license or security issue has no accepted mitigation.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The spike MUST identify one immutable candidate Rivet source revision and every consumed package/version, build input, checksum, and license required to reproduce the result.
- **FR-002**: The spike MUST provide an executable compatibility procedure and a small reference project that exercises editor load/save behavior, a dataset operation, headless execution, a host operation, cancellation, and remote-debugger connection where supported.
- **FR-003**: The spike MUST record whether the candidate editor supports a workspace-scoped injected IO provider, dataset provider, and constrained native capability provider; any required patch MUST be isolated, minimal, reproducible, and attributable to the selected source revision.
- **FR-004**: The spike MUST identify every candidate editor behavior that relies on browser-profile storage, browser/native file pickers, Tauri APIs, global directories, unrestricted filesystem access, or external navigation and classify it as supported through a Wright adapter, prohibited, or unresolved.
- **FR-005**: The spike MUST establish whether the candidate Node runtime can execute an immutable project fixture, emit bounded lifecycle information, receive cancellation, and connect a remote debugger without granting the editor direct Wright authority.
- **FR-006**: The spike MUST establish whether the documented host external-call mechanism is sufficient for a Wright-governed operation bridge, or document the evidence and scope required for a Wright-owned approved plugin.
- **FR-007**: The spike MUST test a reproducible editor/runner build and fixture operation with runtime package/CDN/plugin downloads denied, and MUST inventory any remaining network dependency as a release blocker.
- **FR-008**: The spike MUST inventory direct and transitive dependency licenses, security findings, asset sizes, supported-platform limitations, and maintenance/update obligations relevant to the selected baseline.
- **FR-009**: The spike MUST publish a versioned compatibility matrix that states supported, unsupported, conditional, and unverified capabilities across browser, Hermes, native runtime, Docker, and offline contexts.
- **FR-010**: The spike MUST record a go, conditional-go, or no-go recommendation with explicit criteria for progressing to the workspace-persistence, headless-runner, and editor-host-adapter slices.
- **FR-011**: The spike MUST keep all experimental assets, scripts, patches, and fixtures feature-disabled and isolated from production packages, routes, persistence schemas, and user-visible workspace functionality.
- **FR-012**: The spike MUST document rollback as removal of spike-only assets and metadata with no migration or user-authored workflow data created.
- **FR-013**: The spike MUST record commands, environment versions, inputs, output checksums, test results, and limitations so another maintainer can reproduce or invalidate the result.
- **FR-014**: The spike MUST stop and request an umbrella-plan amendment before production work if any mandatory workspace confinement, Wright-governed execution, offline operation, licensing, or packaging requirement cannot be met.

### Key Entities

- **Candidate Baseline**: One immutable Rivet source revision plus its published package versions, lockfile, patch set, checksums, license inventory, and supported-platform claim.
- **Compatibility Fixture**: A small non-production project and host harness that exercises the required editor and runner seams without user data or credentials.
- **Capability Finding**: A versioned statement of a tested editor/runner capability, its evidence, limitations, and Wright disposition: supported, adapter-required, prohibited, unresolved, or blocked.
- **Compatibility Matrix**: The consolidated set of findings by capability and deployment context, including proof status and follow-up slice owner.
- **Go/No-Go Decision**: The maintainer-approved conclusion that permits the next program slice, permits it with explicit conditions, or requires an umbrella amendment.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A second maintainer can reproduce the selected candidate build and compatibility fixture from recorded inputs and obtain matching source/package/build checksums in 100% of two independent clean-environment trials.
- **SC-002**: The completed matrix classifies 100% of the eight compatibility questions assigned to slice 0 in the umbrella research as supported, adapter-required, prohibited, unresolved, or blocked, with a linked evidence record for each.
- **SC-003**: The reference fixture completes editor load/save tracing, one dataset operation, one headless run, one host-operation request, one cancellation attempt, and one debugger-connect attempt; unsupported behavior is recorded as a typed finding rather than omitted.
- **SC-004**: The offline trial records zero undeclared runtime download requests across the supported fixture path, or the decision is no-go/conditional-go with every request identified and assigned a remediation.
- **SC-005**: The dependency inventory accounts for 100% of shipped direct dependencies and their transitive license/security status before any production package pin is proposed.
- **SC-006**: The spike leaves zero production routes, persistent schemas, enabled user features, user-authored workflows, or unbounded credentials behind when its fixtures are removed.
- **SC-007**: A later-slice maintainer can locate the selected pin, patch status, supported capabilities, prohibited capabilities, evidence commands, and go/no-go criteria in under 10 minutes from the slice documentation.

## Assumptions

- The umbrella planning commit `21d2982` is the sole prerequisite and this slice branch starts from that commit.
- The spike may fetch and build upstream Rivet only in isolated development/test locations; it must not add Rivet or Node as a required Wright runtime dependency or modify production packaging.
- The upstream MIT license is a candidate, not final approval; the full dependency and notice inventory determines whether the baseline can progress.
- A small maintained patch is acceptable only when a documented official injection seam is insufficient and the patch remains isolated, reproducible, and reviewable.
- The fixture may use mock Wright host operations and mock credentials; it may not call live engineering tools, persist user data, or expose real secrets.
- The default decision is no-go for any requirement that lacks reproducible evidence. A conditional-go must name the exact constraint that later slices must enforce.
- The slice ends after the human-approved plan, tasks, analysis, experimental compatibility work, and evidence are complete; it does not start workspace persistence, production runner, editor tab, or governed tool implementation.
