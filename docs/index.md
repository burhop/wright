# Wright Platform

Welcome to the official documentation for **Wright**, a local-first agent
orchestrator for physical engineering workflows.

Wright is alpha software for developers, MCP porters, demos, and selected beta
feedback. It is bring-your-own-AI: the Docker image does not bundle an LLM, API
key, local model, hosted model, or paid engineering backend. Point
Wright at your own OpenAI-compatible local or hosted endpoint with
`LLM_API_URL`, `LLM_API_KEY`, and `LLM_API_MODEL`.

The fastest first run is the minimal Docker appliance:

```bash
cp docker/.env.example docker/.env
docker compose -f docker-compose.minimal.yml up -d --build
```

Then open:

```text
http://localhost:8080
```

## What Wright Provides Today

- **Agent orchestration**: coordinate LLM-backed agents and deterministic
  engineering tools through a local API and web UI.
- **Build and carry out processes**: edit blocks, typed connections and source;
  use a common or saved AI-created working interface inside a workspace tab.
- **Inspect engineering evidence**: open actual outputs, assumptions, findings
  and review attachments, with links to the producing step and recorded run.
- **Portable instructions and explicit interaction**: retain instruction bodies
  and policy in saved workflows; declare input and review steps that wait durably.
- **Engineering workflow templates**: create editable workspace workflows from
  ten versioned templates with explicit readiness and approval boundaries.
- **MCP tool registry**: catalog, classify, and validate selected engineering
  MCP servers.
- **Flexible AI backends**: use local model servers or hosted
  OpenAI-compatible providers.
- **Local-first operation**: keep workspaces, state, logs, and generated
  artifacts on infrastructure you control.
- **Selected tool integration**: connect CAD, CAE, CAM, PLM, and manufacturing
  software when the required host dependencies, credentials, or licenses are
  explicitly installed for that workflow.

## Alpha Boundaries

This site describes the current source. Published releases can differ. The
[working-view guide](workflows/process-working-interfaces.md) records required
build flags and provider setup. A Codex MCP connection is available for calling
Wright; replacing Wright's Hermes agent runtime with Codex is separate future work.
Digital examples and passing software checks do not establish physical fit,
manufacturing acceptance, supplier approval or qualification of every MCP server.

Wright's base image includes the Wright API, static web UI, Hermes
profile/bootstrap, and general validation tooling. It does not include selected
MCP host software such as FreeCAD, OpenSCAD, CalculiX, Blender, vendor CAD
systems, license managers, GPU drivers, or hardware interfaces.

Engineering MCP validation follows
`docs/mcp-catalog/mcp-server-testing-process.md`: start from a clean container,
install only the selected server's package and testable host dependencies, run
standard protocol probes, and record blocked proprietary or hardware-bound
dependencies instead of baking them into the base image.

## High-Level Flow

```text
Engineers and designers
        |
        v
Wright API and web UI
        |
        +--> Agent adapters and BYO-AI model endpoint
        +--> Hermes integration
        +--> MCP tool registry
        +--> Local workspace files, state, and logs
        |
        v
Selected MCP servers and engineering tools
```

## Start Here

- [Getting Started Overview](getting-started/overview.md)
- [Install Matrix](getting-started/install-matrix.md)
- [Docker Appliance](getting-started/quickstart-docker.md)
- [PC Local Setup](getting-started/quickstart-local.md)
- [GB10 and DGX Workstations](getting-started/workstation-gb10-dgx.md)
- [Existing Hermes Plugin](getting-started/hermes-plugin.md)
- [Engineering Workflow Templates](workflows/engineering-workflow-templates.md)
- [Engineering Workspace Tour](workflows/engineering-workspace-tour.md)
- [Process Working Interfaces](workflows/process-working-interfaces.md)
- [Output Validation](workflows/process-output-validation.md)
