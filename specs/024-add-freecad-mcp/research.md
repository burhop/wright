# Research: FreeCAD MCP Server Integration

## Findings & Decisions

### 1. FreeCAD Installation on Host (GB10)
- **Decision**: Install FreeCAD 1.1+ on the GB10 host via the snap package manager (`sudo snap install freecad`).
- **Rationale**: The native `.deb` package is not available for the `arm64` (aarch64) architecture in standard Ubuntu 24.04 repositories, and the official stable PPA (`ppa:freecad-maintainers/freecad-stable`) does not package `arm64` binaries for Ubuntu Noble (24.04) or Resolute (26.04). Snap officially supports `arm64` and provides the headless command-line interface executable `/snap/bin/freecad.cmd` out of the box.
- **Alternatives Considered**: 
  - *PPA Repository*: Rejected because it returns 404 (no release files) for the `arm64` architecture.
  - *Compiling from Source*: Rejected because it requires 1–3 hours of compile time and complex dependency chains.
  - *AppImage*: Evaluated but snap is preferred for native system-wide package updates on the host.

### 2. FreeCAD Installation in Docker Container
- **Decision**: Download the official `FreeCAD_1.0.0-conda-Linux-aarch64-py311.AppImage` release in `docker/Dockerfile`, make it executable, extract it via `--appimage-extract` into `/opt/freecad`, and symlink `/opt/freecad/usr/bin/freecadcmd` to `/usr/local/bin/freecadcmd` and `/usr/local/bin/freecad` respectively.
- **Rationale**: The Docker container is running `ubuntu:26.04` (arm64) and does not support nested `snapd` easily. Since the Ubuntu 26.04 package index also lacks `freecad` binaries for `arm64` (resulting in `Candidate: (none)`), downloading the self-contained official AppImage and extracting it is the cleanest, most reliable way to ship FreeCAD in the container without mounting FUSE devices.
- **Alternatives Considered**:
  - *Conda/Mamba*: Micromamba is installed, but `conda-forge::freecad` packages pulls in heavy Python/C/C++ dependencies that conflict with the image's existing Python 3.13 venv layout.

### 3. Server Startup & Command Resolution
- **Decision**: Configure the Tool Registry's catalog entry with the stdio command `["uvx", "freecad-mcp"]` (seeded in the database). When starting up the MCP server, we will set the `FREECAD_PATH` environment variable to `/snap/bin/freecad.cmd` on the host, and `/usr/local/bin/freecadcmd` in the Docker container.
- **Rationale**: `freecad-mcp` is hosted on PyPI and can be executed dynamically via `uvx`. Setting the `FREECAD_PATH` points the server to the correct headless executable, bypassing GUI dependencies.
