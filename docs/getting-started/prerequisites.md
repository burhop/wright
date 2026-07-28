# Prerequisites

Wright has two production distribution paths with different prerequisites.

## Native Hermes user

The native path requires only a released Hermes version named by Wright's
compatibility contract and a supported Python runtime managed by Hermes. Wright
itself must not require the user to install Git, Docker, Node.js, npm, uv, clone
a repository, set `WRIGHT_REPO_DIR`, or run a Python package command.

Public support begins only after clean production evidence passes on the exact
platform and architecture. The intended matrix is Windows 11 x64, Ubuntu
22.04/24.04 x64, and macOS Sonoma 14+ on recorded x64/arm64 runners where both
Hermes and Wright claim support. At present no released Hermes version has the
required `python-distribution-v1`, so native production availability is false.

Online install/update needs access to the approved Python package index. Offline
start can use a complete previously verified cache; an incomplete cache fails
before activation.

## Docker appliance user

- Docker Engine 24+ or Docker Desktop with Compose v2.20+.
- 4 CPU cores, 16 GB RAM, and 20 GB free disk as a practical alpha baseline.
- Network access for the selected image registry and any configured model/MCP
  endpoints.

Docker remains a mandatory turnkey release artifact even after native Hermes is
available.

## Contributor

Source development additionally uses Git, Python 3.11-3.14, uv, Node.js 22,
npm, and Docker for container gates. These are contributor tools, not native
user prerequisites. See [CONTRIBUTING.md](https://github.com/burhop/wright/blob/main/CONTRIBUTING.md).

## External engineering tools

FreeCAD, OpenSCAD, CalculiX, Blender, vendor CAD systems, license managers,
drivers, credentials, and hardware remain selected-MCP prerequisites. They are
not part of the base native runtime or Docker image.
