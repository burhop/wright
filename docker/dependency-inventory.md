# Production Image Dependency Inventory

Feature 047 validates one `linux/amd64` appliance. Multi-architecture indexes are not a support claim.

| Input | Pin | Verification/update rule |
| --- | --- | --- |
| Node web builder | `node:24.17.0-slim@sha256:862263c...` | Node 24 LTS; resolve the official index digest and rerun frontend plus exact-image smoke before updating. |
| Python/Hermes base | `python:3.13.13-slim@sha256:aa938a8...` | Official image index; Hermes 0.19.0 supports Python 3.11-3.13; validate amd64 manifest, Python runtime, API/Hermes smoke, scan, and licenses. |
| Hermes Agent | `0.19.0` | Install into `/opt/hermes/.venv`; require the standard Wright plugin lifecycle, direct gateway health, and final `uv pip check`. |
| uv binary | `ghcr.io/astral-sh/uv:0.9.26@sha256:9a23023...` | Official Astral image index; copy only `/uv`; verify version in image inventory. |
| micromamba | `2.5.0`, SHA-256 `cec496f2...103b6` | Download the versioned linux-64 archive and fail the build on checksum or architecture mismatch. |
| Python workspace | committed `uv.lock` | `uv sync` must use the lock and dependency audit must pass. |
| Hermes runtime patches | exact non-conflicting versions in `docker/Dockerfile` | Do not replace Hermes' exact `cryptography` or Pillow requirements independently. Changes require `uv pip check`, vulnerability-policy, and Hermes smoke evidence. |

The Dockerfile contains no `apt-get upgrade`, moving `latest` input, or unchecked binary download. Release workflows build the candidate once, store its digest, and direct all smoke, scan, SBOM, provenance, tag promotion, and optional mirror verification at that digest.

Rebuild comparison is diagnostic: repeat builds may differ because upstream package repositories and timestamps are not yet fully hermetic. Release identity is established by testing and promoting the first immutable digest, never by rebuilding and assuming equality.
