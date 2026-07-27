# Feature Specification: Secrets, Container, and Provider Configuration

**Feature Branch**: `codex/043-secrets-container-and-provider-config`

**Created**: 2026-07-10

**Status**: Approved for implementation by the roadmap continuation

**Input**: Close SEC-03, SEC-04, and CTR-01 without weakening Wright's local-first and air-gapped operation.

## User Scenarios & Testing

### User Story 1 - Configure Providers Without Secret Disclosure (Priority: P1)

As a local Wright administrator, I can configure API, Git, MCP, and integration credentials while all read surfaces report only whether a credential is configured, never its value.

**Why this priority**: Plaintext credentials in responses, state, process arguments, or logs are a release-blocking compromise path.

**Independent Test**: Configure representative credentials, exercise settings, Git, MCP, logs, and diagnostics, and prove the original values never appear outside the protected credential provider while legitimate operations still receive them.

**Acceptance Scenarios**:

1. **Given** a configured provider credential, **When** an authenticated administrator reads settings, **Then** the response reports configuration status without returning the credential.
2. **Given** a Git credential containing reserved URL characters, **When** Wright performs a remote operation, **Then** authentication succeeds without placing the credential in the remote URL or process arguments.
3. **Given** protocol messages and subprocess errors containing credential-shaped data, **When** Wright records or returns diagnostics, **Then** sensitive values are redacted.

---

### User Story 2 - Upgrade Existing Secrets Safely (Priority: P1)

As an existing operator, I can upgrade from plaintext Wright settings without losing credentials, serving against a partial migration, or being unable to restore the previous state.

**Why this priority**: A security migration that loses credentials or silently leaves plaintext behind is not deployable.

**Independent Test**: Start from representative legacy settings, run the upgrade, verify protected storage and plaintext removal, simulate an interrupted migration, and restore from the generated backup.

**Acceptance Scenarios**:

1. **Given** legacy plaintext credentials, **When** upgrade runs, **Then** a recoverable backup is created before values move to protected storage and plaintext sources are cleared only after verification.
2. **Given** migration failure, **When** Wright starts, **Then** affected credential-dependent operations fail closed with recovery guidance rather than using incompatible or partial state.
3. **Given** a completed migration, **When** rollback is required, **Then** an operator can restore the documented backup without exposing values in normal command output.

---

### User Story 3 - Run a Least-Privilege Appliance (Priority: P1)

As an appliance operator, I can run Wright without universal default credentials, passwordless privilege escalation, unnecessary capabilities, or persistence of operating-system directories.

**Why this priority**: Container compromise must not automatically become root access or persist across image replacement.

**Independent Test**: Inspect and start the production appliance, prove it runs as a non-root identity with restricted privileges and documented data-only persistence, then restart or upgrade it and verify required Wright state survives.

**Acceptance Scenarios**:

1. **Given** a fresh appliance configuration, **When** it starts, **Then** required credentials are generated or explicitly supplied and no shared default key is accepted.
2. **Given** a running appliance, **When** its process identity and privileges are inspected, **Then** it has no passwordless escalation path or unnecessary elevated capability.
3. **Given** an appliance replacement, **When** documented data volumes are reattached, **Then** Wright data survives while system software and configuration come from the new image.

---

### User Story 4 - Update Configuration Without Destroying Other Providers (Priority: P2)

As an operator using multiple model or agent providers, I can change one provider's configuration without replacing unrelated entries or comments owned by other tools.

**Why this priority**: Security hardening must not make local multi-provider configuration destructive.

**Independent Test**: Begin with configuration containing Wright-owned and unknown entries, update one Wright setting, and verify all unrelated content remains semantically unchanged.

**Acceptance Scenarios**:

1. **Given** existing unknown provider entries, **When** Wright changes one owned setting, **Then** unknown entries remain present and usable.
2. **Given** an interrupted configuration write, **When** the operation fails, **Then** the previous complete configuration remains available.

### Edge Cases

- Concurrent writers updating different credentials must not lose either update or produce invalid storage.
- A missing, corrupt, unreadable, or permission-insecure fallback store must fail safely with actionable diagnostics.
- Empty values must mean explicit removal only when the request clearly identifies the credential being removed.
- Secret values containing whitespace, Unicode, shell metacharacters, URL delimiters, or newlines must not alter command execution or redaction.
- Redaction must cover structured fields, nested payloads, exception text, stdout, stderr, and protocol messages without hiding non-sensitive operational context.
- Read-only or ephemeral container filesystems must produce a clear configuration error rather than silently weakening permissions.

## Requirements

### Functional Requirements

- **FR-001**: Wright MUST expose one provider-neutral credential boundary for API, Git, MCP, agent, and integration credentials.
- **FR-002**: Credential reads through HTTP, logs, diagnostics, and configuration status MUST return only masked status metadata and MUST NOT return stored values.
- **FR-003**: The protected provider MUST support local air-gapped operation and a documented mounted-secret or owner-only fallback when an operating-system credential facility is unavailable.
- **FR-004**: Fallback credential updates MUST be atomic, durable, permission-restricted, and safe under concurrent readers and writers.
- **FR-005**: Existing plaintext credentials MUST migrate through a backup-first, verify-before-delete process with explicit failure and rollback behavior.
- **FR-006**: Wright MUST NOT place credentials in Git remote URLs, command arguments, process listings, exception messages, or audit records.
- **FR-007**: Logs and protocol diagnostics MUST redact credential values and credential-shaped fields by default before persistence or API return.
- **FR-008**: Configuration writers MUST preserve unknown and unrelated provider entries and MUST replace files atomically.
- **FR-009**: The appliance MUST run application processes as a non-root identity without passwordless privilege escalation or unnecessary elevated capabilities.
- **FR-010**: Production configuration MUST NOT contain a universal default API key, password, token, or signing secret.
- **FR-011**: Production persistence MUST be limited to documented Wright data and secret/configuration mounts; operating-system directories MUST come from the image on each deployment.
- **FR-012**: A one-release legacy deployment path MAY retain old volume layout only when clearly labeled insecure/migration-only and accompanied by an upgrade and rollback procedure.
- **FR-013**: Startup and readiness MUST fail closed when required secrets cannot be loaded, migrated, or validated.
- **FR-014**: Security and leak-scanning tests MUST cover API responses, state stores, process arguments, logs, configuration output, container definitions, and concurrent fallback-store access.

### Key Entities

- **Credential Reference**: A provider-neutral identifier and configuration status for a secret without its value.
- **Credential Provider**: The protected boundary that stores, retrieves, removes, and verifies credential values.
- **Migration Backup**: A restricted, recoverable snapshot created before plaintext credential removal.
- **Provider Configuration**: Wright-owned settings merged into a larger configuration while preserving unrelated content.
- **Appliance Data Set**: The documented files and directories that legitimately persist across image replacement.

## Success Criteria

### Measurable Outcomes

- **SC-001**: Automated leak scans find zero configured credential values across API responses, databases, process arguments, logs, diagnostics, and generated configuration.
- **SC-002**: At least 100 concurrent fallback-store updates complete without lost writes, corrupt data, or permission widening.
- **SC-003**: Every supported legacy plaintext source upgrades and restores successfully in automated migration scenarios, including one simulated interruption.
- **SC-004**: A fresh production appliance starts with no shared default secret and all application processes run without root or passwordless escalation.
- **SC-005**: Appliance replacement retains 100% of documented Wright user data while persisting none of the prohibited operating-system directories.
- **SC-006**: Updating any one supported provider preserves all unknown configuration entries in representative compatibility fixtures.

## Assumptions

- Wright remains a single-user, local-first appliance; remote multi-user identity is outside this feature.
- Feature 042 authentication remains the authority protecting administrative HTTP surfaces.
- Numbered database schema migration infrastructure belongs to Feature 044; Feature 043 may provide an idempotent credential migration seam invoked by current startup only when it fails closed and is compatible with later migration ownership.
- Provider-specific cloud APIs remain optional; credential storage and migration must work without network access.
- Actual registry publication, secret rotation in external services, and stable release promotion remain out of scope.
