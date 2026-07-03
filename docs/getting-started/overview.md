# Platform Overview

Wright is a modular agent orchestration platform for local-first product design,
CAD manipulation, structural engineering, manufacturing setup, and MCP server
validation.

Wright is alpha software and bring-your-own-AI. It does not bundle an LLM, API
key, local model, hosted model, or paid engineering backend. Choose the run path
that matches what you already have, then configure model providers and selected
MCP host dependencies explicitly.

## Choose Your Alpha Path

| Path | Best for | Start here |
| --- | --- | --- |
| Install matrix | Choose the correct alpha path by use case | [Install Matrix](install-matrix.md) |
| Docker appliance | Fastest public-alpha trial, demos, and MCP porting from a clean container | [Quick Start: Docker Appliance](quickstart-docker.md) |
| PC local setup | Editing the API, UI, plugin, docs, or tests on a normal development PC | [Quick Start: PC Local Setup](quickstart-local.md) |
| GB10/DGX workstation | Running Wright beside a local model server or GPU-backed engineering tools | [Quick Start: GB10 and DGX Workstations](workstation-gb10-dgx.md) |
| Existing Hermes plugin | Hermes Desktop or CLI users who want `/wright` commands first | [Quick Start: Existing Hermes Plugin](hermes-plugin.md) |

## Current Appliance Model

The Docker appliance runs the Wright API, static web UI, Hermes
profile/bootstrap, and general validation tooling. It is a control plane for
selected tools, not a sealed image that already contains every CAD, CAE, CAM,
PLM, AI, or hardware integration.

Selected MCP dependencies are installed and validated per server:

1. Start from a clean Wright container.
2. Read the server catalog metadata.
3. Install only the selected MCP package and testable free/open host
   dependencies needed for a safe probe.
4. Record proprietary, license-bound, credential-bound, or hardware-bound gaps
   as blocked follow-up work.

MCP-specific host software such as FreeCAD, OpenSCAD, CalculiX, Blender, vendor
CAD systems, license managers, and GPU drivers is outside the base-image
contract unless it is required for the selected server being validated or used.

## Core Workflows

```text
1. Define spec
   |
   v
2. Plan and run an agent workflow
   |
   v
3. Actuate selected MCP tools
   |
   v
4. Review generated artifacts and logs
   |
   v
5. Commit or revise the local workspace
```

Typical alpha workflows include:

- Drafting requirements and implementation plans with Spec Kit.
- Connecting Wright to a local or hosted OpenAI-compatible model endpoint.
- Testing the Docker appliance on `http://localhost:8080`.
- Validating a selected MCP server from a clean container.
- Recording MCP setup recipes and follow-up records for missing dependencies.

See the Docker, local setup, workstation, and Hermes plugin quickstarts for the
supported first-run commands.
