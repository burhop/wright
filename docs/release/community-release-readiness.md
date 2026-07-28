# Community Release Readiness

This page records the public-alpha release posture for Wright. It keeps install, package, container, visibility, and funding decisions in one place so public surfaces stay consistent.

## Alpha Channels

| Surface | Alpha decision | Status |
| --- | --- | --- |
| Docker Hub | `burhop/wright:<tag>` | Required, protected, and digest-verified for every production release. |
| GHCR | `ghcr.io/burhop/wright:<tag>` | Enabled by the release workflow. |
| PyPI | `wright-engineering` | Single complete application distribution used by Hermes and its isolated runtime. |
| Native Hermes | Exact `wright-engineering` package through `python-distribution-v1` | Primary user path; production blocked until a released compatible Hermes exists. |
| Component packages | Not published for alpha | Existing package names collide or need a dependency plan. |
| Contact | `wright@makerengineer.com` | Public support and partner contact. |
| Sponsorship | GitHub Sponsors for `burhop` | Active. Organization/fiscal host deferred. |

## Messaging Rules

- Wright is public-alpha software for testing, MCP porting, demos, and selected beta feedback.
- Wright is local-first and bring-your-own-AI. Public artifacts must not imply bundled LLMs, provider credentials, model weights, hosted services, proprietary engineering tools, or paid backends.
- Native Hermes is the primary user design and requires no Git, Docker,
  Node/npm, checkout, `WRIGHT_REPO_DIR`, or manual Python package commands.
- `wright-engineering` is the one complete public application distribution:
  thin Hermes entry point plus the same exact distribution's isolated `runtime`
  extra, packaged API/UI, canonical catalog, and provider-neutral gateway.
- Docker is the mandatory turnkey path and must publish to GHCR and Docker Hub
  for every production release even after native Hermes is available.
- The legacy `hermes-plugin-wright` Git mirror and internal `wright-*` component
  packages are migration/development surfaces, not alternate public installs.
- MCP-specific host software stays out of the base image unless a separate validated feature changes that boundary.
- NVIDIA Inception and organization/fiscal-host funding are deferred until Wright has an eligible company, organization, or fiscal host.

## Release Gate

Before merging this feature branch to `dev`, run `scripts/check-dev-merge.sh` or document the specific local host limitation that prevented the gate. Before merging `dev` to `main`, run `scripts/check-prod-merge.sh`.

The production gate has no native skip. Final evidence must contain a released
Hermes capability/version, exact wheel and runtime-extra identities, clean
platform lifecycle results, stable-channel activation, and mandatory Docker
digest/mirror verification before docs and GitHub Release.
