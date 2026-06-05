# Wright Platform

Welcome to the official documentation for **Wright**, a local-first multi-agent mechanical engineering appliance designed for advanced design, simulation, and product development workflows.

Wright provides a standalone, high-performance **"engineering AI-in-a-box"** that operates entirely offline, enabling developers and engineers to orchestrate multiple specialized AI agents across standard CAD, CAM, FEA, and PLM toolchains.

```
                         ┌───────────────────────────┐
                         │   Engineers & Designers   │
                         └─────────────┬─────────────┘
                                       │
                                       ▼
                         ┌───────────────────────────┐
                         │   Wright Orchestrator     │
                         └─────────────┬─────────────┘
                                       │
 ┌──────────────────┬──────────────────┼──────────────────┬──────────────────┐
 ▼                  ▼                  ▼                  ▼                  ▼
[Concept Agents]  [CAD Agents] [Simulation Agents] [Machining Agents] [Systems Agents]
 │                  │                  │                  │                  │
 └──────────────────┴────────┬─────────┴──────────────────┴──────────────────┘
                             ▼
                Model Context Protocol (MCP)
                             ▼
    Universal Integrations (Open Source & Enterprise Vendors)
```

## Key Features

*   **Multi-Agent Orchestration**: Coordinate specialized AI agents (such as Hermes, OpenClaw, and Pi) to handle complex product design, analysis, and execution tasks.
*   **Model Context Protocol (MCP)**: Actuate third-party software packages and enterprise CAD/CAM configurations using MCP as a universal interface layer.
*   **Offline-First & Secure**: Built with zero cloud-dependencies to ensure complete data security for defense, aerospace, and advanced R&D sectors.
*   **Agnostic LLM Backends**: Seamlessly connect to local on-premise model runtimes or remote cloud endpoints.
*   **Monorepo Architecture**: Clean separation of API, Web dashboard, and package runtimes.

---

To get started, follow our [Getting Started Overview](getting-started/overview.md).
