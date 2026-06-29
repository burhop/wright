# Platform Overview

Wright is a modular agent orchestration platform built to enable autonomous, local-first product design, CAD manipulation, structural engineering, and manufacturing setups. 

By utilizing the open **Model Context Protocol (MCP)**, Wright decouples Large Language Model reasoning from system-specific engineering packages, bringing agentic capabilities to standard computational software.

## The Engineering AI-in-a-Box Concept

Traditional engineering software runs inside heavy desktop client configurations or fragmented cloud networks, creating significant latency and data governance vulnerabilities. Wright consolidates:
1.  **Multi-Agent Coordination Layer**: Specialized agent systems routing design plans, execution instructions, and code verification stages.
2.  **Model Context Protocol Engine**: Unified server executors connecting LLMs to local filesystems, command lines, and binary geometry kernels.
3.  **Deterministic tool layer**: Cataloged MCP servers can connect agents to selected local or hosted engineering tools such as FreeCAD, CalculiX, OpenSCAD, and vendor systems when those dependencies are installed and validated for that workflow.

Coupled with professional workstations and selected tool installs, Wright can form a local-first engineering appliance while keeping AI providers and MCP host dependencies explicit.

## Core Workflows

```
┌─────────────────┐       ┌──────────────────┐       ┌───────────────────┐
│ 1. Define Spec  │ ───>  │ 2. Draft CAD     │ ───>  │ 3. Run Simulation │
│ (Spec-Kit docs) │       │ (OpenSCAD/FreeCAD)│      │ (CalculiX/OpenFOAM)│
└─────────────────┘       └──────────────────┘       └───────────────────┘
                                                               │
                                                               ▼
┌─────────────────┐       ┌──────────────────┐       ┌───────────────────┐
│ 6. Commit & Tag │ <───  │ 5. Slice G-Code  │ <───  │ 4. Verify Mesh    │
│ (Local Git repo)│       │ (PrusaSlicer CLI)│       │ (OpenCASCADE OCCT)│
└─────────────────┘       └──────────────────┘       └───────────────────┘
```

1.  **Specification Generation**: Outline requirements using standard markdown and YAML structures.
2.  **Parametric Drafting**: Agents generate parametric shapes using script-driven modeling engines.
3.  **Simulation & Mesh Verification**: Structural stress (FEA) and fluid flow (CFD) run automatically to assess load limits.
4.  **Manufacturing Execution**: Files slice to G-code formats to prepare for additive and subtractive industrial machines.
5.  **Workspace Commit**: Version design modifications inside the workspace Git repository.
