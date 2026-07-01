# Wright Architecture Refactoring Audit

Date: 2026-07-01

This report captures a repository-wide architectural review focused on
maintainability, constitution compliance, extensibility, clean interfaces,
documentation quality, formatting consistency, and testability.

## Confirmed Direction

- `hermes-plugin-wright` remains a first-class package.
- Use **Wright gateway** as the agent-neutral gateway term.
- OpenClaw will use the same MCP gateway protocol as Hermes.
- Engineering MCP validation should run locally in clean containers.
- Package-manager install/update flows do not need extra approval gates, but
  must still respect catalog safety defaults, blocked/non-working metadata, and
  offline-first failure behavior.
- Do not tune architecture specifically to Hermes. Hermes is one agent
  implementation among future engines.

## Executive Summary

- Wright has the right intended shape, but several core seams are still
  Hermes-shaped rather than agent-neutral.
- API routes are not consistently thin; `agent.py`, `mcp.py`, `workspace.py`,
  and `main.py` contain business logic, persistence, external proxying, and
  orchestration.
- MCP catalog metadata is strong, but validation is mostly metadata
  classification, not the documented clean-container protocol loop.
- The catalog currently has two competing sources: a large Python seed in
  migrations and `hermes-plugin-wright/catalog.yaml`.
- UI tests exist, but the frontend architecture leans heavily on large
  inline-styled components and duplicated client-side domain constants.
- `data_vault` is effectively a placeholder while SQLite/file/log behavior
  lives in API/core modules, weakening package ownership.
- System E2E coverage is missing: `tests/e2e` only contains `.gitkeep`, despite
  the constitution requiring smoke tests.
- The next architectural seam should be the Wright gateway contract: Hermes and
  OpenClaw should consume the same gateway protocol through adapter/profile
  implementations.

## Top Refactoring Opportunities

### 1. Introduce An Agent Runtime Registry

Problem:
The API boots Hermes directly and treats Hermes as the default agent.

Evidence:

- `apps/api/src/api/main.py:14` imports `HermesAdapter`.
- `apps/api/src/api/main.py:119` instantiates `HermesAdapter` in global app
  state.
- `apps/api/src/api/config.py:3` imports Hermes config resolution directly.
- `apps/api/src/api/routers/setup.py:105` hardcodes supported agents as
  `["hermes", "openclaw", "pi"]`.
- `packages/core/src/core/agent_sync.py:53` branches on `self._active_agent`.

Why it matters:
OpenClaw will inherit Hermes assumptions unless the engine lifecycle, config,
health, and sync hooks become explicit.

Recommended refactor:
Add an `AgentEngineRegistry` in `packages/agent_adapters` with provider
metadata, config resolution, health capability flags, adapter factories, and a
gateway profile hook. API boot should ask the registry for the active engine
instead of importing `HermesAdapter`.

Constitution principle affected:
Agent Abstraction; Modular Monorepo Boundaries.

Risk/effort estimate:
High impact, medium effort.

Suggested tests or verification:

- Registry unit tests for Hermes and OpenClaw stub selection.
- API tests proving `/api/agent/active` switches engines without API-level
  Hermes imports.
- Contract tests ensuring unknown agents fail with a typed error.

### 2. Extract API Route Business Logic Into Services

Problem:
Route modules perform workspace creation, SQLite writes, MCP installation,
credential handling, validation writes, Git commands, and Python execution.

Evidence:

- `apps/api/src/api/routers/agent.py:178` creates sessions and workspaces.
- `apps/api/src/api/routers/agent.py:212` writes workspace/session mapping to
  SQLite.
- `apps/api/src/api/routers/mcp.py:259` handles MCP install orchestration.
- `apps/api/src/api/routers/mcp.py:338` performs validation classification and
  follow-up writes.
- `apps/api/src/api/routers/workspace.py:306` runs workspace Python files.
- `apps/api/src/api/routers/workspace.py:790` creates dashboard workspaces.

Why it matters:
Thin routes are a constitutional requirement and are the easiest seam for
adding future engines without rewriting HTTP handlers.

Recommended refactor:
Create service modules or package services:

- `AgentSessionService`
- `WorkspaceService`
- `McpCatalogService`
- `McpInstallService`
- `McpValidationService`
- `CredentialService`
- `GatewayService`

Routes should validate request/response, delegate to services, and translate
domain exceptions into HTTP responses.

Constitution principle affected:
Modular Monorepo Boundaries.

Risk/effort estimate:
High impact, medium-high effort.

Suggested tests or verification:

- Service unit tests with fake engines/registries.
- Route tests focused on HTTP status and response mapping.
- Regression tests for session creation, workspace activation, MCP install,
  and credential save/delete.

### 3. Make Wright Gateway Sync Agent-Neutral

Problem:
Gateway sync lives in Hermes-specific APIs and files, with stub behavior for
other agents.

Evidence:

- `apps/api/src/api/services/hermes_sync.py:1` is explicitly Hermes-specific.
- `apps/api/src/api/services/hermes_sync.py:91` syncs MCP server state to
  Hermes.
- `packages/core/src/core/agent_sync.py:64` contains original Hermes config
  syncing logic.
- `packages/core/src/core/agent_sync.py:173` writes stub configs for other
  agents.
- `packages/core/src/core/workspace.py:1281` writes `.hermes.md` workspace
  files.

Why it matters:
OpenClaw should plug into the same Wright gateway protocol, not a `.hermes.md`
and `~/.hermes/config.yaml` workflow. Hermes can remain first-class without
making Hermes the architecture boundary.

Recommended refactor:
Define gateway-facing contracts in `packages/agent_adapters`, for example:

- `WrightGatewayProfile`
- `WrightGatewaySyncAdapter`
- `WorkspaceContextWriter`

Hermes implements these contracts in `hermes-plugin-wright` or a Hermes adapter
module. OpenClaw later implements the same gateway protocol. Keep
`hermes-plugin-wright` first-class, but move shared Wright gateway contract
types out of the Hermes package.

Constitution principle affected:
Agent Abstraction; Engineering Tooling Protocol.

Risk/effort estimate:
High impact, medium effort.

Suggested tests or verification:

- Contract tests with fake gateway sync adapters.
- Hermes implementation tests for config file writes.
- OpenClaw stub tests proving no Hermes paths are touched.

### 4. Unify MCP Catalog Source Of Truth

Problem:
`apps/api` has a 3,000+ line migration file containing catalog seed data, while
`hermes-plugin-wright/catalog.yaml` also carries catalog metadata.

Evidence:

- `apps/api/src/api/database/migrate.py:24` defines `ENGINEERING_CATALOG`.
- `apps/api/src/api/database/migrate.py:2855` seeds the engineering catalog.
- `hermes-plugin-wright/catalog.yaml:3` starts a separate YAML catalog.
- `hermes-plugin-wright/catalog.py:15` implements a separate `CatalogLoader`.
- `hermes-plugin-wright/schemas.py:76` defines `CatalogEntry`.

Why it matters:
Divergent catalog schemas will cause validation, UI, and plugin behavior to
drift.

Recommended refactor:
Keep `hermes-plugin-wright` first-class, but make the canonical catalog loader,
normalizer, and schema live in `packages/tool_registry`. The Hermes plugin
should consume those shared models or export its YAML through the shared
normalizer. Keep migrations schema-focused, not catalog-data-heavy.

Constitution principle affected:
Modular Monorepo Boundaries; Documentation Quality.

Risk/effort estimate:
High impact, medium effort.

Suggested tests or verification:

- Golden catalog normalization tests.
- Migration seed tests that load from canonical catalog fixtures.
- Hermes plugin catalog tests that assert parity with `tool_registry` models.

### 5. Implement Real Clean-Container MCP Validation

Problem:
`classify_server()` checks blocked flags and local host binaries, but does not
install per MCP, run `initialize`, `notifications/initialized`, `tools/list`,
safe backend probe, Wright gateway proxy probe, or reset container state.

Evidence:

- `packages/tool_registry/src/tool_registry/mcp_validation.py:54` checks host
  dependencies with `shutil.which`.
- `packages/tool_registry/src/tool_registry/mcp_validation.py:72` classifies
  metadata.
- `packages/tool_registry/src/tool_registry/mcp_validation.py:116` returns
  `skipped` when no automated probe is defined.
- `docs/mcp-catalog/mcp-server-testing-process.md:21` defines the required
  clean-container validation loop.

Why it matters:
`tested` status can become ambiguous without reproducible clean-container
evidence. Local clean-container validation is now an explicit direction.

Recommended refactor:
Add a local validation runner package with:

- `ValidationPlan`
- `ValidationProbe`
- `ValidationEvidence`
- `CleanContainerExecutor`
- `WrightGatewayProbe`

Keep metadata classification as a fast preflight, not final validation. The
runner should install only the selected MCP dependencies, run MCP protocol
probes, run one safe backend-touching call when possible, verify Wright gateway
proxying when applicable, and write evidence/follow-up records.

Constitution principle affected:
Container Strategy; Offline-First Mandate; Engineering Tooling Protocol.

Risk/effort estimate:
High impact, high effort.

Suggested tests or verification:

- Unit tests for validation plan generation.
- Integration test using a mock MCP server in Docker.
- Follow-up record snapshot tests.
- Local CLI smoke test that validates one known lightweight MCP candidate.

### 6. Split Broad UI Components And Move Domain Logic Out Of Views

Problem:
`ToolCard.tsx` is 1,700+ lines and owns credentials, install/update flows,
workspace toggles, metadata labels, inline styling, and rendering.
`ToolRegistryPage.tsx` duplicates tier/category sorting.

Evidence:

- `apps/web/src/components/tools/ToolCard.tsx:26` defines the large component.
- `apps/web/src/components/tools/ToolCard.tsx:106` owns verification display
  metadata.
- `apps/web/src/components/tools/ToolCard.tsx:217` handles credential
  persistence.
- `apps/web/src/components/pages/ToolRegistryPage.tsx:25` duplicates tier
  ordering.
- `apps/web/src/components/pages/ToolRegistryPage.tsx:95` performs filtering
  and category decisions in the page.

Why it matters:
The MCP UI will become harder to extend as install states, validation states,
and safety metadata grow.

Recommended refactor:
Extract focused components and a shared display model:

- `ToolCardHeader`
- `ToolMetadataBadges`
- `CredentialPanel`
- `InstallControls`
- `WorkspaceToolPanel`
- `mcpDisplayModel`

Move status labels, sort order, and derived metadata into pure functions with
unit tests.

Constitution principle affected:
UI Component Layers; Testability.

Risk/effort estimate:
Medium impact, medium effort.

Suggested tests or verification:

- Component tests per extracted panel.
- Pure function tests for sorting/filtering/status display.
- Playwright layout tests for long metadata, blocked entries, missing
  credentials, and high-risk entries.

### 7. Move Storage Ownership Into `data_vault`

Problem:
`data_vault` declares SQLite/LanceDB/filesystem ownership but only has an
empty package initializer. SQLite, logs, and file vault behavior live in
API/core.

Evidence:

- `packages/data_vault/src/data_vault/__init__.py:1` documents intended storage
  scope.
- `apps/api/src/api/config.py:21` reads SQLite settings directly.
- `packages/core/src/core/workspace.py:42` creates SQLite connections directly.
- `packages/core/src/core/workspace.py:1368` reads application logs from
  `apps/api/wright.log`.

Why it matters:
Storage logic is scattered, making offline behavior, migrations, tracing, and
backup strategy harder to reason about.

Recommended refactor:
Put SQLite connection/session helpers, vault filesystem APIs, log readers, and
eventual LanceDB clients into `data_vault`. Keep `core` domain-focused.

Constitution principle affected:
Data Storage & RAG; Modular Monorepo Boundaries.

Risk/effort estimate:
Medium impact, medium effort.

Suggested tests or verification:

- SQLite WAL and foreign-key tests.
- Vault path sanitization tests.
- Log-reader tests with temp files.
- Import-boundary tests proving API routes do not own storage implementation.

### 8. Close Observability And Test Gaps

Problem:
Some packages still use stdlib logging, `print()`, string-formatted logs, and
direct SQLite calls without traced DB spans. E2E smoke tests are absent.

Evidence:

- `packages/core/src/core/logging.py:4` states JSON logging is required.
- `packages/core/src/core/agent_sync.py:4` imports stdlib `logging`.
- `packages/tool_registry/src/tool_registry/manager.py:2` imports stdlib
  `logging`.
- `apps/api/src/api/database/migrate.py:2746` prints migration status.
- `packages/core/src/core/tracing.py:80` provides traced DB helpers, but many
  DB calls bypass them.
- `tests/e2e/.gitkeep:1` is the only E2E file.

Why it matters:
The constitution requires JSON logging, trace propagation, mandatory spans, and
system smoke tests.

Recommended refactor:
Standardize on `core.logging.get_logger`, replace direct DB calls with traced
repositories/helpers, and add minimal E2E coverage for API health, agent
fallback, and MCP list.

Constitution principle affected:
Observability & Tracing; 3-Tier Testing.

Risk/effort estimate:
Medium impact, low-medium effort.

Suggested tests or verification:

- Tests asserting logs are JSON and include `trace_id`.
- E2E smoke for local FastAPI backend plus mocked agent/MCP paths.
- Trace tests for representative SQLite reads/writes and MCP tool execution.

## Do First

1. Add the agent registry and stop importing `HermesAdapter` from API boot code.
2. Extract MCP install/validation/follow-up logic from
   `apps/api/src/api/routers/mcp.py`.
3. Choose one canonical MCP catalog source and make `hermes-plugin-wright`
   consume the shared model while remaining first-class.
4. Define the Wright gateway adapter/profile contracts before OpenClaw work.
5. Add a minimal `tests/e2e` smoke suite.

## Avoid

- Do not make `.hermes.md`, `wrightgateway`, or Hermes config files the generic
  extension point for all agents.
- Do not mark MCPs `tested` from host-local dependency checks alone.
- Do not add FreeCAD, OpenSCAD, Blender, SolidWorks, vendor SDKs, license
  managers, or other MCP-specific host software to the base image just to make
  catalog validation green.
- Do not let API routes grow new direct SQLite, subprocess, package-manager, or
  file-vault behavior.
- Do not weaken offline-first behavior by making version checks, cloud CAD, or
  package registries required for core workflows.
- Do not add package-manager approval gates beyond catalog safety defaults and
  blocked/non-working install restrictions.

## Architectural Decisions Recorded

- Hermes plugin remains first-class.
- The generic gateway term is **Wright gateway**.
- OpenClaw will use the same MCP gateway protocol.
- Clean-container validation should run locally.
- Package-manager operations do not require additional approval gates.

## Open Questions

- Which package should own the concrete Wright gateway protocol schemas:
  `packages/agent_adapters`, `packages/tool_registry`, or a small new shared
  package?
- Should local clean-container validation produce Markdown evidence, structured
  JSON evidence, or both?
- Should the web UI read display metadata directly from the API, or should it
  continue to derive labels client-side from shared constants generated from
  backend schema?
