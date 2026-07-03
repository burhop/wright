# Alpha Release Notes Template

Use this template when cutting an alpha, beta, or release-candidate tag such as
`v0.1.0-alpha.1`. Public prereleases must be explicit about what was tested,
what was skipped, and what operators still need to provide.

## Summary

Wright `<tag>` is alpha software for developers, MCP porters, demo users, and
selected testers. Wright is bring-your-own-AI: this release does not bundle an
LLM, model weights, hosted provider account, API key, paid engineering backend,
or MCP-specific host software.

## Images

- GHCR: `ghcr.io/burhop/wright:<tag>`
- Docker Hub: `burhop/wright:<tag>` or `not published for
  this tag`
- `latest` updated: `yes` for stable tags only; `no` for alpha, beta, and
  release-candidate tags

## Verification

- Source tag: `<tag>`
- Commit SHA: `<sha>`
- Python tests: `<command and result>`
- Frontend tests: `<command and result>`
- Frontend production build: `<command and result>`
- MkDocs strict build: `<command and result>`
- Public-alpha leak scan: `<command and result>`
- Docker appliance smoke test: `<image, architecture, command, and result>`
- History secret scan: `<tool, date, and result>`
- SBOM/provenance: `<published attestation link>` or `deferred for this alpha;
  no SBOM/provenance attestation is published`

## Architecture and Runtime Status

- `linux/amd64`: `<built/smoked/not tested>`
- `linux/arm64`: `<built/smoked/not tested>`
- CUDA/GPU passthrough: `<tested assumptions>` or `not tested`
- NVIDIA Container Toolkit / `--gpus all`: `<tested assumptions>` or
  `documented only`
- Local model server path: `<tested provider/server>` or `not tested`
- Hosted model provider path: `<tested provider>` or `not tested`

## MCP Validation

- Fully validated MCP servers: `<list or none>`
- Dependency-missing or credential-missing MCP servers: `<list or none>`
- Skipped MCP validation: `<reason and link to follow-up>`
- Clean-container process used:
  `docs/mcp-catalog/mcp-server-testing-process.md`

## Known Limitations

- Wright is not production-ready.
- Users must configure their own LLM endpoint.
- Selected MCP host dependencies are installed and validated per server.
- Paid, proprietary, unsafe, hardware-bound, or credential-bound backends are not
  bundled in the base image.
- Hermes Desktop Linux container images, CUDA image variants, and broad
  multi-architecture smoke coverage remain follow-up work unless explicitly
  listed as tested above.

## Upgrade and Rollback Notes

- Upgrade path: `<commands or not applicable>`
- Rollback path: `<commands or not applicable>`
- Breaking changes since the previous public tag: `<list or none>`

## Links

- Release checklist: `docs/public-launch-checklist.md`
- Version policy: `docs/versioning.md`
- Docker quickstart: `docs/getting-started/quickstart-docker.md`
- Install paths: `docs/getting-started/overview.md`
