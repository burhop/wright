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

## Containerization Strategy (Thick Base / Thin Code)

To eliminate local dependency drift and simplify deployment on air-gapped hardware, Wright employs a **Thick Base / Thin Code** Docker architecture:

*   **Base Image (`Dockerfile.base`)**: Contains the massive, system-level dependencies required for engineering computation, including NVIDIA CUDA runtimes, PyTorch, FreeCAD (Python bindings), CalculiX (FEA solver), and OpenSCAD.
*   **Application Mount**: The application logic (`/apps` and `/packages`) is mounted as a live volume during development and container execution. This permits near-instant iteration and agent-driven hot-swapping without costly container rebuilds, maximizing deployment efficiency.

---

## Engineering Workspace & Local Git Integration

Every project within Wright is structured as a standard directory on the local disk managed by a local **Git repository**. The backend core package exposes a robust `WorkspaceManager` that handles file browser trees, state synchronization, and conflict resolution:

*   **Git-Porcelain Status Mapping**: Files are monitored in real-time. The file tree endpoint queries `git status --porcelain` to label each file node as *Unmodified (Clean)*, *Added (A)*, *Deleted (D)*, *Modified (M)*, or *Untracked (U)*, displaying these states directly in the IDE UI.
*   **Atomic Operations & Lock Management**: To prevent simultaneous write corruption from concurrent agents or human edits, the `WorkspaceManager` implements file-level locking. A hashing mechanism registers locks inside a hidden `.git/workspace_locks/` directory.
*   **Reversion and Checkpoint Commits**: Prior to running complex design scripts, the workspace commits changes locally. If the resulting CAD script fails execution or generates self-intersecting meshes, the system executes an automated rollback (`git reset --hard HEAD`), ensuring the design timeline remains unbroken.
*   **Path Traversal Protection**: To enforce strict security boundaries, the `WorkspaceManager` sanitizes and validates all relative paths, preventing agents from reading or writing files outside the designated workspace path or the local `/tmp/` scratch directory.
