# Quickstart: Capability Library and MCP Onboarding

This document is the implementation and acceptance walkthrough for loop 068. All normal paths use deterministic fixtures and require no vendor credentials, subscriptions, proprietary applications, GPU, or hardware.

## 1. Validate the bundled catalog

1. Start from a fresh migrated database with networking disabled.
2. Bootstrap the package-resource catalog.
3. Open Capability Library.
4. Search CAD, filter by evidence and current-machine state, and open details for compatible, uncertain, blocked, and no-public-MCP records.

Expected:

- All bundled records are available offline.
- The active source is labeled bundled/recovery.
- Every non-compatible record has a reason and recovery or honest no-action explanation.
- No server process starts and no user-owned state changes.

## 2. Exercise signed update and rollback

1. Inject the test public key as the approved test channel.
2. Preview a fixture envelope whose next sequence adds a distinct official record.
3. Inspect signer, expiry, schema, identity changes, and field-level diff.
4. Activate with the exact preview digest.
5. Restart and verify the new active snapshot.
6. Roll back to the named previous snapshot.
7. Repeat with tampered, expired, replayed, lower-sequence, invalid-schema, duplicate-alias, and interrupted fixtures.

Expected:

- Valid activation and rollback are atomic.
- Invalid fixtures fail closed and leave the prior catalog readable.
- Custom rows, install state, explicit disablement, credential flags, and workspace grants remain byte-for-byte/logically unchanged.
- No update invokes an installer.

## 3. Confirm Onshape evidence

1. Find `onshape-labs-featurescript-mcp`.
2. Verify it is distinct from community Onshape entries.
3. Inspect vendor source, endpoint, official-preview status, account/subscription prerequisite, and no-live-validation limitation.

Expected:

- The record is discoverable and correctly classified.
- Install/connect remains disabled until the user meets external prerequisites and creates a current plan.
- The normal test never contacts Onshape or accepts an App Store license.

## 4. Import configurations safely

Preview fixtures for:

- Claude `mcpServers` with multiple stdio and remote servers.
- VS Code `servers` plus `inputs` and secret placeholders.
- Plain local and remote single-server objects.
- Invalid JSON, mixed valid/invalid records, duplicate names, unknown types, credential-bearing headers/environment values, shell metacharacters, and oversized input.

Expected:

- Detected formats and normalized drafts are stable.
- Values that may be secrets are redacted and converted to credential requirements.
- No raw source is persisted or logged.
- No command is executed, no variable is expanded, no endpoint is contacted, and no server is registered during preview.

## 5. Generate exact preflights

Create plans against deterministic fixtures:

1. Local package with available test runtime and reversible isolated target.
2. Local HTTP/SSE fixture endpoint.
3. Host bridge with fake application/add-on/handshake detectors.
4. Missing runtime, unsupported architecture, unavailable host, stale observation, and blocked catalog record.

Expected:

- Every plan identifies exact revision, machine observation, requirements, effects, validation, rollback, approvals, blockers, expiry, and digest.
- Preflight is read-only.
- Any material input change invalidates prior approval.

## 6. Apply, validate, and enable one workspace

1. Approve the deterministic local-package plan by digest.
2. Apply through the fake/local fixture adapter.
3. Observe ordered effects and cleanup metadata.
4. Validate initialize, initialized notification, tools/list, and a read-only health probe.
5. Supply a test credential only through the isolated test secret provider when required.
6. Enable the resulting capability for workspace A.

Expected:

- Workspace A can discover the capability; workspace B cannot.
- Validation evidence contains schema/result digests and no secrets.
- Workspace enablement does not authorize an invocation.
- Injected failure rolls back reversible effects and reports any residue.

## 7. Verify the user journey

Component tests cover every required state. Mocked Playwright covers offline discovery, signed update/rollback, import, each preflight backend, validation, workspace selection, and structured missing reporting. The live-local browser smoke uses the actual FastAPI service plus deterministic child fixtures.

Required accessibility checks:

- keyboard-only add journey
- focus trap/restore
- live-region progress and alerts
- non-color status text
- no serious or critical automated violations

## 8. Focused verification commands

Run the repository's standard package tools for:

- Ruff check and format check over changed Python
- tool-registry and data-vault migration tests
- MCP API tests
- web unit tests and TypeScript checks
- focused Playwright capability-library/onboarding tests
- all MCP bundle verifiers
- package-resource and wheel/sdist tests
- strict docs build

Finally fetch current `origin/dev`, integrate it, and run `scripts/check-dev-merge.sh` against the exact feature tree. Merge only when the worktree is clean and the merged `dev` tree hash matches the validated feature tree hash.

## Optional external validation

Live Onshape validation is a separately authorized follow-up:

1. The user independently accepts the Onshape Labs/App Store terms and provides a permitted account.
2. Credentials/tokens are stored through Wright's secret boundary.
3. An opt-in test connects to the published endpoint, records MCP initialize and tools/list evidence, performs only a vendor-documented read-only probe, and records exact limitations.

Absence of this external authority does not fail normal gates and must never be represented as a successful live validation.
