# Community Release Readiness

## Alpha channels

| Surface | Decision | Status |
| --- | --- | --- |
| Docker Hub | `burhop/wright:<tag>` | Required and digest-verified for every production release |
| GHCR | `ghcr.io/burhop/wright:<tag>` | Required canonical OCI subject |
| PyPI | `wright-engineering` | One complete manager-neutral application distribution |
| Hermes | Production Git adapter plus exact Wright wheel | Primary manager path; Git is the Hermes adapter prerequisite |
| Codex | Direct MCP profile | Supported without Hermes when its profile evidence passes |
| OpenClaw | Future adapter seam | Not supported or release-gated in this delivery |
| Component packages | Not published | Private monorepo implementation surfaces |

## Messaging rules

- Wright is public-alpha, local-first, and bring-your-own-AI.
- Hermes is the primary manager path. It requires Git for its documented plugin
  operation, but Wright runtime commands require no source checkout, Docker, or
  Node/npm.
- Codex connects directly to the same Wright MCP runtime. Its
  prerequisites and configuration stay in their adapters.
- `wright-engineering` contains the one complete application. Manager adapters
  contain only installation or connection projection.
- Docker is the mandatory turnkey path and must publish to GHCR and Docker Hub
  for every production release.
- MCP-specific host software remains outside the base wheel and image.

## Release gate

Before feature-to-`dev`, run `scripts/check-dev-merge.sh`. Before `dev`-to-`main`,
run `scripts/check-prod-merge.sh`. Final evidence must contain exact Wright and
adapter identities, clean platform lifecycle/MCP results, forbidden-executable
audits, and Docker digest/mirror verification before documentation and the
GitHub Release complete.
