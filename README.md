<p align="center">
  <img src="docs/images/wright-logo.png" width="180" alt="Wright Logo">
</p>

<h1 align="center">Wright</h1>

<p align="center">
  <strong>An open-source agent orchestrator for physical engineering — actuating deterministic tools for designers, engineers, and product managers.</strong>
</p>

<p align="center">
  <a href="https://github.com/burhop/wright/actions"><img src="https://github.com/burhop/wright/actions/workflows/docker-build.yml/badge.svg" alt="Build Status"></a>
  <a href="https://opensource.org/licenses/MIT"><img src="https://img.shields.io/badge/License-MIT-yellow.svg" alt="License: MIT"></a>
  <a href="https://hub.docker.com/r/burhop/wright"><img src="https://img.shields.io/docker/pulls/burhop/wright.svg" alt="Docker Pulls"></a>
  <a href="https://www.python.org/downloads/"><img src="https://img.shields.io/badge/python-3.11+-blue.svg" alt="Python 3.11+"></a>
  <a href="https://nodejs.org/"><img src="https://img.shields.io/badge/node-22+-green.svg" alt="Node 22+"></a>
  <a href="https://github.com/burhop/wright/stargazers"><img src="https://img.shields.io/github/stars/burhop/wright.svg?style=social" alt="GitHub stars"></a>
</p>

---

## Why Wright?

### The Vision
The rise of generative AI has brought unprecedented, compound productivity gains to software developers. Wright is built to bring this same AI-driven engineering velocity to traditional physical engineering roles. 

Our vision is to unlock new, order-of-magnitude levels of productivity for **product designers**, **engineers** (mechanical, structural, thermal, electrical), and **engineering product managers**. By orchestrating specialized, agentic workflows, Wright bridges the gap between high-level engineering design intent and low-level computational execution, enabling the engineer to model, simulate, and manufacture faster than ever before.

### Orchestrating Deterministic Tools
Physical engineering demands absolute mathematical rigor. While LLMs excel at planning, reasoning, and translating natural language into design parameters, they are probabilistic and cannot directly compute physical load vectors or compile error-free CAD geometry. 

Wright bridges this gap. It positions AI agents not as direct geometry creators, but as orchestrators that **actuate, coordinate, and steer deterministic engineering tools**. The AI manages the high-level workflow loops, parameter optimization, and feedback cycles, while industry-standard deterministic kernels guarantee physical validity and mathematical precision:
* **Commercial Vendors**: Coordinate enterprise CAD/CAM suites (like SolidWorks, Creo, Fusion 360) and proprietary cloud simulation APIs.
* **Startups**: Actuate cutting-edge generative design, neural topology optimization, and programmatic geometry platforms (like Zoo/KittyCAD).
* **Universities & Researchers**: Hook into specialized academic solvers, finite element analyses (FEA), and custom engineering calculators.
* **Open Source Developers**: Actuate community-driven tools like FreeCAD, OpenSCAD, CalculiX, and PrusaSlicer via the standardized Model Context Protocol (MCP).

### Secure and Flexible Execution
* **Orchestration Power**: Run any agentic framework or LLM model. Swap commercial cloud models, research APIs, and local models seamlessly.
* **Modular Integrations**: Actuate professional CAD, FEA, and CAM software via extensible, standardized MCP servers.
* **Local or Hybrid Cloud**: Wright's architecture is fully open. While capable of running completely local and air-gapped on enterprise hardware (like the Dell GB10 / NVIDIA DGX Spark) to safeguard proprietary designs, it is equally ready to scale with cloud-based hybrid tools.

### Built on Open Industry Standards
Wright is committed to open, vendor-neutral standards that allow the toolbox to grow alongside the AI and engineering ecosystems. We actively support and plan compatibility with key emerging specs:
* **[Model Context Protocol (MCP)](https://github.com/modelcontextprotocol)**: Developed under the Linux Foundation, MCP serves as our core translation layer, enabling loose coupling so any compliant tool, database, or API can be actuated by any agent runtime.
* **[MCP Apps](https://github.com/modelcontextprotocol/ext-apps)** (the official standardization of the experimental *MCP-UI* proposal): Allows MCP servers to deliver rich, dynamic web interfaces (such as parameter sliders and data visualizations) that render directly in the agent session.
* **[WebMCP](https://github.com/webmachinelearning/webmcp)**: A browser-native standard incubated by the W3C Web Machine Learning Community Group that exposes web forms and imperative JavaScript APIs to agents via `navigator.modelContext`, letting Wright actuate browser-based tooling natively.

---

## Key Features

* 🤖 **Universal Agent Orchestration** — Act as the central coordinator and control loop, coordinating any LLM engine (commercial cloud, startup APIs, or local runtimes) and agentic framework.
* 🔌 **Plug-and-Play Tool Registry** — Load, swap, and manage any compliant engineering tool via standard Model Context Protocol (MCP) servers. The core platform is completely decoupled from the tools themselves.
* 🔧 **Deterministic Tool Actuation** — Actuate and steer rigorous physical engineering engines. Rather than relying on probabilistic models to generate geometry or math, Wright coordinates deterministic external software:
  * *CAD & Geometry kernels* (e.g., FreeCAD, OpenSCAD, PTC Creo, Autodesk Fusion 360) for parametric solid modeling
  * *CAE & Simulation solvers* (e.g., CalculiX FEA, OpenFOAM CFD) for structural stress and thermal analysis
  * *CAM & Manufacturing engines* (e.g., PrusaSlicer, CuraEngine) for automated G-code toolpath slicing
* 🚀 **Software-Level Workflow Automation** — Bring rapid prototyping, versioned rollbacks (via local Git), and test-driven loops of modern software development to physical design tasks.
* 🔒 **Flexible & Secure Deployment** — Run local-first (on on-prem hardware to safeguard IP) or scale using hybrid cloud tools.
* 🐳 **Appliance-in-a-Box Setup** — Get started instantly with a bundled Docker stack that includes standard open-source tools (FreeCAD, OpenSCAD, CalculiX) pre-configured.

---

## User Interface

### 1. Agent Chat Interface
Interact with local LLM agents to iterate on designs, request modifications, or write code.
![Agent Chat Interface](docs/images/screenshot_agent_chat.png)

### 2. Tool Registry
View active engineering tools (CAD, simulation, calculators) available to the AI agents.
![Tool Registry](docs/images/screenshot_tool_registry.png)

### 3. File Vault
Browse STEP, STL, and G-code artifacts generated by the agent during design turns.
![File Vault](docs/images/screenshot_file_vault.png)

---

## Quick Start

### Docker (Recommended)

Start the complete local appliance stack with a single command. 

```bash
# 1. Clone the repository
git clone https://github.com/burhop/wright.git && cd wright

# 2. Configure your local LLM API credentials
cp docker/.env.example docker/.env
# Edit docker/.env and set your API keys

# 3. Build and launch the container
make docker-build && docker compose up
# Open http://localhost:8080 in your browser
```

For advanced manual installation (development outside Docker using `uv`), see [CONTRIBUTING.md](CONTRIBUTING.md).

---

## Architecture

Wright is built as a modular monorepo, separating routing endpoints from domain business logic and agent runtimes.

```mermaid
flowchart TD
    User([User Web Browser]) -->|HTTP / WebSockets| API[FastAPI API Gateway]
    API -->|Routing| Agent[BaseAgentEngine - Hermes]
    API -->|Routing| MCP[McpEngine - Tool Registry]
    Agent -->|Uses| MCP
    MCP -->|Subprocess| OpenSCAD[OpenSCAD Headless]
    MCP -->|Simulations| CalculiX[CalculiX FEA]
    API -->|Database & Vector RAG| Vault[Local SQLite & LanceDB]
```

### Repository Structure
```text
wright/
├── apps/
│   ├── api/                    # FastAPI — zero business logic, routing only
│   └── web/                    # Frontend UI (React + Vite, atomic design)
├── packages/
│   ├── core/                   # Shared domain models, structured JSON logging
│   ├── agent_adapters/         # Adapter pattern for LLM agents (Hermes, openclaw, PI)
│   ├── tool_registry/          # BaseTool pattern with online/offline fallback
│   └── data_vault/             # SQLite (WAL) + LanceDB (Arrow) + filesystem vault
├── tests/
│   ├── ui-integration/         # Tier 2 — Playwright UI integration tests
│   └── e2e/                    # Tier 3 — System smoke tests
├── docker/                     # Dockerfile and supervisord process configurations
├── docs/                       # Architecture specifications and documentation
└── .specify/                   # Spec-kit developer workflow configurations
```

Refer to [docs/virtual_engineer_architecture.pdf](docs/virtual_engineer_architecture.pdf) for the formal architecture analysis, and [constitution.md](constitution.md) for core project engineering standards.

---

## Spec-Kit (Spec-Driven Development)

This project uses [spec-kit](https://github.com/github/spec-kit) with the Antigravity (`agy`) integration. Available workflow skills:

| Skill | Purpose |
|---|---|
| `$speckit-constitution` | Establish project principles |
| `$speckit-specify` | Define what to build |
| `$speckit-plan` | Create implementation plans |
| `$speckit-tasks` | Generate actionable task lists |
| `$speckit-implement` | Execute implementation |
| `$speckit-clarify` | Clarify ambiguous areas |
| `$speckit-analyze` | Cross-artifact consistency check |

---

## Contributing

We welcome contributions from the community! Please read our [CONTRIBUTING.md](CONTRIBUTING.md) for details on our code style, specification requirements, and local setup. 

Looking for a place to start? Look for the **Good First Issue** label on our issues tracker!

---

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## Star History & Contributors

[![Star History Chart](https://api.star-history.com/svg?repos=burhop/wright&type=Date)](https://github.com/burhop/wright)

<a href="https://github.com/burhop/wright/graphs/contributors">
  <img src="https://contrib.rocks/image?repo=burhop/wright" alt="Contributors list">
</a>
