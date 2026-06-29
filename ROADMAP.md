# Wright Project Roadmap

This document outlines the strategic vision and upcoming feature development for Wright. Our goal is to create the premier open-source agent orchestrator for physical engineering. 

Rather than strict chronological phases, we organize our roadmap into **Development Tracks**. These areas can be developed in parallel depending on contributor interests, community needs, and project priorities.

## Public Alpha Priorities

These items are the near-term backlog for making Wright useful to MCP porters,
demo users, and selected beta testers while preserving its alpha status.

- [ ] **MCP Catalog Improvements:** Continue validating statused engineering MCP
  entries, add setup recipes, and convert failed validations into durable
  follow-up records.
- [ ] **Web MCP Support:** Prototype browser-native WebMCP flows for web-based
  engineering tools while keeping credential and origin boundaries explicit.
- [ ] **Process Flow Support:** Add workflow/process views for multi-step
  engineering runs such as spec -> CAD -> mesh -> simulation -> review.
- [ ] **OpenClaw Support:** Complete the OpenClaw agent adapter path and add
  parity tests with Hermes-backed workflows.
- [ ] **Hermes Desktop Integration:** Deepen panel, setup, and status integration
  with Hermes Desktop while keeping browser-based Wright usable on its own.
- [ ] **Local LLM Setup Flows:** Improve setup/status screens for OpenAI-
  compatible local servers, hosted providers, degraded health states, and
  troubleshooting.
- [ ] **Security and Workspace Isolation:** Harden workspace boundaries, secret
  handling, local auth, and MCP execution safety before broader public use.
- [ ] **CAD/CAE/CAM Artifact Viewers:** Add first-class STEP, STL, G-code, mesh,
  simulation result, and validation viewers.
- [ ] **MCP Apps / Embedded Panels:** Explore parameter panels and embedded UI
  surfaces for safe, inspectable engineering tool control.

## Needed MCP Server Backlog

Candidates remain disabled or limited until their source, dependency burden,
platform support, and safety posture are validated.

| Priority | Area | Candidate | Source | Status | Dependencies | Platforms | Safety notes | Next action |
|:---|:---|:---|:---|:---|:---|:---|:---|:---|
| P0 | CAD/geometry | OpenSCAD linter/server | `docs/mcp-catalog/tools-list.md` | Follow-up exists | OpenSCAD for full backend probe | Linux first | Safe read/export probes only | Finish clean-container recipe |
| P0 | CAD/geometry | FreeCAD engineering MCPs | `docs/mcp-catalog/tools-list.md` | Follow-ups exist | FreeCAD host install/AppImage | Linux/Windows varies | Avoid destructive filesystem actions | Validate dependency-missing diagnostics |
| P1 | FEA/CFD | CalculiX/OpenFOAM adapters | To source | Needed | Solver installs, meshes, examples | Linux first | Non-destructive sample simulations only | Identify maintained MCP servers |
| P1 | CAM/slicing | PrusaSlicer/CuraEngine adapters | To source | Needed | CLI slicer and sample STL | Linux/Windows/macOS varies | No machine-control output execution | Find maintained CLI-safe MCPs |
| P1 | Electronics/EDA | KiCad MCP | `docs/mcp-catalog/tools-list.md` | Follow-up exists | KiCad install | Linux/Windows/macOS varies | Read-only project inspection first | Retest with clean dependency recipe |
| P2 | PLM/PDM/docs | Document/PDM connectors | To source | Needed | Provider APIs, credentials | Cloud/enterprise varies | Credential-bound, disabled by default | Inventory open-source candidates |
| P2 | Vendor/proprietary | SolidWorks/Fusion/Creo bridges | `docs/mcp-catalog/tools-list.md` | Follow-ups exist | Licensed desktop software/SDKs | Mostly Windows/macOS | License-bound and host-dependent | Keep blocked until maintainer can test |
| P2 | Browser/Web MCP | Web-based CAD and calculators | To source | Needed | Browser APIs, site credentials | Browser-dependent | Origin and credential isolation required | Prototype with non-sensitive demo tool |

## 🧠 Agent Intelligence & Orchestration
*Focuses on the core LLM capabilities, multi-agent frameworks, and specialized personas.*

- [ ] **Universal LLM Configuration:** Provide an intuitive UI and config system to seamlessly define and hot-swap LLM servers. Support both commercial cloud APIs (OpenAI, Anthropic) and local offline runtimes (Ollama, vLLM).
- [ ] **Advanced Agent Adapters:** Complete robust integration for the OpenClaw and PI agent frameworks to allow flexible agent runtime selection.
- [ ] **Council of Engineers:** Implement a multi-agent framework where different specialized agents can collaborate, debate, and solve complex multidisciplinary problems together.
- [ ] **Engineering Personalities:** Define distinct engineering personas (e.g., Thermal Expert, Structural Analyst, Manufacturing Engineer) with specialized system prompts and restricted toolsets.
- [ ] **Long-Term Session Memory:** Implement memory compression and persistent context (managed directly by agent adapters like Hermes, OpenClaw, or PI) so agents can recall design decisions made weeks or months prior across different sessions.

## 🏗️ Workspace & Core Infrastructure
*Focuses on session management, data persistence, security, and version control.*

- [ ] **Workspace & Session Management:** Overhaul the workspace model. Allow assigning specific MCP tool servers to a workspace and maintaining multiple saved conversation sessions per workspace.
- [ ] **Workspace RAG (Retrieval-Augmented Generation):** Implement intelligent semantic search tied to specific workspaces to contextually query project files, requirement specs, and CAD data.
- [ ] **Git Integration & Versioning:** Finish local Git integration for automatic versioned rollbacks of CAD/code artifacts generated by agents.
- [ ] **Authentication & Access Control:** Implement User Login (OAuth, Local Auth) for multi-tenant deployments, teams, or secure hosted environments.
- [ ] **Encrypted Data Vault:** Support for encrypting local workspaces at rest to protect highly sensitive proprietary engineering IP from unauthorized access.

## 💻 Execution Environments & UI
*Focuses on how agents execute code, present data, and interact with the user.*

- [ ] **Sandboxed Python Execution:** Provide a safe, isolated Python environment (e.g., via Docker or WebAssembly) for agents to write and execute scripts securely.
- [ ] **Interactive UI Panels:** Create a simple framework to render agent-generated Python code (like Plotly charts or data tables) directly inside dynamic UI panels.
- [ ] **Frontend UI Polish:** Modernize the frontend, improving responsive design, accessibility, and the flow of the agent chat interface.
- [ ] **3D Artifact Viewers:** Build out robust, out-of-the-box in-browser panel viewers for generated artifacts. Support formats like STEP, STL, G-Code, 3MF, and 3D Meshes directly in the UI.

## ⚙️ Physical Engineering Capabilities
*Focuses on domain-specific engineering tools and generative models.*

- [ ] **Local 3D Meshing & Generation:** Integrate AI-based 3D meshing or generative geometry models. Prioritize local execution to protect intellectual property.
- [ ] **Generative Image Renderings:** Integrate image generation models (like Stable Diffusion) for rapid product concept renderings and visual ideation.
- [ ] **Native Geometry Conversions:** Add built-in background utilities to convert between common CAD formats without requiring heavy desktop software.
- [ ] **FEA/CFD Result Visualization:** Integrate visualization tools (like VTK.js) to display simulation and load-testing results directly in the chat interface.
- [ ] **Model Builder Integration:** Add future support for integrated model builders, allowing engineers and agents to collaboratively construct and manipulate models directly within the workspace.

## 🤝 Collaboration & Project Management
*Focuses on human-to-agent and team workflows.*

- [ ] **Social & Chat Connectors:** Create Signal and Discord connectivity, including a built-in community Discord connector for agent notifications, status reports, and remote commands.
- [ ] **Integrated Project Management:** Add Kanban boards, Gantt charts, and task tracking tools natively into the workspace so agents can update project statuses based on engineering progress.
- [ ] **Automated Reporting:** Allow agents to compile comprehensive engineering reports (PDF/Markdown) summarizing a session's design decisions, calculations, and final artifacts.
- [ ] **Multiplayer Sessions:** Support simultaneous collaboration where multiple users can interact with the same agent session in real-time.

---

## Contributing
Have feedback or want to help build these features? Join the discussion on our [Discord](https://discord.gg/2JsdMRxq) or check out the [GitHub Issues](https://github.com/burhop/wright/issues).
