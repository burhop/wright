# Wright Artifact Topology

Wright has one product version and three intentionally different delivery surfaces.

| Surface | Role | Public identity | Support boundary |
| --- | --- | --- | --- |
| Python | Lightweight CLI, diagnostics, configuration dry-run, appliance status, and direct MCP STDIO bridge | `wright-engineering` | No appliance runtime or workspace-private dependencies |
| OCI | Complete local Wright appliance | `ghcr.io/burhop/wright@sha256:<digest>` | `linux/amd64`; GHCR canonical |
| Integrations | Codex and optional Hermes packaging | Versioned release assets/packages in their owning features | Consume public CLI/API/MCP contracts only |

`wright-core`, `wright-tool-registry`, `wright-workspace-service`, `wright-agent-adapters`, `wright-data-vault`, and `wright-api` are private monorepo distributions. They are marked `Private :: Do Not Upload`, are absent from public publication workflows, and must never be resolved from public indexes. The `wright` and `wright-core` names on PyPI belong to other projects.

The root `pyproject.toml` version is authoritative. A release tag, Python metadata, OCI labels/tags, changelog, and release evidence must agree before candidate construction.

## Exact-artifact rule

- Build the wheel and sdist once. Record filenames, safe content manifests, and SHA-256 hashes. TestPyPI and PyPI consume those bytes.
- Build the `linux/amd64` OCI candidate once. Record its digest. Smoke, scan, inventory, SBOM, provenance, GHCR promotion, and optional Docker Hub mirror consume that digest.
- A retry with the same identity and same subjects may resume. Different subjects require a new patch version.
- A dry-run rehearsal proves local identity and ordering only. It is not a production release.
