# Production Image Dependency Inventory

Feature 047 validates one `linux/amd64` appliance. Multi-architecture indexes are not a support claim.

| Input | Pin | Verification/update rule |
| --- | --- | --- |
| Node web builder | `node:24.17.0-slim@sha256:862263c...` | Node 24 LTS; resolve the official index digest and rerun frontend plus exact-image smoke before updating. |
| Python/Hermes base | `python:3.13.11-slim@sha256:2b9c980...` | Official image index; validate amd64 manifest, Python runtime, API/Hermes smoke, scan, and licenses. |
| uv binary | `ghcr.io/astral-sh/uv:0.9.26@sha256:9a23023...` | Official Astral image index; copy only `/uv`; verify version in image inventory. |
| micromamba | `2.5.0`, SHA-256 `cec496f2...103b6` | Download the versioned linux-64 archive and fail the build on checksum or architecture mismatch. |
| Python workspace | committed `uv.lock` | `uv sync` must use the lock and dependency audit must pass. |
| Hermes runtime patches | exact versions in `docker/Dockerfile` | Changes require vulnerability-policy and Hermes smoke evidence. |

The Dockerfile contains no `apt-get upgrade`, moving `latest` input, or unchecked binary download. Release workflows build the candidate once, store its digest, and direct all smoke, scan, SBOM, provenance, tag promotion, and optional mirror verification at that digest.

Rebuild comparison is diagnostic: repeat builds may differ because upstream package repositories and timestamps are not yet fully hermetic. Release identity is established by testing and promoting the first immutable digest, never by rebuilding and assuming equality.
