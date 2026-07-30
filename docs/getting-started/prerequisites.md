# Prerequisites

Wright's runtime is manager-neutral. Each manager adapter owns its own small set
of prerequisites.

## Hermes

- A released Hermes version satisfying the packaged compatibility contract.
- Git, because `hermes plugins install`, `update`, and `remove` use Hermes' Git
  plugin interface.
- Network access to the adapter repository and PyPI for first install/update.

After the adapter is installed, Wright lifecycle commands do not invoke Git,
Docker, Node.js, npm, uv, or a source checkout. A complete verified cache can be
used offline; missing or mismatched artifacts fail before activation.

## Codex

- Codex with MCP server support.
- An installed `wright-engineering[runtime]` command or a running Wright HTTP
  service.

Codex connects directly over STDIO or Streamable HTTP. Hermes and Git are not
Codex runtime prerequisites.

## OpenClaw

OpenClaw integration is future work. It is not a prerequisite, supported
installation path, or release gate for this version of Wright.

## Supported platform evidence

Public native support is claimed only after clean evidence passes on Windows 11
x64, Ubuntu 22.04/24.04 x64, and macOS Sonoma 14+ on each recorded x64 or arm64
runner where Wright and the chosen manager both claim support.

## Docker appliance

- Docker Engine 24+ or Docker Desktop with Compose v2.20+.
- 4 CPU cores, 16 GB RAM, and 20 GB free disk as an alpha baseline.
- Network access for the image registry and configured model/MCP endpoints.

Docker is a mandatory turnkey release artifact even though native managers are
supported.

## Contributors and external engineering tools

Source development additionally uses Git, Python 3.11-3.14, uv, Node.js 22,
npm, and Docker. FreeCAD, OpenSCAD, CalculiX, Blender, vendor CAD systems,
license managers, drivers, credentials, and hardware remain selected-MCP
prerequisites; they are not part of the base native runtime or Docker image.
