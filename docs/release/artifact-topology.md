# Wright Artifact Topology

Wright has one product version and intentionally separate, jointly mandatory
delivery surfaces.

| Surface | Role | Public identity | Support boundary |
| --- | --- | --- | --- |
| Native Hermes/Python | Complete application wheel: thin Hermes entry point plus isolated runtime extra, packaged API/UI/catalog/gateway | `wright-engineering` | Primary user path; requires released `python-distribution-v1` and full platform lifecycle evidence |
| OCI | Complete local Wright appliance | `ghcr.io/burhop/wright@sha256:<digest>` and byte-identical `burhop/wright:<tag>` | `linux/amd64`; both registries required for a completed release |
| Legacy integration | One-release Git-plugin migration delegate | `burhop/hermes-plugin-wright` mirror | Cannot satisfy native release evidence |

`wright-core`, `wright-tool-registry`, `wright-workspace-service`, `wright-agent-adapters`, `wright-data-vault`, and `wright-api` are private monorepo distributions. They are marked `Private :: Do Not Upload`, are absent from public publication workflows, and must never be resolved from public indexes. The `wright` and `wright-core` names on PyPI belong to other projects.

The root `pyproject.toml` version is authoritative. A release tag, Python metadata, OCI labels/tags, changelog, and release evidence must agree before candidate construction.

## Exact-artifact rule

- Build the complete wheel and sdist once. Record filenames, safe content
  manifests, UI/compatibility/runtime-extra hashes, and SHA-256 hashes. Candidate
  tests, TestPyPI, PyPI, Hermes channel activation, and public native lifecycle
  verification consume those bytes.
- Build the `linux/amd64` OCI candidate once. Record its digest. Smoke, scan, inventory, SBOM, provenance, GHCR promotion, and required Docker Hub distribution consume that digest.
- A retry with the same identity and same subjects may resume. Different subjects require a new patch version.
- A dry-run rehearsal or package-plugin fixture proves local identity and
  ordering only. It is not released-Hermes production evidence.
- Native Hermes and OCI/Docker are both terminal. Neither may be skipped because
  the other passed.
