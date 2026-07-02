# Wright Architecture Refactoring Phase 2

Date: 2026-07-01

Related documents:

- [Refactoring Audit 2026-07-01](refactoring-audit-2026-07-01.md)
- Spec 038 Phase 2 Plan: `specs/038-refactoring-phase-2/plan.md`
- Engineering MCP Catalog Plan: `specs/034-engineering-mcp-catalog/plan.md`
- [MCP Server Testing Process](../mcp-catalog/mcp-server-testing-process.md)

## Purpose

Phase 1 established the first architectural seams: agent runtime registry,
Wright gateway contracts, MCP service extraction, catalog normalization,
validation plan/evidence models, and offline smoke coverage.

Phase 2 hardens those seams into stable ownership boundaries. The goal is not a
large rewrite. The goal is to make OpenClaw and future engines additive, keep
API routes thin, make MCP catalog and validation behavior reproducible, and
remove the remaining Hermes-shaped assumptions from generic Wright code.

## Implemented Phase 2 Slice

The first Phase 2 implementation adds `packages/workspace_service` as the
workspace lifecycle facade for priority API paths: create, activate, config
update, workspace tool assignment, file execution, and context refresh. API
routes keep their response shapes while delegating business behavior to the
package facade.

Agent context materialization is now an `agent_adapters` contract. Hermes
materializes `.hermes.md` through `agent_adapters.hermes_gateway`; OpenClaw is a
selectable stub provider that does not write Hermes files. Legacy generic route
and core activation paths no longer write `.hermes.md` directly.

`tool_registry` owns MCP catalog seed data, MCP safety policy decisions for
install, start, and call boundaries, plus opt-in validation CLI seams that write
redacted JSON evidence and Markdown summaries. Clean-container validation
remains operator-invoked and must not be claimed as passed unless the documented
container workflow actually runs.

Frontend domain contracts are generated into
`apps/web/src/types/generated/wright-contracts.ts` and checked by
`scripts/generate-frontend-contracts.py --check`. The largest frontend hotspots
also received targeted decomposition: workspace enablement moved out of
`ToolCard`, and the workspace activity bar moved out of `WorkspacePanel`.

Observability updates clarify that OpenTelemetry owns `trace_id` and `span_id`,
while Wright owns `wright.correlation_id` and the `X-Trace-Id` response header.
Remote telemetry export remains disabled unless explicitly opted in.

The completion pass moved the large catalog seed out of API migrations into
`packages/tool_registry/src/tool_registry/engineering_catalog.py`, added a
`data_vault` SQLite state-store seam used by migrations and workspace service,
and strengthened `DockerCleanContainerExecutor` so an operator-invoked run
launches a clean container and records direct stdio MCP probe evidence. Evidence
is marked `partial` unless Wright gateway proxy probes are also executed and
recorded.

## Non-Negotiable Direction

- Hermes remains first-class and remains the default working adapter.
- Hermes is not the generic architecture boundary.
- OpenClaw and future engines must plug into agent-neutral contracts.
- API routes remain HTTP translation layers and delegate business behavior.
- Offline-first behavior remains the default for local development and tests.
- Clean-container MCP validation must not depend on MCP-specific host software
  in the base Docker image.
- Catalog entries that are uncertain, blocked, partial, or follow-up-required
  must be preserved rather than hidden.
- Package-manager install/update flows do not need a separate approval prompt
  just because an installer is involved. Safety approvals are driven by catalog
  risk, credentials, network access, and tool capability.
- Logging, tracing, and telemetry are part of the safety architecture, not
  cleanup. Phase 2 work is incomplete until important workspace, agent, MCP,
  validation, and catalog flows are observable, locally auditable, and redacted.
- Telemetry remains local-first by default. Remote export requires explicit
  operator opt-in.

## Resolved Architectural Decisions

### 1. Workspace Lifecycle Ownership

Decision:
Create a dedicated `packages/workspace_service` package for workspace lifecycle
orchestration.

Rationale:
`packages/core` has grown into a mixed package containing domain helpers,
workspace orchestration, storage calls, logging, tracing, subprocess execution,
and agent-specific context writing. That makes API extraction harder and keeps
agent behavior tangled with workspace behavior.

Target ownership:

- `packages/workspace_service` owns workspace creation, activation, file
  execution policy, git workflow orchestration, workspace tool assignment, and
  workspace context refresh orchestration.
- `packages/data_vault` owns SQLite connections, migrations-facing storage
  helpers, vault filesystem access, local audit records, and future LanceDB
  clients.
- `packages/agent_adapters` owns agent runtime selection, gateway profiles,
  adapter-specific context materialization, and agent health/session contracts.
- `packages/tool_registry` owns MCP catalog, safety policy, install/start/call
  policy, credential metadata, validation plans, and validation evidence.
- `packages/core` keeps cross-cutting primitives such as logging, tracing,
  typed errors, shared value objects, and small pure helpers.
- `apps/api` wires dependencies and translates HTTP requests/responses only.

Dependency rule:

```text
apps/api -> workspace_service -> data_vault
                           \-> agent_adapters
                           \-> tool_registry
                           \-> core

apps/api -> agent_adapters
apps/api -> tool_registry
apps/api -> data_vault

packages/* must not import apps/api
```

Phase 2 should not move every function at once. Start by introducing
`workspace_service` as an application facade, then migrate route behavior behind
that facade operation by operation.

### 2. Safety Approval Scope

Decision:
Use two local approval scopes:

- Global machine approval for installing or updating a server whose catalog
  metadata requires approval due to high/safety-critical risk, credential use,
  remote network access, proprietary dependencies, or machine-control
  capability.
- Workspace approval for enabling, starting, or calling a risky server inside a
  specific workspace.

Rationale:
Install state is local-machine state, but tool use risk is usually workspace
specific. A user may approve a server's installation once while still wanting
per-workspace control over whether that server can operate on a given project.

Rules:

- `blocked` and `non_working` servers cannot be installed unless a future
  explicit developer override mode is added.
- High-risk and safety-critical servers require recorded local approval before
  install/start/call when catalog metadata says approval is required.
- Missing required credentials block start/call.
- Remote network servers require explicit catalog metadata and workspace
  enablement.
- Package-manager use alone does not create an extra approval gate.
- Approval records are local, auditable, and offline.

### 3. Clean-Container Validation Entry Point

Decision:
Expose clean-container validation primarily through a local CLI entry point,
with API support limited to reading evidence, listing validation plans, and
optionally requesting a queued local validation job later.

Rationale:
Docker execution, package installation, network probes, and proprietary tool
checks are operator activities. Running them directly from a web route would
make safety, credentials, cancellation, and logs harder to control.

Target entry point:

```text
wright mcp validate <server-id> --container ubuntu-x64 --evidence-dir docs/mcp-catalog/evidence
```

Initial implementation may live behind a Python module command before a formal
CLI wrapper exists:

```text
uv run python -m tool_registry.validation_cli validate <server-id>
```

Validation evidence:

- Structured JSON is canonical for automation.
- Markdown summaries are generated for human review and follow-up records.
- Evidence must record environment, install commands, protocol probes,
  credentials redaction, safe backend probe result, gateway proxy result when
  applicable, and follow-up recommendations.

### 4. UI Contract Strategy

Decision:
Generate TypeScript contract types from backend/package JSON Schema for MCP
catalog, MCP server state, validation evidence summaries, agent runtime
metadata, and workspace service responses.

Rationale:
Hand-written TypeScript interfaces already duplicate backend defaults. Contract
generation prevents drift as catalog metadata, risk policy, and agent providers
evolve.

Rules:

- Generated TypeScript contracts are checked into the repo for offline-first
  builds.
- CI verifies generated files are current.
- UI display constants may remain hand-authored only when they are visual
  presentation metadata, not domain truth.
- During migration, add parity tests before deleting hand-written interfaces.

### 5. Hermes Compatibility Window

Decision:
Keep Hermes compatibility files, including `.hermes.md` and Hermes config
materialization, through Phase 2 and the current alpha cycle. These files must
be generated only by the Hermes adapter/profile implementation, never by generic
workspace or API code.

Rationale:
Existing workspaces and the first-class Hermes plugin need continuity, but
future agents should not inherit Hermes file names, directory layout, or config
shape.

Target context model:

- Canonical Wright workspace context lives in local storage managed by
  `data_vault` and `workspace_service`.
- Agent adapters materialize provider-specific files from that canonical
  context.
- Hermes materializes `.hermes.md` and `~/.hermes/...` config.
- OpenClaw materializes its own files later through the same adapter interface.

Compatibility removal:
Do not set a removal date yet. Revisit after one non-Hermes adapter can create,
activate, receive gateway tool sync, and run smoke tests without Hermes files.

### 6. Catalog Source Of Truth

Decision:
Move the canonical engineering MCP catalog into `packages/tool_registry` as
packaged data, with shared Pydantic models and normalizers. The Hermes plugin
must consume or export that shared catalog rather than maintaining an
independent schema/source of truth.

Rationale:
Catalog state is used by the API, UI, validation tools, docs, and Hermes plugin.
The registry package is the natural owner because it owns installability,
validation, credentials, safety metadata, and runtime state.

Rules:

- API migrations may call registry seed helpers, but must not contain large
  catalog data blocks.
- User-local mutable fields, such as install state, credentials, enabled tools,
  validation history, and local notes, must not be overwritten by catalog seed
  refreshes.
- `docs/mcp-catalog/followups` remains the human-readable follow-up record
  location.
- Catalog YAML/JSON format must be documented and validated.

### 7. Evidence Format

Decision:
Use both JSON and Markdown, with JSON canonical.

Rationale:
Automation needs structured evidence. Maintainers need readable summaries and
follow-up notes.

Required JSON fields:

- `server_id`
- `catalog_version`
- `validation_started_at`
- `validation_finished_at`
- `environment`
- `container_image`
- `install_steps`
- `protocol_probes`
- `safe_backend_probe`
- `gateway_proxy_probe`
- `credential_requirements`
- `network_requirements`
- `result`
- `diagnostics`
- `follow_up_required`
- `redactions`

### 8. Observability And Telemetry Contract

Decision:
Treat observability as a phase 2 release gate. Define a local-first telemetry
contract that separates correlation IDs from OpenTelemetry trace IDs, requires
redaction before emission, and gives every major workflow a stable event/span
name.

Rationale:
Wright runs local agents, starts MCP servers, executes tools, and validates
engineering integrations. Missing, inconsistent, or over-sharing telemetry is a
safety problem, not only a debugging inconvenience. The current implementation
has useful pieces, but the documented end-to-end model is stronger than the
actual guarantees.

Trace identity:

- OpenTelemetry owns `trace_id` and `span_id`.
- `X-Trace-Id` becomes a Wright correlation ID unless the system later adopts
  full W3C trace-context propagation.
- Logs include both `trace_id` and `wright.correlation_id` when available.
- API responses continue returning `X-Trace-Id` for user-visible support and
  UI correlation.

Local-first telemetry:

- Default exports are local only: stdout JSON logs, local rotating log file,
  local Jaeger or equivalent OTel collector when configured, and browser-local
  logs.
- No cloud telemetry, vendor collector, or remote support upload is enabled by
  default.
- Remote export requires explicit operator configuration and must preserve the
  same redaction rules.

Required workflow spans:

- `workspace.create`
- `workspace.activate`
- `workspace.config.update`
- `workspace.file.execute`
- `agent.runtime.select`
- `agent.context.materialize`
- `agent.chat.start`
- `agent.chat.stream`
- `mcp.catalog.seed_refresh`
- `mcp.server.install`
- `mcp.server.start`
- `mcp.server.stop`
- `mcp.tool.call`
- `mcp.safety.evaluate`
- `mcp.validation.plan`
- `mcp.validation.run`
- `mcp.validation.evidence.write`

Required event fields where applicable:

- `wright.correlation_id`
- `wright.workspace_id`
- `wright.session_id`
- `wright.agent_id`
- `wright.provider_id`
- `wright.server_id`
- `wright.tool_name`
- `wright.validation_id`
- `wright.catalog_version`
- `wright.policy_decision`
- `wright.support_level`
- `duration_ms`
- `error_code`

Forbidden or redacted fields:

- Raw credential values.
- Full environment maps.
- Unredacted command lines that may include tokens or paths to private data.
- Full tool arguments when they may contain file contents, proprietary geometry,
  customer data, or secrets.
- Full subprocess stdout/stderr by default.
- Full validation evidence payloads before redaction.

Redaction rule:
Every telemetry path that emits command, environment, subprocess, validation,
credential, or tool-argument data must pass through a shared redaction helper
before logging, span attributes, evidence writing, or UI display.

## Phase 2 Workstreams

### Workstream A: Workspace Service Boundary

Problem:
Workspace lifecycle behavior is split across API routes and `packages/core`,
with direct filesystem, SQLite, subprocess, git, and Hermes-context operations.

Target:
Create `packages/workspace_service` and route workspace operations through it.

Initial service surface:

- `create_workspace(request) -> WorkspaceRecord`
- `activate_workspace(workspace_id, agent_id | None) -> WorkspaceActivation`
- `update_workspace_config(workspace_id, patch) -> WorkspaceConfig`
- `list_workspace_tools(workspace_id) -> WorkspaceToolState`
- `set_workspace_tool_enabled(workspace_id, server_id, enabled) -> WorkspaceToolState`
- `execute_workspace_file(workspace_id, path, policy) -> FileExecutionResult`
- `refresh_agent_context(workspace_id, agent_id) -> ContextRefreshResult`

Refactor order:

1. Wrap existing behavior behind service methods without changing responses.
2. Move direct route logic into service methods.
3. Replace API imports from `core.workspace` with service facade calls.
4. Move storage-specific code into `data_vault`.
5. Move agent context materialization calls into `agent_adapters`.

Acceptance gates:

- API route tests still pass without response-shape changes.
- No `packages/*` module imports `apps/api`.
- Workspace creation no longer calls `write_workspace_hermes_md` from API code.
- A fake non-Hermes adapter can activate a workspace without Hermes paths.

### Workstream B: Agent Runtime And Context Materialization

Problem:
Hermes paths and context files still appear in generic config, workspace, sync,
and UI paths.

Target:
Finish the provider boundary so each agent owns its runtime config and context
materialization.

Required contracts:

- `AgentRuntimeProvider`
- `AgentRuntimeRegistry`
- `AgentGatewayProfile`
- `AgentContextMaterializer`
- `AgentHealthProbe`
- `AgentSessionGateway`

Provider responsibilities:

- Resolve local/remote API settings.
- Create engine adapter instances.
- Describe gateway server profile.
- Materialize provider-specific context/config files.
- Report support level: `supported`, `experimental`, `stub`, or `unavailable`.

Acceptance gates:

- API boot does not import Hermes-specific classes directly.
- `HERMES_*` config names are not used by generic API code.
- `core` and `workspace_service` call adapter contracts, not Hermes helpers.
- OpenClaw stub tests prove provider selection and workspace activation do not
  touch `.hermes.md` or `~/.hermes`.

### Workstream C: MCP Catalog, Safety, And Install Policy

Problem:
Catalog metadata, install policy, and UI display policy are split across API
migrations, registry services, plugin schemas, and frontend constants.

Target:
Make `tool_registry` the policy owner for catalog data, installability, safety,
and validation state.

Package responsibilities:

- Load canonical catalog packaged data.
- Normalize platform support and dependency metadata.
- Preserve partial/failed/follow-up-required entries.
- Decide install/start/call eligibility.
- Record local approvals and audit events.
- Export JSON Schema for API/UI/plugin contracts.

Safety policy:

```text
can_install(server, approval_context) -> PolicyDecision
can_start(server, workspace, approval_context) -> PolicyDecision
can_call_tool(server, tool, workspace, approval_context) -> PolicyDecision
```

Decision fields:

- `allowed`
- `reason`
- `required_approvals`
- `missing_credentials`
- `network_required`
- `blocked_by_catalog`
- `diagnostics`

Acceptance gates:

- Blocked/non-working install attempts fail in `tool_registry`, not only in UI.
- High/safety-critical servers requiring approval cannot start without a local
  approval record.
- Missing credentials block start/call with a typed error.
- API migration seeding uses `tool_registry` helpers.
- Hermes plugin catalog loading validates against shared registry models.

### Workstream D: Clean-Container Validation

Problem:
Validation plans and evidence models exist, but clean-container execution is
not yet a first-class operator workflow.

Target:
Implement an opt-in validation runner that follows the documented clean-container
process.

Components:

- `ValidationPlanBuilder`
- `ValidationExecutor` protocol
- `MockValidationExecutor`
- `DockerCleanContainerExecutor`
- `ValidationEvidenceWriter`
- `FollowUpRecordWriter`
- `ValidationCli`

Execution rules:

- Start from a clean Ubuntu/Linux x64 container per server validation.
- Install only dependencies required by the selected MCP candidate.
- Do not add MCP-specific software to the base image to make tests pass.
- Run MCP protocol probes: `initialize`, `notifications/initialized`,
  `tools/list`.
- Run one safe backend-touching probe when credentials/software are available.
- Run Wright gateway proxy probe when the server is expected to be proxied.
- Mark host-dependent/proprietary entries as follow-up-required with clear
  diagnostics when they cannot be validated locally.

Acceptance gates:

- Default package/API tests do not require Docker, network, credentials, or
  proprietary software.
- Mock executor can generate complete evidence fixtures.
- Docker executor is behind an explicit CLI flag or command.
- Evidence writer redacts credentials and environment secrets.
- Validation results never silently overwrite catalog truth without preserving
  diagnostics.

### Workstream E: API Service Layer Completion

Problem:
Some API routes still perform domain work directly.

Target:
Keep route modules as request/response translators and move operations into
package or service-layer code.

Priority routes:

1. `apps/api/src/api/routers/workspace.py`
2. `apps/api/src/api/routers/agent.py`
3. `apps/api/src/api/routers/vault.py`
4. Remaining MCP endpoints not already delegated

Route rules:

- Parse request.
- Call a service.
- Translate typed domain errors to HTTP errors.
- Return response model.
- No direct subprocess execution.
- No direct SQLite writes.
- No direct provider-specific file writes.
- No direct package-manager execution.

Acceptance gates:

- Route tests cover HTTP status and response shape.
- Service tests cover business behavior.
- Import-boundary test prevents `packages/* -> apps/api`.
- Thin-route review checklist added to contributing docs.

### Workstream F: UI Architecture And Contracts

Problem:
Large React components mix data loading, domain decisions, style details, and
view rendering. UI types duplicate backend/package models.

Target:
Introduce generated contracts and split high-risk UI surfaces into data hooks,
display models, and focused presentational components.

Priority components:

- `WorkspacePanel`
- `ToolCard`
- `ToolRegistryPage`
- `AddToolModal`
- `CreateWorkspaceModal`
- `FileEditor`
- `FileTree`

Refactor pattern:

```text
services/api client -> store/query hook -> display model -> presentational component
```

Rules:

- Domain defaults come from API/package contracts, not duplicated frontend
  constants.
- Presentation labels and icons may remain frontend-owned.
- Interactive controls must have stable `data-testid` values.
- Shared controls use design tokens for color, spacing, radius, typography, and
  focus states.
- Browser `prompt`, `confirm`, and `alert` should be replaced with typed modal
  flows for important workflows.
- Direct `fetch` calls inside complex components should move to service modules.

Acceptance gates:

- Generated TypeScript contracts are current.
- Component tests cover risk badges, credential prompts, blocked installs,
  validation states, and workspace tool enablement.
- Playwright smoke covers tool registry install-blocked state and workspace
  activation.
- Visual/layout tests cover long metadata and mobile width.

### Workstream G: Observability And Error Model

Problem:
Structured logging and tracing exist but are not consistently used across API,
core, registry, validation, and runners. Current docs describe end-to-end
observability, but implementation still has stdlib loggers, `print()` calls,
possible trace/correlation ID confusion, unredacted command logging, and gaps in
database/tool/validation spans.

Target:
Use one structured logging, typed error, trace identity, telemetry taxonomy, and
redaction pattern across phase 2 seams. Observability is a release gate for
workspace service, MCP safety, clean-container validation, and agent adapter
materialization.

Rules:

- Use `core.logging.get_logger` or the agreed structlog wrapper in packages.
- Do not pass arbitrary keyword fields to stdlib loggers.
- Do not use `print` from library or migration code except explicit CLI output.
- Treat `trace_id` as the OpenTelemetry trace ID and
  `wright.correlation_id` as the user-visible/request correlation value.
- Preserve `X-Trace-Id` as the external correlation header until a full W3C
  trace-context decision is made.
- Redact command arguments, environment values, credentials, validation
  evidence, subprocess output, and tool arguments that may contain secrets or
  proprietary project data.
- Domain services raise typed errors; API translates them.
- Tool starts, tool calls, validation runs, workspace activation, and agent
  context refreshes emit traceable events.
- Remote telemetry export is disabled by default and requires explicit operator
  opt-in.
- Browser-side logs remain local by default and must use the same correlation
  ID when calling the API.

Required implementation tasks:

- Add a shared telemetry field-name module or documented constants for
  `wright.*` attributes.
- Add a shared redaction helper used by logging, tracing, validation evidence,
  and UI log display.
- Replace stdlib logging and `print()` in touched paths with structured events.
- Add span wrappers for workspace service operations, agent context
  materialization, MCP safety evaluation, MCP server start/stop, tool calls,
  catalog refresh, and validation evidence writing.
- Add typed error codes that are safe to log and safe to return through API
  errors.

Acceptance gates:

- Regression test for the current stdlib keyword-logging failure class.
- Log-shape tests assert JSON output with `trace_id`,
  `wright.correlation_id`, event name, level, timestamp, and component where
  request context exists.
- Trace-propagation tests prove API responses, server logs, and UI log records
  share the same correlation ID.
- Redaction tests cover command lines, env vars, validation evidence, tool
  arguments, subprocess stdout/stderr, and credential diagnostics.
- Representative workspace, MCP, agent context, catalog refresh, and validation
  flows emit required spans.
- Tests prove remote telemetry export is off by default.

### Workstream H: Documentation And Contributor Experience

Problem:
Some documentation still frames Wright around Hermes, and some package READMEs
do not describe current ownership boundaries.

Target:
Make docs teach the architecture Wright wants contributors to extend.

Docs to update:

- `README.md`
- `docs/architecture/agent-adapters.md`
- `docs/architecture/observability.md`
- `docs/architecture/tool-registry.md`
- `docs/architecture/system-overview.md`
- `apps/web/README.md`
- `hermes-plugin-wright/README.md`
- `docs/contributing/dev-setup.md`
- `docs/contributing/testing.md`

Rules:

- Hermes is described as default/first-class adapter, not the generic engine.
- OpenClaw is described as a future peer adapter using the same Wright gateway
  protocol.
- Package ownership and import boundaries are explicit.
- Observability docs distinguish OpenTelemetry trace IDs from Wright
  correlation IDs and document default-local telemetry behavior.
- MCP validation docs distinguish metadata preflight, mock validation, and
  clean-container validation.
- Docs must not contain local `file://` paths.

Acceptance gates:

- Docs link check passes.
- Search for stale Vite template text returns no app README hits.
- Search for local `file://` links returns no public docs hits.
- Architecture docs name canonical package owners.

## Implementation Sequence

### Phase 2.1: Boundary Guards And Contracts

Deliverables:

- Add import-boundary tests.
- Add JSON Schema export points for agent, MCP, validation, and workspace
  response models.
- Add generated TypeScript contract pipeline in check-only mode.
- Add typed error base classes for workspace, registry, validation, and agent
  domains if missing.
- Add telemetry event/span taxonomy constants and redaction helper interfaces
  before adding new instrumented flows.

Exit criteria:

- Boundary tests fail on `packages/* -> apps/api`.
- Contract generation/check command runs offline.
- Telemetry contract tests prove event names, required fields, and forbidden
  fields are enforced at the helper boundary.
- Existing tests pass.

### Phase 2.2: Workspace Service Facade

Deliverables:

- Add `packages/workspace_service`.
- Wrap current workspace creation, activation, tool enablement, config update,
  and file execution behind service methods.
- Move API route calls to the facade without response changes.
- Remove generic calls to Hermes context writing from route code.

Exit criteria:

- Workspace API tests pass.
- Workspace service unit tests cover happy path and typed errors.
- Fake non-Hermes context materializer test passes.
- Workspace create, activate, config update, and file execution emit spans with
  correlation ID, workspace ID when available, duration, and safe error codes.

### Phase 2.3: Agent Context And Gateway Materialization

Deliverables:

- Add `AgentContextMaterializer` and provider support-level metadata.
- Move Hermes `.hermes.md` and config writes behind Hermes provider code.
- Add OpenClaw stub materializer that writes no Hermes files.
- Update UI/service metadata to read provider labels and support level.

Exit criteria:

- No generic package or API route calls Hermes writer functions.
- Hermes smoke still materializes expected files.
- OpenClaw stub smoke proves generic activation path.
- Agent runtime selection and context materialization emit provider/support-level
  telemetry without logging provider secrets or full generated context content.

### Phase 2.4: Catalog Source And Safety Policy

Deliverables:

- Move canonical catalog data to `tool_registry`.
- Replace API migration catalog constants with registry seed helpers.
- Add `McpSafetyPolicy` and local approval/audit storage.
- Update API and UI to use policy decisions.
- Keep Hermes plugin first-class through shared loader/model validation.

Exit criteria:

- Catalog parity tests pass.
- Install/start/call safety tests pass.
- User-local install/credential/enabled state survives catalog refresh.
- UI displays policy decisions from API instead of re-deriving domain truth.
- Safety decisions and catalog refreshes emit structured local audit events with
  redacted diagnostics.

### Phase 2.5: Clean-Container Validation CLI

Deliverables:

- Add validation CLI/module entry point.
- Add mock executor and evidence fixture tests.
- Add Docker executor behind explicit operator invocation.
- Write JSON evidence and Markdown follow-up summaries.
- Add docs and examples for one lightweight MCP candidate.

Exit criteria:

- Fast tests remain offline and Docker-free.
- Mock validation evidence is complete and redacted.
- Clean-container validation can run manually for one lightweight server.
- Failed/proprietary/host-dependent entries produce follow-up records.
- Validation CLI logs and evidence use the shared correlation/redaction model,
  and no credentials, full env maps, or raw secret-bearing commands are emitted.

### Phase 2.6: UI Decomposition And Generated Contracts

Deliverables:

- Replace duplicated MCP and agent TypeScript interfaces with generated
  contracts.
- Split `ToolCard` and `WorkspacePanel` into hooks, display models, and
  presentational components.
- Replace prompts/alerts in priority workflows with modals.
- Add missing `data-testid` values to important controls.
- Move inline styles toward tokenized component styles.

Exit criteria:

- Vitest and Playwright smoke pass.
- Generated contract check passes.
- Tool registry and workspace panels remain layout-stable at mobile and desktop
  widths.
- UI API calls preserve `X-Trace-Id` correlation, and local UI logs can be
  matched to API logs by correlation ID.

### Phase 2.7: Observability And Docs

Deliverables:

- Replace remaining stdlib logging/print usage in touched paths.
- Implement the telemetry contract from resolved decision 8.
- Add redaction helpers for command/env/evidence/tool-argument/subprocess output.
- Add trace events around workspace activation, agent runtime selection, agent
  context materialization, MCP safety evaluation, MCP start/call, catalog
  refresh, validation planning, validation run, and evidence writing.
- Clarify `trace_id` versus `wright.correlation_id` in code, docs, and tests.
- Add default-off remote telemetry configuration checks.
- Refresh architecture and contributor docs.

Exit criteria:

- Log-shape, trace/correlation propagation, redaction, and remote-export-off
  tests pass.
- Docs link check passes.
- Architecture docs reflect package ownership and phase 2 decisions.

## Verification Matrix

Default local verification must remain offline:

```text
uv run pytest packages/agent_adapters packages/tool_registry packages/workspace_service apps/api/tests
npm run test --workspace=apps/web
npm run test:e2e --workspace=apps/web
```

Targeted verification by workstream:

- Agent registry: provider selection, unknown provider typed error, OpenClaw
  stub support-level behavior.
- Workspace service: create, activate, config update, tool enablement, file
  execution policy, typed errors.
- Catalog: schema validation, duplicate IDs, seed refresh merge policy,
  plugin parity.
- Safety: blocked install, high-risk approval, missing credentials, remote
  network metadata, call-time enforcement.
- Validation: plan generation, mock execution, evidence redaction, follow-up
  writing, optional Docker execution.
- UI: generated contract freshness, test IDs, credential flow, blocked install,
  validation display, mobile layout.
- Observability: JSON logs, OTel trace IDs, Wright correlation IDs, required
  span taxonomy, redacted command/env/tool/evidence fields, and default-off
  remote telemetry.

Manual or opt-in verification:

```text
uv run python -m tool_registry.validation_cli validate <server-id> --container ubuntu-x64
```

This command may use Docker, network, credentials, or external package
registries only when explicitly requested by the operator.

## Migration And Rollback

Migration strategy:

- Keep API response models stable.
- Add service facades before moving implementation details.
- Keep Hermes behavior green before introducing OpenClaw behavior.
- Run catalog seed in parity mode before deleting migration constants.
- Generate UI contracts alongside existing interfaces before switching imports.
- Keep Docker validation opt-in.
- Add telemetry helpers and tests before broad instrumentation, so later
  workstreams do not invent incompatible field names or ad hoc redaction.

Rollback strategy:

- Workspace service facade can delegate back to existing `core.workspace`
  functions until each operation is migrated.
- Hermes provider can keep existing config/context output while generic callers
  move to provider contracts.
- Catalog seeding can retain legacy migration constants behind a temporary
  fallback until packaged catalog parity is proven.
- Safety policy can start in report-only mode for non-blocked entries, then
  become enforcing after tests and UI flows are complete.
- Validation CLI can ship with mock executor first; Docker executor can remain
  experimental until evidence is reliable.
- If telemetry instrumentation creates noise or performance issues, keep the
  event names and redaction contract stable while reducing span detail behind
  local configuration. Do not remove correlation, safety, or audit events.

## Risks And Mitigations

Risk:
Moving workspace behavior into a new package may create circular dependencies.

Mitigation:
Add import-boundary tests first. Keep `workspace_service` dependent on
`agent_adapters`, `tool_registry`, `data_vault`, and `core`; never the reverse.

Risk:
Catalog migration may overwrite local state.

Mitigation:
Define a merge policy before migration. Add tests for install state,
credentials, workspace enabled tools, validation history, and local notes.

Risk:
Generated UI contracts may slow frontend iteration.

Mitigation:
Check generated files into the repository and add a simple freshness check.
Keep display-only metadata frontend-owned.

Risk:
Safety policy enforcement could break existing workflows.

Mitigation:
Introduce policy decisions in API responses first, update UI flows, then enforce
high-risk start/call gates. Continue blocking `blocked` and `non_working`
entries immediately.

Risk:
Clean-container validation could become network/proprietary-tool dependent.

Mitigation:
Keep default tests mock-only. Use explicit CLI flags for network, credentials,
and Docker. Record follow-up diagnostics instead of forcing green validation.

Risk:
Telemetry could leak secrets, proprietary project data, or command details while
trying to improve debuggability.

Mitigation:
Add redaction helpers and tests before broad instrumentation. Treat raw
credentials, full env maps, full command lines, raw tool arguments, subprocess
output, and unredacted evidence as forbidden telemetry fields.

Risk:
Trace IDs and user-visible request IDs could diverge and make logs harder to
join across UI, API, and local tools.

Mitigation:
Make the distinction explicit: OpenTelemetry owns `trace_id`; Wright owns
`wright.correlation_id` and the `X-Trace-Id` header. Tests must prove API
responses, backend logs, and UI logs share the correlation ID.

## Avoid

- Do not solve OpenClaw by copying Hermes branches and renaming variables.
- Do not make `.hermes.md` or `~/.hermes` part of the generic workspace model.
- Do not put Docker execution behind an ordinary web route by default.
- Do not add FreeCAD, OpenSCAD, Blender, SolidWorks, vendor SDKs, license
  managers, or other MCP-specific host software to the base validation image.
- Do not let API migrations remain the long-term catalog editor.
- Do not re-derive backend safety policy in React components.
- Do not silently remove uncertain catalog entries because validation is hard.
- Do not introduce network-dependent tests into the default fast suite.
- Do not enable remote telemetry export by default.
- Do not log raw credentials, full environment maps, unredacted commands, raw
  tool arguments, or full subprocess output.
- Do not treat `X-Trace-Id` as the OpenTelemetry trace ID unless Wright adopts
  full W3C trace-context propagation.

## Definition Of Done

Phase 2 is complete when:

- A non-Hermes stub provider can create and activate a workspace through the
  same generic API path without Hermes file/path writes.
- Workspace route business logic is delegated to `workspace_service`.
- Canonical MCP catalog data and schema live in `tool_registry`.
- Safety policy is enforced at install/start/call boundaries.
- Clean-container validation has an opt-in CLI path and produces JSON plus
  Markdown evidence.
- Generated UI contracts are in use for MCP, agent, validation, and workspace
  surfaces touched by phase 2.
- Priority UI workflows have stable test IDs and tokenized layout.
- Structured logs, correlation IDs, OpenTelemetry traces, redaction, and typed
  errors cover workspace activation, agent runtime selection, agent context
  materialization, catalog refresh, MCP safety decisions, MCP lifecycle, tool
  calls, validation planning, validation runs, and evidence writing.
- Remote telemetry export is disabled by default and covered by tests.
- Docs describe Hermes as first-class but not architectural, and OpenClaw as a
  peer adapter target.
