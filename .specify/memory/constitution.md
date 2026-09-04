<!--
Sync Impact Report
- Version change: 3.0.0 -> 3.1.0 (2026-09-04)
- Modified principles:
  - Architectural Foundation: explicitly include the established workspace_service application boundary, with core/data_vault ownership and dependency-direction gates retained.
- Added sections: none
- Removed sections: none
- Templates:
  - .specify/templates/plan-template.md: validated; no structural change required
  - .specify/templates/spec-template.md: validated; no structural change required
  - .specify/templates/tasks-template.md: validated; no structural change required
- Feature guidance: specs/079-wright-native-authoring/plan.md and milestone-decision.md record the bounded amendment and independent finding C1.
- Prior distribution/runtime obligations from v3.0.0 remain unchanged.
- Deferred placeholders: none
-->
# Virtual Mechanical Engineer Constitution v3.1.0

Amendment 2026-09-04: Under the user's standing native-milestone architecture authorization, clarify the established modular application-service boundary. The prior wording named only adapter/registry packages despite the accepted workspace-service architecture. Independent planning review identified this contradiction (C1); this prospective clarification changes no historical approval or evidence and does not weaken thin routes, offline operation, or security gates.

## 1. Architectural Foundation
* **Framework**: The backend API MUST be implemented using the strictly typed FastAPI framework to ensure native Pydantic data validation and fast local execution.
* **Architecture**: The system MUST utilize a Modular Monorepo (using `uv` or `Poetry`). API routes MUST contain no business logic and delegate to isolated application services in `workspace_service`, `agent_adapters`, or `tool_registry` according to ownership. Pure domain contracts belong in `core`; storage belongs in `data_vault`. Application services compose these boundaries without importing HTTP transport code. Existing dependency-direction and package-boundary checks remain mandatory.
* **Offline-First Mandate**: The entire appliance MUST be capable of running fully air-gapped. No core functionality may rely on an external cloud API without a graceful local fallback.

## 2. Serving & Execution
* **Production Distribution Strategy**: Wright MUST ship and verify the shared
  native Wright runtime, every agent-manager adapter it publicly claims as
  supported, and the Docker appliance for every production release. Hermes is
  the primary native path for Hermes users; Codex, OpenClaw, and future managers
  MUST consume the same Wright runtime and MCP service through their own thin
  adapters. An adapter MAY rely on prerequisites of its manager's documented
  installation mechanism, such as Git for Hermes or Node.js/npm for OpenClaw.
  After an adapter is installed, Wright runtime installation, startup, and
  operation MUST NOT require a Wright source checkout, `WRIGHT_REPO_DIR`, a
  frontend build, or Docker. Docker MUST remain a complete turnkey isolated path
  and a mandatory release artifact; a release is incomplete when any claimed
  native adapter or the Docker path fails its acceptance gates.
* **Container Strategy (Thick Base / Thin Code)**: The Docker production and
  development profiles MUST use the heavy base image containing the approved
  CUDA, PyTorch, FreeCAD, and CalculiX stack. Application logic (`/apps` and
  `/packages`) MUST remain mountable as live volumes for container-based
  iteration without rebuilding the base image. MCP-specific host software MUST
  NOT be added to the base image solely to satisfy catalog validation.
* **Native Runtime Isolation**: Wright MUST manage one versioned runtime and
  stable data root independently of Hermes, Codex, OpenClaw, or any other agent
  manager. Manager adapters MUST invoke the public Wright lifecycle and MCP
  contracts rather than importing application dependencies into the manager
  process. Native installation MUST use prebuilt, versioned application and UI
  artifacts, preserve user data across ordinary upgrades, and provide tested
  rollback and uninstall behavior.
* **Agent Abstraction**: LLM agents and managers (Hermes, Codex, OpenClaw, Qwen,
  and Pi) MUST NOT be hardcoded into the API or native lifecycle core. They MUST
  integrate through adapter contracts (`BaseAgentEngine`, manager installation
  adapters, and the provider-neutral Wright MCP service) so installation rules,
  model frameworks, and session behavior remain independently replaceable.

## 3. Data Storage & RAG (100% Embedded)
* **Zero-Server Databases**: The system MUST NOT rely on background database servers (e.g., standalone PostgreSQL or Qdrant containers) to conserve GPU/CPU resources for local inference.
* **State & Memory**: All relational data (agent sessions, task trees, trace logs) MUST be stored in local **SQLite** utilizing WAL mode for concurrency.
* **Vector RAG**: All semantic engineering data (material specs, standard documentation) MUST be embedded and queried using **LanceDB** running in-process via Apache Arrow.
* **File Vault**: All generated physical artifacts (STEP, STL, G-code) MUST be saved to a structured local file system vault, with file paths indexed in SQLite.

## 4. Security & Identity
* **Local Authentication**: The system MUST use FastAPI's native `OAuth2PasswordBearer` with `passlib` (bcrypt) and `python-jose` (JWT). No external identity providers (Auth0/Cognito) are permitted.
* **Storage**: User credentials MUST be securely hashed and stored in the local SQLite database.
* **Role-Based Access Control (RBAC)**: The system MUST enforce basic roles, distinguishing between administrators (tool/user management) and standard engineers (task execution).

## 5. Engineering Tooling Protocol
* **Template Method Pattern**: Every engineering tool wrapped for LLM use MUST inherit from a `BaseTool` class.
* **Write-Through Cache**: Tools that fetch external data (e.g., standard fastener dimensions from a web API) MUST explicitly implement an `is_online()` check, a `_run_online()` method that caches results to the local vault, and a `_run_offline()` method that retrieves from the cache.
* **CLI/Code Isolation**: Tools must be built so they are completely code-driven and CLI-accessible. No tool can require GUI interaction for the agent to execute it.

## 6. UI & Testing (3-Tier Pyramid)
* **Component Layers**: UI development MUST follow atomic design (Tokens -> Primitives -> Components -> Patterns). All styling flows strictly through design tokens.
* **Tier 1 — Component Tests**: Interactive components MUST have a local testing function (e.g., Storybook `play` functions or equivalent component tests) that exercises states (default, loading, error).
* **Tier 2 — UI Integration**: Page-level user journeys MUST have mocked Playwright tests in `tests/ui-integration/`.
* **Tier 3 — System E2E**: Happy-path smoke tests verifying the local FastAPI backend and LLM response parsing must exist in `tests/e2e/`.
* **Test IDs**: All interactive UI elements MUST include a `data-testid` attribute (e.g., `generate-cad-button`).

## 7. Observability & Tracing (Glass Box Verification)
* **Local OpenTelemetry**: The system MUST export OpenTelemetry traces to a local **Jaeger** container (`jaegertracing/all-in-one`) running via Docker Compose.
* **Structured Logging**: All packages MUST implement structured JSON logging (e.g., `structlog`). Traditional text logs are forbidden.
* **Agent Traceability**: Every user request MUST generate a `trace_id`. This ID must be passed down to every sub-agent, tool execution, and database query.
* **Mandatory Spans**: Always trace:
    * LLM Inference generation times and token counts.
    * Tool execution success/failure (e.g., `tool.cadquery_generate`, `tool.openfoam_sim`).
    * Database reads/writes to LanceDB and SQLite.
* **UI Transparency**: The frontend MUST surface agent decision matrices to the user. Every generated artifact must be verifiable via the UI, displaying the exact prompt, constraints, and Python script used to generate it.

## 8. Autonomous Agent Workflow Rules (speckit / openclaw / Claude Code)
* **Phase Isolation**: Coding agents MUST strictly isolate phases. Planning artifacts (`/plan`) must be approved by the human operator before implementation code (`/implement`) is generated.
* **Branch Discipline**: Agents MUST create and switch to specific feature branches (e.g., `feat/hermes-cad-tool`) before modifying code. Agents are forbidden from committing directly to `main`.
* **Manual Gating**: After completing any major lifecycle command or tool generation, agents MUST stop and wait for explicit human review.

## Governance
Amendments to this constitution require a documented proposal, review, and
approval from the project maintainers. Version changes follow semantic
versioning: MAJOR for incompatible principle redefinitions or removals, MINOR
for new principles or materially expanded guidance, and PATCH for clarifying
wording without changed obligations. Every feature plan MUST evaluate all
principles before design and after contracts are complete. Every pull request
and AI-generated change MUST identify applicable gates, and release changes
MUST update the authoritative merge-gate scripts when new CI failures expose a
missing local gate.

**Version**: 3.1.0 | **Ratified**: 2026-06-02 | **Last Amended**: 2026-09-04
