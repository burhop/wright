# Platform Overview

Wright is a local-first engineering workspace and provider-neutral MCP control
plane. It is alpha software and bring-your-own-AI: model endpoints,
credentials, licensed tools, and MCP-specific host software stay under operator
control. Wright does not bundle an LLM.

## Choose Your Alpha Path

| Path | Intended user | Status |
| --- | --- | --- |
| [Native Hermes](hermes-plugin.md) | Most Wright users | Primary manager path. Git is required by Hermes for plugin installation; Wright needs no checkout, Docker, or Node/npm. |
| [Codex](codex.md) | Codex users and coding agents | Direct MCP connection to the same Wright runtime; Hermes is not involved. |
| OpenClaw | Future integration | Not part of the current supported installation or release gate. |
| [Docker appliance](quickstart-docker.md) | Turnkey trial or third-party evaluator | Mandatory published path for every production release. |
| [PC development](quickstart-local.md) | Contributors changing Wright | Source checkout and developer tools required. |
| [GB10/DGX workstation](workstation-gb10-dgx.md) | GPU-backed engineering work | Follow host, model, and selected-MCP prerequisites. |

The public `wright-engineering` distribution contains the complete application
runtime. Manager adapters only install or connect to it. Internal component
packages are not public installation choices.

## Shared native runtime

All native manager paths use one Wright-owned root, `WRIGHT_HOME` (default
`~/.wright`). Versioned runtime code is stored below `WRIGHT_HOME/runtimes` and
retained data below `WRIGHT_HOME/data`. No manager owns those paths.

`/wright uninstall` removes managed runtime code but preserves data. `/wright
purge` is separate, previews the exact Wright-owned path, and requires the
generated confirmation code. External workspaces and unrelated Hermes, Codex,
or OpenClaw files are never purge targets.

## MCP boundary

Hermes and Codex reach the same provider-neutral Wright MCP service. OpenClaw
integration is future work and is not claimed by this release.
Wright packages do not acquire CAD/CAE/CAM applications merely because a catalog
entry exists. Install and validate selected MCP host dependencies separately
using the [MCP server testing process](../mcp-catalog/mcp-server-testing-process.md).
