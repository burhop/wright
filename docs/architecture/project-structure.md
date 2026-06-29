# Project & Monorepo Structure

Wright is structured as a **Modular Monorepo** managed by `uv` to enforce strict architectural boundaries and facilitate fast local dependency resolution. Business logic is completely isolated from routing and presentation, ensuring modularity, testability, and hot-swappable AI backends.

## Directory Layout

```text
wright/
├── apps/
│   ├── api/                    # FastAPI web server (Zero-business-logic, routing only)
│   └── web/                    # React 19 Frontend SPA (Atomic design, WebGL visualization)
├── packages/
│   ├── core/                   # Shared domain models, workspace Git state, and logging/tracing
│   ├── agent_adapters/         # Abstracted interfaces & adapters for LLM engines
│   ├── tool_registry/          # Model Context Protocol (MCP) engine and execution runners
│   └── data_vault/             # Embedded database managers (SQLite WAL, Vector RAG)
├── specs/                      # Spec-kit documentation (Spec-Driven Development)
└── tests/                      # 3-Tier Testing suite (Vitest, pytest, Playwright E2E)
```

## Containerization Strategy

Wright's public-alpha Docker appliance is a local-first control plane for the
API, web UI, Hermes integration, and MCP catalog. It does not bundle an LLM,
model weights, hosted provider account, paid engineering backend, or
MCP-specific host software.

Current container roles:

*   **Runtime image (`docker/Dockerfile`)**: Builds the React UI, installs the
    Wright Python workspace, installs Hermes with the Wright plugin, and runs
    `wright-api` plus `hermes-gateway` under supervisord.
*   **Compose entry points**: `docker-compose.minimal.yml` is the recommended
    public-alpha first run on `http://localhost:8080`; `docker-compose.yml` adds
    Jaeger and uses `http://localhost:8000`.
*   **Selected MCP dependencies**: FreeCAD, OpenSCAD, CalculiX, Blender, vendor
    CAD systems, license managers, GPU drivers, and similar host software are
    installed only for the selected MCP server being validated or used.
*   **Clean-container validation**: Engineering MCP server validation follows
    `docs/mcp-catalog/mcp-server-testing-process.md`; do not add MCP-specific
    host software to the base image just to make catalog validation pass.

---

## Engineering Workspace & Local Git Integration

Every project within Wright is structured as a standard directory on the local disk managed by a local **Git repository**. The backend core package exposes a robust `WorkspaceManager` that handles file browser trees, state synchronization, and conflict resolution:

*   **Git-Porcelain Status Mapping**: Files are monitored in real-time. The file tree endpoint queries `git status --porcelain` to label each file node as *Unmodified (Clean)*, *Added (A)*, *Deleted (D)*, *Modified (M)*, or *Untracked (U)*, displaying these states directly in the IDE UI.
*   **Atomic Operations & Lock Management**: To prevent simultaneous write corruption from concurrent agents or human edits, the `WorkspaceManager` implements file-level locking. A hashing mechanism registers locks inside a hidden `.git/workspace_locks/` directory.
*   **Reversion and Checkpoint Commits**: Prior to running complex design scripts, the workspace commits changes locally. If the resulting CAD script fails execution or generates self-intersecting meshes, the system executes an automated rollback (`git reset --hard HEAD`), ensuring the design timeline remains unbroken.
*   **Path Traversal Protection**: To enforce strict security boundaries, the `WorkspaceManager` sanitizes and validates all relative paths, preventing agents from reading or writing files outside the designated workspace path or the local `/tmp/` scratch directory.
