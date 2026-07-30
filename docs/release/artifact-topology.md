# Wright Artifact Topology

Wright has one product version and separate, jointly required delivery surfaces.

| Surface | Role | Public identity | Release evidence |
| --- | --- | --- | --- |
| Wright runtime | Complete manager-neutral application, UI, catalog, gateway, lifecycle, and MCP profiles | `wright-engineering` wheel/sdist | Exact filename, SHA-256, runtime lock, clean install, and lifecycle |
| Hermes adapter | Standard-library-only projection from Hermes' real Git plugin interface to Wright lifecycle | `burhop/hermes-plugin-wright` Git commit | Released Hermes version, mirror commit and provenance, install/update/remove, `/wright` lifecycle |
| Codex adapter | Direct STDIO or Streamable HTTP MCP profile | Versioned Wright profile at the release commit | Profile identity and MCP initialize/list/call |
| OCI appliance | Turnkey local Wright appliance | `ghcr.io/burhop/wright@sha256:<digest>` and `burhop/wright:<tag>` | Same tested manifest digest in both registries |

`wright-core`, `wright-tool-registry`, `wright-workspace-service`,
`wright-agent-adapters`, `wright-data-vault`, and `wright-api` are private
monorepo distributions. They are not resolved from public indexes. The `wright`
and `wright-core` names on PyPI belong to other projects.

## Exact-subject rule

- Build the public wheel and sdist once and retain their content manifests and
  hashes through TestPyPI, PyPI, and native manager verification.
- Verify the Hermes mirror's installed Git commit and provenance source commit
  before running Wright. Hermes does not select a Git ref, so post-clone
  identity verification is mandatory.
- Codex evidence names the Wright release commit and verifies the
  direct MCP contract without Hermes.
- Build the OCI candidate once; GHCR and Docker Hub must resolve to that tested
  digest.
- A retry may resume only with identical subjects. A different subject requires
  a new patch version.
- Native manager paths and Docker are both terminal release requirements.
