# Community Release Readiness

This page records the public-alpha release posture for Wright. It keeps install, package, container, visibility, and funding decisions in one place so public surfaces stay consistent.

## Alpha Channels

| Surface | Alpha decision | Status |
| --- | --- | --- |
| Docker Hub | `burhop/wright:<tag>` | Enabled for alpha releases when Docker Hub secrets are present. |
| GHCR | `ghcr.io/burhop/wright:<tag>` | Enabled by the release workflow. |
| PyPI | `wright-engineering` | Single alpha helper package. |
| Component packages | Not published for alpha | Existing package names collide or need a dependency plan. |
| Contact | `wright@makerengineer.com` | Public support and partner contact. |
| Sponsorship | GitHub Sponsors for `burhop` | Active. Organization/fiscal host deferred. |

## Messaging Rules

- Wright is public-alpha software for testing, MCP porting, demos, and selected beta feedback.
- Wright is local-first and bring-your-own-AI. Public artifacts must not imply bundled LLMs, provider credentials, model weights, hosted services, proprietary engineering tools, or paid backends.
- Docker is the primary end-user install path for alpha.
- `wright-engineering` is a lightweight Python helper and discovery package, not the full appliance.
- MCP-specific host software stays out of the base image unless a separate validated feature changes that boundary.
- NVIDIA Inception and organization/fiscal-host funding are deferred until Wright has an eligible company, organization, or fiscal host.

## Release Gate

Before merging this feature branch to `dev`, run `scripts/check-dev-merge.sh` or document the specific local host limitation that prevented the gate. Before merging `dev` to `main`, run `scripts/check-prod-merge.sh`.
