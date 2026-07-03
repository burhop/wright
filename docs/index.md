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
        +--> Local workspace, data vault, and logs
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
