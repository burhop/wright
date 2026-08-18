# Feature Specification: Windows MCP Qualification

**Feature Branch**: `codex/074-windows-mcp-qualification`

**Created**: 2026-08-13

**Status**: Approved for implementation by the durable Windows qualification goal

**Input**: Qualify only the seven explicitly approved engineering MCP servers on
native Windows, produce honest evidence for every qualification stage, and make
the process safely repeatable without installing or executing any other MCP.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Safely qualify an approved server (Priority: P1)

As a Wright maintainer, I can select an explicitly approved MCP server, review
its pinned source and safety findings, and run a bounded native Windows
qualification that never proceeds past a failed safety gate.

**Why this priority**: Real package execution is the highest-risk part of the
program. The allowlist and safety preflight must fail closed before any install,
launch, connection, or executable download occurs.

**Independent Test**: A local fixture qualification proves that an allowlisted
recipe advances stage by stage while a non-allowlisted identifier is rejected
before any executor or network seam is invoked.

**Acceptance Scenarios**:

1. **Given** an identifier outside the seven-entry allowlist, **When** a
   qualification is requested, **Then** Wright refuses it before any install,
   download, launch, connection, or subprocess action.
2. **Given** an allowlisted server with a completed safety preflight, **When**
   the operator starts qualification, **Then** each source, install, startup,
   protocol, safe-probe, Wright onboarding, gateway, and cleanup stage receives
   its own factual result and evidence.
3. **Given** an unresolved material safety concern, **When** the preflight is
   evaluated, **Then** the server is classified `safety_blocked`, no executable
   content is installed or run, evidence is saved, and processing continues to
   the next allowlisted server.

---

### User Story 2 - Understand what works on this computer (Priority: P2)

As an engineer browsing Wright's MCP Server Library, I can distinguish whether
an MCP package installs on Windows, whether the server starts and speaks MCP,
whether its commercial host or credentials are available, whether Wright can
register it, and whether its tools are exposed through the workspace gateway.

**Why this priority**: A single compatibility badge incorrectly conflates the
server package, host application, remote account, and Wright integration.

**Independent Test**: Fixture evidence for a server whose package works but
whose host is absent renders an installation pass and a separate host-required
boundary, without the words `incompatible` or a false backend pass.

**Acceptance Scenarios**:

1. **Given** current Windows evidence, **When** an engineer views a server,
   **Then** the interface shows the validation date and separate concise stage
   results for package/registration, MCP startup, MCP protocol, host/backend,
   Wright setup, gateway, and cleanup.
2. **Given** a desktop bridge whose commercial host is absent, **When** its MCP
   package and protocol start successfully, **Then** Wright shows those stages
   as passed and the backend as `partial` with a host-required reason.
3. **Given** a remote MCP endpoint, **When** its evidence is displayed, **Then**
   Wright describes registration or connection rather than local installation.
4. **Given** evidence invalidated by a source revision, package, tool schema,
   machine, or credential-binding change, **When** it is displayed, **Then** it
   is visibly stale and cannot support a current Windows claim.

---

### User Story 3 - Reproduce and audit qualification (Priority: P3)

As a Wright maintainer, I can rerun a structured recipe in an isolated Windows
workspace and obtain bounded, redacted, machine-readable and readable evidence
that records exactly what was attempted and cleaned up.

**Why this priority**: Current catalog notes cannot reliably prove installation,
protocol behavior, safety boundaries, gateway behavior, or residue cleanup.

**Independent Test**: Fake local recipes exercise timeouts, output ceilings,
redaction, process-tree cleanup, residue detection, digest capture, and stage
serialization without network access or installation of a real MCP.

**Acceptance Scenarios**:

1. **Given** a fixture recipe, **When** qualification completes, **Then** it
   emits one structured evidence record, one readable report, and an updated
   consolidated matrix using the required result vocabulary.
2. **Given** a hung or noisy subprocess, **When** its bound is exceeded, **Then**
   the process tree is terminated, captured material is bounded and redacted,
   cleanup is attempted, and the affected stage is factual rather than passed.
3. **Given** all seven allowlisted results, **When** the audit list is reviewed,
   **Then** it proves that no non-allowlisted MCP was installed, launched,
   connected, or executed.

---

### User Story 4 - Finish an unattended qualification run (Priority: P4)

As the program operator, I can let Wright work through the seven approved
servers in the specified order, saving a checkpoint and cleaning temporary
state after each server instead of blocking on unavailable credentials,
subscriptions, commercial hosts, or external services.

**Why this priority**: Honest partial and blocked results are useful; an
unattended run must not stall or invent success when an external prerequisite
is unavailable.

**Independent Test**: A fixture sequence with passed, partial, failed,
safety-blocked, obsolete, remote, and not-tested outcomes completes in order and
writes a terminal classification for every server.

**Acceptance Scenarios**:

1. **Given** the ordered allowlist, **When** one server needs credentials or a
   commercial host, **Then** Wright records the boundary, cleans up, checkpoints
   the matrix and progress log, and continues automatically.
2. **Given** the end of the run, **When** completion is evaluated, **Then** every
   allowlisted server has current Windows evidence and an honest terminal
   classification, or the run remains incomplete.

### Edge Cases

- A canonical repository is renamed, archived, deleted, transferred, or no
  longer matches its claimed publisher.
- A package name resolves to a different publisher or revision than the recipe.
- An installer attempts global state, administrator elevation, lifecycle hooks,
  service creation, startup registration, or an undocumented network contact.
- A server emits logs on protocol stdout, malformed messages, unusable tool
  schemas, required internal context fields, oversized output, or fails shutdown.
- A server starts cleanly but reports a missing CAD host, add-in, session,
  credential, subscription, or license.
- A remote endpoint has no separate local package and cannot be contacted
  without authentication.
- Wright onboarding succeeds but the workspace gateway does not expose the
  expected namespaced tools, or exposes tools after disablement.
- Cleanup finds residual processes, files, registrations, or state outside the
  isolated Wright-owned test roots.
- A previous evidence record is structurally valid but no longer binds to the
  current source, package, schema, machine, or credential context.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The qualification system MUST hard-code and expose exactly the
  seven approved catalog IDs and MUST fail closed before any side effect for all
  other identifiers.
- **FR-002**: The approved processing order MUST be `brep-mcp`,
  `solid-edge-mcp-burhop`, `aps-mcp-server-nodejs`,
  `autodesk-product-help-mcp`, `autodesk-fusion-desktop-mcp`,
  `autodesk-fusion-data-mcp`, then `onshape-labs-featurescript-mcp`.
- **FR-003**: Every server MUST receive a source and safety preflight covering
  publisher, canonical source, immutable revision or package version, license,
  Windows method, launch method, documented network destinations, credentials,
  host requirements, maintenance status, install hooks, dependencies,
  subprocesses, filesystem access, exposed tools, and material risks.
- **FR-004**: An unresolved material safety concern MUST produce
  `safety_blocked` evidence without installing, downloading executable content,
  launching, connecting, or executing the server.
- **FR-005**: Qualification MUST isolate package and generated state beneath
  Wright-owned temporary roots, avoid administrator/global/system changes, use
  bounded subprocesses, and never require changes to Windows security controls.
- **FR-006**: Recipes MUST be structured data with pinned source identities,
  explicit operations, transports, safe probes, allowed network destinations,
  timeouts, byte ceilings, expected residue, and cleanup instructions; arbitrary
  operator-supplied shell strings MUST NOT become qualification authority.
- **FR-007**: Evidence MUST independently record `source_current`,
  `windows_install_passed`, `mcp_started`, `protocol_passed`,
  `safe_probe_passed`, `wright_install_passed`, `wright_gateway_passed`, and
  `cleanup_passed`.
- **FR-008**: Each stage MUST use only `passed`, `partial`, `failed`,
  `safety_blocked`, `obsolete_or_unavailable`, `not_applicable`, or
  `not_tested`, with a stable reason and recovery guidance when not passed.
- **FR-009**: Protocol evidence MUST record initialization, initialized
  notification, tool listing, server identity, negotiated protocol version,
  tool count, tool-schema digest, transport faults, stdout contamination,
  shutdown result, and applicable timing.
- **FR-010**: Safe probes MUST be documented, bounded, and non-destructive
  outside their disposable workspace. They MUST be read-only except that
  `brep-mcp` MAY run one exact pinned and reviewed deterministic geometry program
  whose only writes are bounded artifacts inside the disposable qualification
  root. Real engineering documents, destructive tools, physical control,
  manufacturing actions, uploads, publishing, operator-supplied or unbounded
  code, and undocumented endpoints MUST never be invoked.
- **FR-011**: A missing commercial host, add-in, live session, credential,
  subscription, or license MUST remain separate from package and protocol
  results and MUST NOT by itself classify an installable MCP as incompatible.
- **FR-012**: Remote registrations MUST be distinguished from local package
  installation and MAY mark local installation `not_applicable`.
- **FR-013**: Wright onboarding evidence MUST use the real onboarding boundary,
  distinguish preview from confirmed state, and confirm installation does not
  incorrectly require a commercial host to be running.
- **FR-014**: Gateway evidence MUST prove discovery through Wright's managed
  MCP runner and workspace gateway, with expected prefixed tools and at most one
  approved safe read-only proxy call when prerequisites permit.
- **FR-015**: Cleanup MUST stop process trees, remove isolated test state where
  practical, verify Wright registry consistency, detect unexpected residue, and
  prove unrelated MCPs, applications, files, and settings were untouched.
- **FR-016**: Persisted evidence MUST redact credentials, environment values,
  sensitive commands and arguments, private paths, and subprocess content while
  retaining bounded digests, counts, timings, classifications, and recovery.
- **FR-017**: Each server MUST produce a structured evidence file and readable
  report, and the run MUST produce a consolidated Windows matrix, progress log,
  installed-items ledger, cleanup ledger, and explicit non-allowlist proof.
- **FR-018**: Catalog claims and the MCP Server Library projection MUST be
  derived only from current saved evidence and MUST show separate source,
  package/registration, MCP startup, protocol, host/backend, Wright setup,
  gateway, and cleanup states plus date.
- **FR-019**: Evidence MUST become stale when its pinned source, package,
  tool-schema digest, machine fingerprint, or credential binding no longer
  matches, and stale evidence MUST not support a current works-on-Windows claim.
- **FR-020**: Offline regression tests MUST use fake or local fixtures, exercise
  the allowlist and safety boundary, and MUST never install or execute a real
  non-allowlisted MCP.
- **FR-021**: The run MUST checkpoint and continue after each server when a
  credential, subscription, administrator right, commercial host installation,
  unsafe behavior, or unavailable external service prevents further progress.
- **FR-022**: Wright MUST say “Installs on Windows with no problems” only when
  installation, startup, protocol discovery, Wright registration, clean
  shutdown, and cleanup passed without unexpected side effects; backend and
  gateway validation MUST remain separate claims.

### Key Entities

- **Qualification Allowlist**: The immutable ordered set of seven approved
  catalog identities authorized for executable qualification.
- **Windows Qualification Recipe**: Pinned publisher/source and constrained
  stage operations, bounds, expected prerequisites, safe probe, and cleanup.
- **Safety Preflight**: Reviewed source facts, behaviors, risks, boundaries, and
  the install-or-refuse decision for one pinned recipe.
- **Stage Evidence**: One factual result for one qualification stage with
  identity bindings, timings, bounded observations, reason, and recovery.
- **Server Qualification Evidence**: The aggregate identity, safety, stages,
  residue, installed-items, and cleanup record for one server and machine.
- **Qualification Run**: Ordered checkpoints for all seven servers plus proof
  that no other MCP received an executable action.
- **Windows Qualification Projection**: The concise current/stale stage view
  presented in the MCP Server Library without exposing sensitive evidence.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 100% of non-allowlisted fixture requests are rejected before the
  first network, installer, subprocess, connection, or registration seam.
- **SC-002**: All seven approved servers have a dated Windows evidence pair and
  terminal classification, and the consolidated matrix accounts for all eight
  stages without blank or ambiguous compatibility cells.
- **SC-003**: 100% of qualification artifacts pass automated secret, private
  path, command-argument, and unbounded-output redaction checks.
- **SC-004**: Hung fixture processes are stopped and their process trees cleaned
  within 10 seconds of the configured timeout, with no residue outside the
  declared isolated roots.
- **SC-005**: An engineer can determine source, package/registration, MCP
  startup, protocol, host/backend, Wright setup, gateway, and cleanup status plus
  evidence age for any qualified server from one detail view in under 30 seconds.
- **SC-006**: Fixture evidence invalidated by any one source, package, schema,
  machine, or credential-binding change is shown as stale in every tested case.
- **SC-007**: The final installed-items and execution ledger contains only the
  seven allowlisted identifiers and explicitly records zero non-allowlisted MCP
  installations or executions.
- **SC-008**: Focused offline regression coverage and the authoritative
  development merge gate pass, or a genuine host-only limitation is recorded
  with its exact failing command and unaffected scope.

## Assumptions

- This Windows x86_64 host is authoritative only for evidence produced on this
  machine; Linux, macOS, and container results remain separate.
- Credentials, paid subscriptions, license acceptances, administrator access,
  and commercial host installation are unavailable and are honest boundaries,
  not failures of the harness.
- Existing commercial hosts may be detected read-only, but the run will not
  install, upgrade, configure, or mutate them or their real documents.
- Canonical publisher evidence may require read-only internet research; package
  downloads and execution remain restricted to the allowlist after safety
  approval.
- The user's durable goal is explicit approval to advance through the complete
  Spec Kit sequence and the ordered, bounded qualification loop without
  optional phase pauses; no merge, push, pull request, or release is authorized.
