# Wright Project Roadmap

Wright is a public-alpha, local-first agent orchestrator for physical
engineering. This roadmap describes the direction of travel, not a production
support guarantee.

## Public Alpha Priorities

- [ ] MCP catalog improvements: continue validating engineering MCP entries,
  add setup recipes, and convert failed validations into durable follow-up
  records.
- [ ] Web MCP support: prototype browser-native tool actuation while keeping
  credential and origin boundaries explicit.
- [ ] Process-flow support: add workflow views for multi-step engineering runs
  such as spec to CAD to mesh to simulation to review.
- [ ] OpenClaw support: complete the OpenClaw agent adapter path and add parity
  tests with Hermes-backed workflows.
- [ ] Hermes Desktop integration: deepen panel, setup, and status integration
  while keeping browser-based Wright usable on its own.
- [ ] Local LLM setup flows: improve setup and status screens for
  OpenAI-compatible local servers, hosted providers, degraded health states, and
  troubleshooting.
- [ ] Security and workspace isolation: harden workspace boundaries, secret
  handling, local auth, and MCP execution safety before broader public use.
- [ ] CAD/CAE/CAM artifact viewers: add first-class STEP, STL, G-code, mesh,
  simulation result, and validation viewers.
- [ ] MCP Apps and embedded panels: explore safe, inspectable parameter panels
  and embedded UI surfaces for engineering tool control.

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

## Agent Intelligence and Orchestration

- [ ] Universal LLM configuration for commercial cloud APIs and local offline
  runtimes.
- [ ] Additional agent adapters for OpenClaw, PI, and future runtimes.
- [ ] Multi-agent engineering review flows with specialized roles.
- [ ] Long-term session memory through agent adapters and local storage.

## Workspace and Core Infrastructure

- [ ] Workspace and session management with per-workspace tool assignment.
- [ ] Workspace RAG for project files, requirement specs, and CAD data.
- [ ] Local Git integration for generated artifacts and rollback flows.
- [ ] Authentication and access control for team or secure hosted deployments.
- [ ] Encrypted local vault support for sensitive engineering IP.

## Execution Environments and UI

- [ ] Sandboxed Python execution for agent-written scripts.
- [ ] Interactive panels for charts, tables, and generated code review.
- [ ] Frontend polish for responsive design, accessibility, and chat flow.
- [ ] Robust in-browser viewers for STEP, STL, G-code, 3MF, meshes, and results.

## Physical Engineering Capabilities

- [ ] Local geometry conversion utilities for common CAD formats.
- [ ] FEA/CFD result visualization in the workspace.
- [ ] Generative concept rendering as an optional, explicitly configured path.
- [ ] Model-builder integration for collaborative model construction.

## Collaboration and Project Management

- [ ] Community and team connectors such as Discord or Signal.
- [ ] Project-management views for engineering tasks and milestones.
- [ ] Automated engineering reports in Markdown and PDF.
- [ ] Multiplayer sessions for shared agent workspaces.

## Contributing

Have feedback or want to help? Use
[GitHub Discussions](https://github.com/burhop/wright/discussions) for
questions and [GitHub Issues](https://github.com/burhop/wright/issues) for
reproducible bugs or scoped feature requests.
