# Feature Specification: Engineering MCP Catalog

**Feature Branch**: `034-engineering-mcp-catalog`

**Created**: 2026-06-26

**Status**: Draft

**Input**: User description: "Implement docs/mcp-catalog/engineering_mcp_research_handoff.md as a new sprint. The research predates the repository, so adapt component layout to the current UI cards. Add strong test coverage per the constitution. Focus first on running in a single Ubuntu container. If an MCP depends on unavailable commercial or host software, installation can still pass when it clearly reports that the host software is not installed. Fully tested MCP servers must appear first, followed by servers that might work, followed by servers that do not work. For non-working MCP servers, create a GitHub PR or equivalent follow-up record so someone can investigate later."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Browse Statused Engineering MCPs (Priority: P1)

An engineer opens the MCP catalog and sees engineering-focused MCP entries grouped by practical readiness: fully tested servers first, then servers that might work, then servers that do not work or are blocked. Each entry clearly shows verification status, platform compatibility, required host software, credentials, risk, and the reason it is available, blocked, or deferred.

**Why this priority**: The catalog is only useful if users can immediately distinguish safe installable servers from uncertain or non-working entries without losing track of valuable future integrations.

**Independent Test**: Can be fully tested by loading the catalog in the product and verifying that known verified entries, uncertain entries, wrapper candidates, and blocked entries are visible in the correct order with clear status details.

**Acceptance Scenarios**:

1. **Given** the catalog contains fully tested, possible, and non-working MCP entries, **When** the user views the MCP catalog, **Then** fully tested entries appear before possible entries and non-working entries appear last.
2. **Given** an entry requires host software that may not exist in the local environment, **When** the user views the entry, **Then** the required software and limitation are displayed without implying the server is fully usable.
3. **Given** an entry is a wrapper candidate or capability alias rather than a verified MCP server, **When** the user views the catalog, **Then** the entry is labeled so users do not mistake it for an installable server.

---

### User Story 2 - Validate Installability in One Local Linux Environment (Priority: P1)

An operator runs catalog validation in a single local Linux container and receives deterministic results for each supported engineering MCP entry. Servers with unavailable commercial CAD, GUI, hardware, or licensed dependencies are allowed to report a clear "host software not installed" or "dependency unavailable" result instead of failing ambiguously.

**Why this priority**: The first support target is a reproducible local environment that can separate package/install failures from expected host-software limitations.

**Independent Test**: Can be fully tested by running the validation workflow in the local Linux container and checking that installable servers are probed, blocked entries are skipped with reasons, and host-dependent failures are classified as expected when appropriate.

**Acceptance Scenarios**:

1. **Given** a verified server has an install command and no unavailable host dependency, **When** validation runs, **Then** the server receives a tested success, tested failure, or explicit diagnostic result.
2. **Given** a server requires unavailable commercial CAD, desktop GUI software, hardware, or credentials, **When** validation runs, **Then** the result records the missing dependency as an expected limitation rather than a generic failure.
3. **Given** an entry has no verified source URL or install command, **When** validation runs, **Then** the entry is blocked from automated install and explains what evidence is missing.

---

### User Story 3 - Track Follow-Up Work for Broken MCPs (Priority: P2)

A maintainer can identify MCP servers that do not work and has a follow-up record suitable for later investigation, including source evidence, observed failure, expected behavior, environment, and suggested next action.

**Why this priority**: Non-working servers should not disappear from the ecosystem map; they need actionable follow-up so someone can fix, verify, or exclude them later.

**Independent Test**: Can be fully tested by marking one sample MCP validation as non-working and verifying that a follow-up record is generated with enough information to create or link a GitHub pull request or issue.

**Acceptance Scenarios**:

1. **Given** validation classifies a server as non-working, **When** follow-up generation runs, **Then** the system creates or records an investigation item with the server identity, failure reason, reproduction context, and recommended owner action.
2. **Given** a non-working server already has a follow-up record, **When** validation runs again, **Then** the catalog links to the existing record instead of creating duplicate follow-up work.

---

### User Story 4 - Report Missing or Newly Found MCPs (Priority: P3)

An engineer can add a missing engineering MCP candidate to the catalog without overstating its status. User-reported entries remain visible as blocked or possible until source and install evidence are verified.

**Why this priority**: The engineering MCP ecosystem changes quickly, so the catalog must accept new candidates while preserving uncertainty and safety.

**Independent Test**: Can be fully tested by submitting a missing MCP candidate and verifying that it appears with a user-reported or pending status, not as a verified installable server.

**Acceptance Scenarios**:

1. **Given** a user submits a new MCP candidate with incomplete evidence, **When** the catalog updates, **Then** the candidate appears as pending verification and is excluded from automated installation.
2. **Given** a submitted candidate duplicates an existing alias or wrapper candidate, **When** the catalog updates, **Then** it is reconciled with the existing entry instead of creating a misleading duplicate.

### Edge Cases

- An MCP package installs successfully but cannot run because credentials, host CAD software, a desktop app, a GUI session, hardware, or a license is unavailable.
- A README claims generic Linux support, but architecture-specific support is unknown.
- A high-risk server exposes code execution, CAD mutation, cloud upload, or machine-control capabilities.
- A catalog row is a documentation server, API wrapper candidate, UI standard, capability alias, or watchlist item rather than an MCP server.
- A source URL is missing, stale, unavailable, or points to a package with no MCP protocol support.
- The same server appears through multiple names, aliases, or prior catalog sources.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The catalog MUST store a stable identity, display name, aliases, source evidence, verification state, install confidence, risk level, deployment mode, required host software, credential requirements, and health-check status for each engineering MCP entry.
- **FR-002**: The catalog MUST track platform support separately for Windows 11 x64, Linux x64, Linux ARM64, macOS x64, and macOS ARM64 using explicit status values and notes.
- **FR-003**: The catalog MUST distinguish verified MCP servers, documentation MCPs, community MCPs, user-reported entries needing URLs, wrapper candidates, capability aliases, UI or web standards, watchlist entries, and excluded entries.
- **FR-004**: The catalog MUST include the high-priority verified, community, seeded, blocked, and wrapper-candidate entries from the engineering MCP research handoff.
- **FR-005**: The catalog MUST order entries so fully tested working servers appear first, entries that might work appear next, and non-working or blocked entries appear last.
- **FR-006**: Users MUST be able to see why an entry is installable, possible, blocked, non-working, disabled, or unsafe.
- **FR-007**: Automated validation MUST attempt only entries with sufficient install evidence and MUST skip or block entries that lack verified source or install details.
- **FR-008**: Automated validation MUST classify unavailable host software, credentials, commercial licenses, GUI apps, and hardware as explicit dependency limitations when those dependencies are required.
- **FR-009**: High-risk and safety-critical entries MUST be disabled by default or restricted to read-only/simulation behavior until explicit approval is available.
- **FR-010**: The UI MUST update existing MCP cards or catalog presentation so verification state, install tier, platform support, required dependencies, credentials, risk, and validation result are visible without requiring users to open raw data.
- **FR-011**: Interactive catalog controls MUST expose stable test identifiers for component and integration testing.
- **FR-012**: Non-working MCP entries MUST produce or link to a follow-up investigation record suitable for GitHub review.
- **FR-013**: The system MUST prevent duplicate follow-up records for the same server and failure context.
- **FR-014**: Users MUST be able to add or report missing MCP candidates as seed entries without granting them verified status.
- **FR-015**: The implementation MUST include automated tests covering catalog data validation, ordering, dependency-limited validation outcomes, safety defaults, UI rendering, and follow-up record generation.

### Key Entities *(include if feature involves data)*

- **MCP Catalog Entry**: A tracked engineering MCP, documentation MCP, wrapper candidate, alias, standard, watchlist item, or excluded candidate with evidence and status metadata.
- **Platform Support Record**: Per-platform compatibility status, tested flag, and notes for a catalog entry.
- **Install Method**: A documented way to install or probe a server, including command family, arguments, environment requirements, and whether automation is allowed.
- **Validation Result**: The most recent outcome of probing an entry, including status, diagnostics, tested platform, dependency limitations, and timestamps.
- **Safety Policy**: Default enablement, risk level, approval gates, and read-only or simulation constraints attached to a catalog entry.
- **Follow-Up Record**: A linkable investigation artifact for non-working entries, including observed failure, reproduction environment, evidence, and next action.
- **Missing MCP Report**: User-submitted candidate data that can become a catalog seed entry after normalization and deduplication.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 100% of catalog entries show a verification state, risk level, platform support record for all required platform keys, and a clear installability tier.
- **SC-002**: At least 95% of users reviewing the catalog can identify which entries are fully tested, might work, or do not work within 30 seconds.
- **SC-003**: Validation in the first supported local Linux environment completes for the seeded catalog without unclassified failures.
- **SC-004**: 100% of high-risk or safety-critical entries are disabled by default or visibly restricted before approval.
- **SC-005**: 100% of non-working validation outcomes create or link to a follow-up investigation record.
- **SC-006**: Automated tests cover every functional requirement with unit, component, integration, or end-to-end coverage appropriate to the behavior.
- **SC-007**: No entry with missing source or install evidence is presented as fully tested or automatically installable.

## Assumptions

- The first runnable target is one local Ubuntu-based container; other operating systems and architectures are tracked but may remain untested until dedicated environments exist.
- Commercial CAD tools, desktop GUI applications, hardware controllers, and licensed vendor software may not be available in the first validation environment.
- A clear dependency-missing diagnostic is an acceptable validation result for host-dependent MCPs.
- Existing MCP catalog cards and registry surfaces should be extended rather than replaced unless the current layout cannot display the required status data.
- Follow-up work for broken servers may be represented locally when direct GitHub PR creation is unavailable in the execution environment, as long as the record is ready to convert into a PR or issue.
