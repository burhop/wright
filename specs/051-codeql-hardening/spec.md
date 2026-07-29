# Feature Specification: CodeQL Security Hardening

**Feature Branch**: `051-codeql-hardening`

**Created**: 2026-07-29

**Status**: Draft

**Input**: User description: "Address only the 14 currently open CodeQL alerts, merge the verified change into dev, and leave dev ready for a later production merge without changing main."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Safely Check Local Services (Priority: P1)

An administrator can verify an intentionally configured local Hermes or local inference service without allowing that health-check feature to access unrelated or sensitive network targets.

**Why this priority**: The critical network-request finding can expose local or cloud infrastructure, while local service checks are required for Wright's primary installation model.

**Independent Test**: Configure representative loopback services and confirm they can be checked, then submit malicious, ambiguous, redirected, metadata, link-local, and DNS edge-case targets and confirm every unsafe request is rejected before protected content is reached.

**Acceptance Scenarios**:

1. **Given** an intentional HTTP or HTTPS service on loopback, **When** an administrator checks its health, **Then** Wright reports the service result without weakening the network policy.
2. **Given** a target using an unsupported scheme, embedded credentials, a metadata or link-local address, an unsafe redirect, or an ambiguous address form, **When** a health check is requested, **Then** Wright rejects it without contacting the protected destination.
3. **Given** a hostname whose resolved destination changes or includes both safe and unsafe addresses, **When** the request is evaluated and sent, **Then** every contacted address remains within the permitted policy.

---

### User Story 2 - Keep Requests Inside Authorized Boundaries (Priority: P1)

An engineer can use vault files, registered workspaces, session titles, package checks, and file viewers while crafted input cannot escape Wright's authorized filesystem, parser, package, or browser-content boundaries.

**Why this priority**: These high-severity findings can create or access arbitrary paths, trigger costly parsing, misclassify external input, or load untrusted content.

**Independent Test**: Exercise each input boundary with valid inputs and with encoded traversal, sibling-prefix, symbolic-link, repeated-input, regular-expression metacharacter, malformed package, malformed Git URL, and non-same-origin content cases; valid workflows continue and unsafe inputs fail closed.

**Acceptance Scenarios**:

1. **Given** a vault request, **When** its canonical target would leave the configured vault through traversal, encoding, a sibling prefix, or a symbolic link, **Then** access is denied.
2. **Given** a session creation request, **When** its workspace is neither registered nor under Wright's managed workspace root, **Then** Wright does not create the directory or session.
3. **Given** valid and adversarial title, glob, package, Git URL, iframe, and document-viewer inputs, **When** they are processed, **Then** valid behavior is preserved and malicious input cannot expand authority, cause unbounded work, or load an insecure external resource.

---

### User Story 3 - Receive Safe, Traceable Failures (Priority: P2)

An engineer receives a concise actionable failure and trace identifier, while operators retain complete diagnostic details in protected structured logs and security scanning accurately distinguishes production fixes from test-only or proven-safe cases.

**Why this priority**: Internal exception details can expose paths, credentials, commands, or service topology, but removing all diagnostic context would make local support impractical.

**Independent Test**: Force failures at each affected client boundary and confirm responses contain a generic message and trace identifier but no sensitive exception content, while correlated structured logs retain the root cause. Confirm the scanner closes production instances and records precise evidence-backed outcomes for the two disposition-specific findings.

**Acceptance Scenarios**:

1. **Given** an internal failure, **When** an API, event stream, or HTML response is returned, **Then** the client receives a generic message and trace identifier without internal details.
2. **Given** that same failure, **When** an operator searches protected logs using the trace identifier, **Then** the complete actionable cause is available.
3. **Given** the current CodeQL alert set, **When** the feature is verified on dev, **Then** all production alerts are resolved and only the documented test-only and proven-safe classifications are dismissed.

### Edge Cases

- Encoded separators, dot segments, alternate path separators, case differences, sibling-prefix directories, and symbolic links must not bypass canonical containment.
- IPv4, IPv6, mapped addresses, integer or unusual textual IP forms, user-info syntax, fragments, DNS aliases, multiple DNS answers, rebinding, and redirect chains must not bypass network policy.
- A valid loopback service must remain usable even though metadata and link-local destinations are rejected.
- Empty, extremely long, repeated, Unicode, and whitespace-heavy title input must finish predictably and obey a documented length bound.
- Glob text containing backslashes and every regular-expression metacharacter must be interpreted literally except for explicitly supported glob tokens.
- Package identifiers and Git URLs that merely contain trusted-looking substrings must not be accepted.
- Error text containing paths, credentials, command output, query strings, or internal endpoints must never reach clients.
- Existing safe same-origin file previews must continue to work without weakening iframe sandboxing.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Wright MUST allow intentional HTTP and HTTPS health checks for legitimate local Hermes and local inference endpoints while preventing requests to prohibited targets.
- **FR-002**: Health-check validation MUST reject unsupported or ambiguous URL forms, metadata and link-local destinations, unsafe DNS results, and redirects that leave the permitted policy.
- **FR-003**: Wright MUST canonicalize every requested vault target and prove containment beneath the configured vault before reading or writing it.
- **FR-004**: A supplied session workspace MUST reference an existing registered directory and MUST never be created by the request; when no workspace is supplied, Wright MAY create only a generated location beneath its managed workspace root.
- **FR-005**: Title command parsing MUST have predictable bounded cost and MUST enforce a reasonable title-length limit without changing ordinary title behavior.
- **FR-006**: Glob translation MUST treat every regular-expression metacharacter literally except for the explicitly supported glob tokens.
- **FR-007**: Package identifiers MUST be strictly validated for their intended package operation, and Git repository references MUST be parsed as Git URLs rather than accepted through trusted-looking substrings.
- **FR-008**: Client-facing failures MUST contain a generic actionable message and trace identifier and MUST NOT disclose internal exception details.
- **FR-009**: Protected structured logs MUST retain the complete correlated failure detail needed by an operator.
- **FR-010**: Workspace iframe and document content MUST use same-origin relative locations and retain appropriate sandbox restrictions.
- **FR-011**: The static application file handler MUST prove traversal, sibling-prefix, and symbolic-link containment through focused tests and clear containment behavior.
- **FR-012**: Every production alert in scope (#3, #4, #5, #7, #8, #10, #12, #24, #25, #27, #28, and #29) MUST be fixed without scanner suppression, exclusion, or weakened analysis.
- **FR-013**: Alert #2 MUST be classified as used in tests only after confirming the synthetic hostname is fully mocked and produces no real request.
- **FR-014**: Alert #13 MAY be classified as a false positive only if focused evidence proves the canonical containment behavior safe and a clearer behavior-preserving implementation does not resolve the finding.
- **FR-015**: Focused regressions MUST cover the primary vulnerability and important bypass forms for every alert in scope.
- **FR-016**: The final change MUST exclude Hermes source changes, MCP-specific changes, unrelated refactors, dependency upgrades, CodeQL workflow-version changes, new product features, scanner-configuration weakening, and changes to main.
- **FR-017**: The feature MUST pass the complete development merge gate, all pull-request and final-dev workflows, CodeQL disposition checks, and the production-readiness gate before it is considered complete.
- **FR-018**: The verified feature MUST be merged only into dev, after which local dev MUST be clean, synchronized, and ready for a separately authorized production merge.

### Key Entities

- **Network Target Policy**: The rules and evaluated address evidence that determine whether an intentional local health-check target and each redirect destination may be contacted.
- **Contained Path**: A canonical filesystem target paired with its authorized root and the evidence that the target remains inside that root.
- **Registered Workspace**: A workspace already known to Wright, including its canonical location and whether it is inside the managed workspace root.
- **Safe Client Error**: A generic user-facing message and trace identifier correlated with complete protected diagnostic detail.
- **Alert Disposition**: The branch, alert number, classification, evidence, and resulting scanner state for each of the 14 findings.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: All 12 production alert instances in scope are absent from final-dev security scan results without suppression or reduced scan coverage.
- **SC-002**: The two disposition-specific findings have precise evidence-backed outcomes: #2 as test-only and #13 as fixed, or as false positive only if the safe-code criteria are met.
- **SC-003**: 100% of focused security regression cases pass, including every required bypass category listed in this specification.
- **SC-004**: Legitimate local Hermes and local inference health checks continue to succeed in representative loopback tests while 100% of prohibited network target cases are rejected.
- **SC-005**: No tested client-facing error contains a path, credential, command output, internal endpoint, raw exception, or stack detail; every tested failure contains a usable trace identifier.
- **SC-006**: The complete development merge gate and production-readiness gate pass on the final dev commit, and every GitHub workflow for the pull request and final dev commit completes successfully.
- **SC-007**: The final dev worktree is clean, exactly synchronized with the remote dev branch, and contains no change outside the defined security scope.

## Assumptions

- The current GitHub CodeQL alert list and alert numbers supplied in the goal are the authoritative scope baseline.
- Loopback health checks are an intentional Wright capability; access to metadata and link-local services is not.
- Existing Wright authentication and authorization remain in force and are not replaced by this change.
- Existing structured logging and trace propagation are the required diagnostic channels.
- Symbolic-link regression cases may be skipped only on hosts that cannot create them, with the specific host limitation recorded and equivalent supported-platform coverage retained.
- Existing instances on main may remain visible until a later, separately authorized dev-to-main merge.
- The operator's explicit end-to-end goal authorizes the specification, planning, task, analysis, implementation, feature-to-dev merge, and verification phases while expressly withholding authorization to modify main.
