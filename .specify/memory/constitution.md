# Virtual Mechanical Engineer Constitution v1.0.0

## 1. Architectural Foundation
* **Framework**: The backend API MUST be implemented using the strictly typed FastAPI framework to ensure native Pydantic data validation and fast local execution.
* **Architecture**: The system MUST utilize a Modular Monorepo (using `uv` or `Poetry`). Code MUST follow strict boundaries: API routes must contain zero business logic and route immediately to the isolated `agent_adapters` and `tool_registry` packages.
* **Offline-First Mandate**: The entire appliance MUST be capable of running fully air-gapped. No core functionality may rely on an external cloud API without a graceful local fallback.

## 2. Serving & Execution
* **Container Strategy (Thick Base / Thin Code)**: Production and development environments MUST utilize a heavy base Docker image (containing CUDA, PyTorch, FreeCAD, CalculiX). Application logic (`/apps` and `/packages`) MUST be mounted as live volumes to allow instant iteration without container rebuilds.
* **Agent Abstraction**: LLM agents (Hermes, Qwen, openclaw, PI) MUST NOT be hardcoded into the API. They MUST be integrated via an Adapter Pattern (`BaseAgentEngine`) to allow hot-swapping of models and frameworks.

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
Amendments to this constitution require a documented proposal, review, and approval from the project maintainers. All pull requests and AI-generated code must verify compliance with these principles.

**Version**: 1.0.0 | **Ratified**: 2026-06-02
