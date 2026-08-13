# Implementation Plan: Capability Library and MCP Onboarding

**Branch**: `068-capability-library` | **Date**: 2026-08-12 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `specs/068-capability-library/spec.md`

## Summary

Turn the existing Engineering Tool Registry into a global Capability Library backed by a complete offline catalog and a deliberate, signed update lifecycle. Keep catalog metadata separate from user-owned install, process, credential, and workspace state. Add a safe configuration-import parser, current-machine observations, immutable install preflights, structured validation evidence, and a guided in-product onboarding journey. Extend the current `tool_registry` domain package and SQLite lifecycle rather than creating a second registry. Preserve the existing MCP service and workspace boundaries, and use injectable deterministic installer/probe adapters for normal tests.

The Gate A choice is a pinned Ed25519 trust root with canonical signed metadata, monotonic sequence and expiry checks, content digest verification, SQLite transactions for candidate/active/previous state, and an explicit administrator preview/activation/rollback workflow. It is intentionally narrower than a multi-role TUF repository but covers this feature's one-publisher channel without a new background service. The trust root is configurable, private signing material never ships in Wright, and an absent configured channel leaves the bundled catalog fully functional.

## Technical Context

**Language/Version**: Python 3.11-3.14 for domain/API code; TypeScript 5 and React 19 for the web application

**Primary Dependencies**: Pydantic 2, FastAPI, SQLite, JSON Schema, PyYAML, MCP SDK, `cryptography` Ed25519 verification, existing Wright secret/workspace/tool-registry services, React/Vitest/Playwright

**Storage**: Existing embedded SQLite database in WAL mode for immutable snapshot envelopes, active/previous pointers, update previews, install-plan records, validation evidence, and missing-capability reports; package resources for the recovery/bundled catalog; existing secret store for credential values

**Testing**: pytest unit/contract/integration tests; schema fixtures; deterministic fake local, remote, and host-bridge adapters; Vitest component/service tests; mocked and live-local Playwright journeys; package-content and migration tests; `scripts/check-dev-merge.sh`

**Target Platform**: Native Windows x64, Linux x64, Linux ARM64/GB10, macOS x64/ARM64 where current Wright runtime support exists; Docker Linux x64/ARM64; browser UI

**Project Type**: Modular monorepo desktop/local web application with provider-neutral MCP domain package, thin FastAPI routes, React frontend, and shared native/Docker distribution

**Performance Goals**: Search/filter 1,000 catalog records in under 250 ms on a reference local machine; parse a 100-server import in under 1 second; read the active snapshot without network access; machine preflight finishes in under 3 seconds when it performs only local detection; update activation completes as one bounded transaction

**Constraints**: Offline-first; no catalog-triggered installation or enablement; no raw secrets outside the secret boundary; no unreviewed command execution during import/preflight; no paid account, license acceptance, proprietary host install, GPU, or hardware in normal gates; no MCP-specific host software added to base images; physical actuation excluded

**Scale/Scope**: Current 69-entry catalog plus the official-preview Onshape Labs record, designed and tested for at least 1,000 records, 100 imported definitions, 10 retained snapshots, and concurrent local readers with one serialized catalog writer

## Constitution Check

*GATE: Passed before Phase 0 research and re-checked after Phase 1 design.*

| Principle | Pre-design and post-design evaluation |
|-----------|----------------------------------------|
| Modular monorepo / thin routes | PASS: signature, import, compatibility, snapshot, plan, and reconciliation logic stays in `packages/tool_registry`; API routes only validate/translate and call `McpApiService`. |
| Offline-first | PASS: package-resource catalog remains the immutable recovery root; update and remote validation failures never remove discovery. |
| Native and Docker distribution | PASS: new Python resources/dependency enter the shared wheel/runtime and are covered by package tests; no source checkout or frontend build is required at runtime. |
| Thick base / thin code | PASS: deterministic adapters and clean-container recipes do not add vendor MCP software to the base image. |
| Manager neutrality | PASS: onboarding targets Wright's provider-neutral MCP registry and gateway, not Hermes- or Codex-owned configuration. |
| Embedded state | PASS: lifecycle records use existing SQLite WAL storage; no database server is introduced. |
| Local authentication / RBAC | PASS: global update and install mutations use the API's existing authenticated administrator boundary; workspace enablement preserves existing workspace authority. No external identity provider is added. |
| Engineering tool isolation | PASS: parser and preflight never execute; install backends are explicit and capability-scoped. Host applications are detected, never installed by this feature. |
| UI atomic design / 3-tier tests | PASS: reusable badges, filters, detail panels, wizard steps, and reports use tokens and stable test IDs, with component, mocked journey, and live-local coverage. |
| Observability and traceability | PASS: update, plan, apply, validate, rollback, and enable decisions receive trace IDs and structured redacted events. |
| Phase isolation and manual gates | PASS WITH RECORDED ADVANCE APPROVAL: the attached program goal explicitly authorizes safest reversible clarification and Gates A-D decisions plus analysis remediation. The Gate A decision is documented in `contracts/gate-a-decision.md`; implementation remains within that approved scope. |
| Branch discipline | PASS: work is isolated on `068-capability-library`; no direct work occurs on `main`. |

No constitution violation requires a complexity exception.

## Project Structure

### Documentation (this feature)

```text
specs/068-capability-library/
|-- spec.md
|-- plan.md
|-- research.md
|-- data-model.md
|-- quickstart.md
|-- contracts/
|   |-- capability-library-api.md
|   |-- catalog-snapshot.schema.json
|   |-- import-preview.schema.json
|   |-- install-plan.schema.json
|   |-- ui-journey.md
|   `-- gate-a-decision.md
|-- checklists/
|   |-- requirements.md
|   `-- capability-library.md
`-- tasks.md
```

### Source Code (repository root)

```text
packages/tool_registry/src/tool_registry/
|-- canonical_catalog.py          # bundled validation and canonical serialization
|-- catalog_models.py             # evidence and catalog record contracts
|-- catalog_signing.py            # envelope canonicalization and Ed25519 verification
|-- catalog_snapshots.py          # candidate/active/previous lifecycle and diff
|-- catalog_reconcile.py          # metadata projection preserving user state
|-- capability_views.py           # catalog plus current user-state projection
|-- config_import.py              # no-execution common-client grammar
|-- compatibility.py              # read-only machine observations
|-- install_plans.py              # immutable exact preflight and approval digest
|-- onboarding.py                 # adapter lifecycle orchestration
|-- validation_evidence.py        # validation state transitions and persistence
`-- catalog/
    |-- engineering-catalog.yaml  # offline recovery snapshot, including Onshape Labs
    |-- schema.json
    `-- trust-root.json            # public verification metadata only

packages/data_vault/src/data_vault/migrations.py
packages/tool_registry/tests/
apps/api/src/api/services/mcp_services.py
apps/api/src/api/routers/mcp.py
apps/api/tests/

apps/web/src/
|-- components/pages/ToolRegistryPage.tsx
|-- components/tools/CapabilityCard.tsx
|-- components/tools/CapabilityDetails.tsx
|-- components/tools/CapabilityFilters.tsx
|-- components/tools/OnboardingWizard.tsx
|-- components/tools/CatalogUpdatePanel.tsx
|-- components/tools/MissingCapabilityForm.tsx
|-- services/mcp-service.ts
|-- store/tools.tsx
`-- **/*.spec.tsx

tests/ui-integration/
|-- capability-library.spec.ts
`-- mcp-onboarding.spec.ts

tests/packaging/
docs/engineering-capability-program-progress.md
docs/mcp-catalog/
```

**Structure Decision**: Extend the existing tool-registry package, migration ledger, thin MCP API, and current registry page. Snapshot and onboarding behavior belong to the domain package; SQLite definitions remain owned by `data_vault`; UI-only state remains in React. This avoids a parallel catalog service and keeps gateway consumers on the same canonical identity and credential boundaries.

## Phase 0 Research Decisions

The completed decisions and primary sources are in [research.md](research.md). The important implementation consequences are:

1. Wright consumes upstream discovery sources into a reviewed publisher pipeline; end-user clients consume Wright snapshots and do not depend directly on the preview MCP Registry.
2. The first update channel uses a single Wright-pinned Ed25519 signing role, strict canonical JSON, expiry and monotonic sequence enforcement, and SHA-256 content binding. Root rotation and delegated publishers remain a later compatible extension.
3. Import supports Claude-style `mcpServers`, VS Code-style `servers` plus `inputs`, and a plain single-server JSON object. Parsing is data-only and never expands a shell.
4. Remote HTTP/SSE, local stdio/package, and host-bridge flows share one Install Plan and adapter lifecycle; no generic command string is executed directly from a catalog update.
5. The Onshape Labs FeatureScript endpoint is vendor-authoritative official preview evidence, but normal validation records `not_live_validated` because subscription/license and credentials are unavailable.

## Phase 1 Design

### Catalog lifecycle

- On first use, validate and register the bundled recovery snapshot without replacing any user record.
- An update arrives only from an administrator-configured channel or an explicitly uploaded envelope. Download bytes are size/time bounded and never interpreted as executable configuration.
- Verify the envelope signature against the pinned public key, then verify expiry, sequence, payload digest, schema, canonical identities, aliases, and evidence invariants.
- Persist a candidate and a stable diff. Activation uses `BEGIN IMMEDIATE` to set `previous_snapshot_id`, set the active snapshot, reconcile metadata, and write an audit record in one transaction.
- Rollback performs the same transaction in reverse. The package-resource snapshot is always available as last-resort recovery.
- Retain the active, previous, and at least eight inactive verified snapshots; never prune a referenced or recovery snapshot.

### Capability projection and UI

- A new capability view merges active immutable catalog metadata with current-machine observations and existing user-owned server/install/credential/workspace state. The catalog never becomes the owner of those values.
- The top-level page is named **Capability Library**. It presents discovery first, then details/preflight. Workspace enablement remains a separate action and Rivet execution is not added here.
- Filters are URL-stable and keyboard operable. Empty, loading, offline, update-available, blocked, failed, and stale states have explicit copy and stable test IDs.
- The current ToolCard remains available during migration but its data is supplied by the capability view; destructive browser prompts are removed.

### Guided onboarding

- Import produces only normalized drafts and credential requirements. It does not store raw pasted input after preview, resolve environment variables, contact endpoints, or execute commands.
- Preflight captures a machine observation and emits an immutable digest-bound Install Plan. Unknown compatibility is visible and blocks apply unless a policy-approved manual path exists.
- Applying a plan requires the same snapshot revision and machine-observation digest. Local package, remote connection, and host bridge adapters implement prepare/apply/validate/rollback/remove and return structured effects.
- Deterministic adapters prove success, blocked, changed-plan, rollback, and cleanup behavior. Optional live tests use explicit environment gates.

### Validation and workspace handoff

- ValidationEvidence records initialize, initialized notification, tools/list, and an optional read-only probe. Partial evidence never becomes `passed`.
- Workspace enablement consumes a passed/current validation record and creates or updates only the existing workspace capability grant. It does not approve a tool call.
- Raw credential values are accepted only by the current secret endpoint and never enter plan or evidence objects.

## Post-Design Constitution Re-check

PASS. Contracts retain package boundaries, offline behavior, SQLite ownership, the secret boundary, RBAC, traceability, three-tier UI testing, deterministic normal gates, and no physical actuation. The only new direct dependency is the audited signature primitive already present transitively in the API runtime; it becomes explicit in `wright-tool-registry` so standalone package behavior is honest. No external service becomes a core dependency.

## Gate and Verification Strategy

1. Contract/schema unit tests for signing, freshness, canonical encoding, malformed inputs, import grammar, plan digests, state transitions, and redaction.
2. Migration/reconciliation integration tests proving exact preservation of custom entries and user-owned state across activate/restart/rollback.
3. Deterministic local package, local HTTP endpoint, and fake host-bridge onboarding tests through service and API boundaries.
4. Component and service tests for every new UI state; mocked Playwright journeys for discovery, update preview/rollback, import/preflight, reporting, and workspace enablement.
5. Local live browser smoke against the installed/backend path, with no network vendor dependency.
6. Package-resource, wheel/sdist, docs, catalog bundle verifiers, and clean-container policy checks.
7. Full `scripts/check-dev-merge.sh` against the exact tree after integrating current `origin/dev`.

## Rollback

- Runtime catalog rollback: administrator activates `previous_snapshot_id`; if state is unreadable, Wright falls back to the bundled recovery snapshot and exposes a diagnostic rather than modifying user state.
- Database migration rollback: no destructive transformation is performed. New tables/columns are additive and older code ignores them; a pre-migration backup remains governed by the existing database lifecycle.
- UI rollback: legacy server list endpoints and stored rows remain compatible while the Capability Library consumes the new projection.
- Feature rollback: revert the feature merge; bundled catalog and existing registry/install state continue to work because no existing columns or secret formats are removed.

## Complexity Tracking

No constitutional exceptions are required.
