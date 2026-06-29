# System Overview

Wright is a modular agent orchestration platform that engineers and designers
use to manage AI-assisted product development workflows. Wright is alpha
software and bring-your-own-AI: it does not bundle an LLM, model weights,
hosted provider account, API key, paid engineering backend, or MCP-specific host
software.

When coupled with local high-performance hardware, such as a GB10 or NVIDIA DGX
Spark-style workstation, Wright can be configured as a local-first engineering
appliance. Operators still provide the model endpoint through `LLM_API_URL` and
install selected MCP host dependencies only for the engineering tools they are
validating or using.

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
       ┌──────────────────┬─────────────────────┼─────────────────────┬──────────────────┐
       ▼                  ▼                     ▼                     ▼                  ▼
[Concept Agents]    [CAD Agents]        [Simulation Agents]   [Machining Agents]  [Systems Agents]
       │                  │                     │                     │                  │
       └──────────────────┴───────────┬─────────┴─────────────────────┴──────────────────┘
                                      ▼
                        Model Context Protocol (MCP)
                                      ▼
             Universal Integrations (Open Source & Enterprise Vendors)
```

## System Block Diagram

```mermaid
graph TD
    User([Engineers / Designers]) <--> |Browser UI / Web3D| FE[React 19 Frontend SPA]
    FE <--> |Local Network HTTP / SSE / WS| BE[FastAPI API Gateway]
    
    subgraph Local-First Engineering Appliance (e.g. GB10 / DGX Spark)
        BE <--> |Adapter Pattern| AA[Agent Adapters: Local/Remote LLM Engines]
        BE <--> |JSON-RPC over Pipes/WebSockets| TR[TR: McpEngine / Extensible Tool Registry]
        BE <--> |In-Process Arrow| DV[Data Vault: Vector RAG]
        BE <--> |SQL / WAL Mode| DB[(SQLite State Database)]
        
        TR <--> |stdio / subprocess| SC[Selected MCP Toolchains: open-source, vendor, or local installs]
        TR <--> |webmcp / websocket| BR[Browser DOM Tools]
    end
```

## The Core Value Proposition

*   **Agent Orchestration Platform**: Wright empowers the engineer to deploy and manage task-specific agents tailored to different phases of the design cycle, from initial concept to physical production.
*   **Universal Tool Actuation**: Wright leverages the open Model Context Protocol (MCP) as a universal interface layer. If an MCP server is configured for a tool, database, or API in any engineering domain, Wright's orchestrator enables the appropriate agent to utilize it programmatically. This extends from open-source tools to commercial enterprise suites from Autodesk, Siemens, PTC, and Dassault Systèmes.
*   **Local-First Engineering Appliance**: Coupled with hardware like a GB10 or DGX Spark-style workstation, Wright can provide a local engineering sandbox. The appliance is not self-contained for every CAD, CAE, CAM, or AI workflow; selected MCP servers and model endpoints must be configured per use case.
*   **Model Agnostic**: Fully decoupled from underlying LLMs, the orchestrator connects to either local on-premise models or remote cloud endpoints supplied by the operator.

## Security & Governance Control

Operating on sensitive intellectual property, Wright incorporates native, air-gapped security frameworks:

*   **Zero-Cloud Authentication**: Uses FastAPI's native `OAuth2PasswordBearer` with `passlib` (bcrypt hashing) and `python-jose` (JSON Web Tokens) to authenticate local operators. No external telemetry or cloud identity providers (e.g., Auth0, Cognito) are permitted.
*   **Role-Based Access Control (RBAC)**: Distinguishes between standard Engineers (allowed to execute chats, browse files, and run CAD tools) and Administrators (allowed to register custom MCP tools, delete workspace histories, and modify engine configurations).
*   **Destructive Gating via MCP Metadata**: Interactive tools expose semantic metadata tags (`readOnlyHint`, `destructiveHint`, `idempotentHint`). Safe operations (e.g., querying mechanical properties, listing file nodes) are executed automatically by the agent. Destructive actions (e.g., executing shell scripts, deleting CAD bodies, committing git history) are paused by the client shell, requiring explicit user approval before execution.
