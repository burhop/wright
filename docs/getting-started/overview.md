# Platform Overview

Wright is a local-first engineering workspace and provider-neutral MCP control
plane. Wright is alpha software and bring-your-own-AI. It does not bundle an
LLM: model endpoints, credentials, licensed tools, and MCP-specific host
software stay under operator control.

## Choose Your Alpha Path

| Path | Intended user | Status |
| --- | --- | --- |
| [Native Hermes](hermes-plugin.md) | The normal Wright user; no Git, Docker, Node/npm, checkout, or manual Python commands | Primary design. Public release is blocked until released Hermes provides `python-distribution-v1`. |
| [Docker appliance](quickstart-docker.md) | A turnkey, working appliance with no local build | Mandatory published path for every production release. |
| [PC development](quickstart-local.md) | Contributors changing API, UI, packaging, tests, or docs | Source checkout and developer tools required. |
| [GB10/DGX workstation](workstation-gb10-dgx.md) | Local-model and GPU-backed engineering work | Follow host/model/MCP-specific prerequisites. |

The public `wright-engineering` Python distribution is the complete application
artifact consumed by Hermes. Users do not install it manually as a separate
helper. Private component packages and the legacy Git-plugin mirror are not
public installation choices.

## Native runtime model

Hermes loads only the dependency-light `wright` entry point. `/wright start`
resolves the exact approved `wright-engineering[runtime]` artifact into
`HERMES_HOME/wright/runtimes/<runtime-id>`, starts one identity-challenged local
API/UI process, and retains user data under `HERMES_HOME/wright/data`.

`/wright uninstall` removes managed runtime code but preserves that data.
`/wright purge` is separate, previews the exact Wright-owned path, and requires
the generated confirmation code. External workspaces and unrelated Hermes files
are never purge targets.

## MCP boundary

Wright's catalog and gateway remain provider-neutral. Native and Docker packages
do not acquire CAD/CAE/CAM applications merely because a catalog entry exists.
Install and validate selected MCP host dependencies separately using the
[MCP server testing process](../mcp-catalog/mcp-server-testing-process.md).
