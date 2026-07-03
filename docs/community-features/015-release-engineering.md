# Feature Brief: Release Engineering & Versioning

Establish a release process that makes Wright's public alpha predictable,
traceable, and honest about its current limits. The goal is not to imply
production readiness; the goal is to make every alpha tag reproducible,
pre-release marked, and clear about what was tested.

## What to build

### Versioning Strategy

1. **Semantic Versioning adoption** - Adopt SemVer tags starting at `v0.1.0`:
   - MAJOR: Breaking API, storage, or runtime architecture changes.
   - MINOR: New features, new MCP tool integrations, or new adapter options.
   - PATCH: Bug fixes, documentation improvements, dependency updates, and
     alpha hardening.
   - Pre-1.0: Minor and patch versions may still introduce breaking changes.
   - Alpha, beta, and release-candidate tags use suffixes such as
     `v0.1.0-alpha.1`, `v0.1.0-beta.1`, and `v0.1.0-rc.1`.

2. **Version source of truth** - Keep the version number aligned across:
   - Python: root `pyproject.toml`.
   - Git: annotated tags such as `v0.1.0-alpha.1`.
   - Containers: GHCR and optional Docker Hub image tags.

### Changelog and Release Notes

3. **Release notes discipline** - Public alpha notes must include:
   - Generated PR summary from release-drafter.
   - Docker image names and tags.
   - Test commands and Docker smoke result.
   - Architecture status for `linux/amd64` and `linux/arm64`.
   - SBOM/provenance status, published or explicitly deferred.
   - Skipped MCP validation and links to follow-up records.
   - A clear statement that Wright is alpha and bring-your-own-AI.

Use `docs/alpha-release-notes-template.md` before publishing an alpha,
beta, or release-candidate tag.

### Release Automation

4. **Release workflow** (`.github/workflows/release.yml`) - A tag matching `v*`
   triggers the publishing workflow:
   - Build the Docker image with OCI version, revision, and created labels.
   - Push `ghcr.io/<owner>/wright:<tag>` using GitHub Packages.
   - Push `burhop/wright:<tag>` only when
     `DOCKERHUB_USERNAME` and `DOCKERHUB_TOKEN` are configured.
   - Mark alpha, beta, and release-candidate tags as GitHub prereleases.
   - Apply `latest` only for stable tags. Prerelease tags must not move
     `latest`.
   - Sync the Docker Hub description only when Docker Hub credentials exist.

5. **Release drafter** (`.github/workflows/release-drafter.yml`) - Keep draft
   notes updated as PRs merge:
   - Categorize PRs by labels such as `feature`, `bug`, `docs`, `maintenance`,
     `dependency`, and `breaking`.
   - Keep drafts unpublished until a maintainer cuts or reviews the release.

### First Public Alpha

6. **Initial alpha release** - The first public tag should be an alpha tag such
   as `v0.1.0-alpha.1`, not a stable production release:
   - Create an annotated tag from the reviewed release branch.
   - Confirm README, Docker docs, install paths, and issue templates match the
     alpha/BYO-AI contract.
   - Run the public repository launch checklist.
   - Publish release notes from `docs/alpha-release-notes-template.md`.

### Docker Image Versioning

7. **Container tag policy** - Keep image tags explicit:
   - Version tags are immutable release records.
   - SHA tags identify the exact source revision where emitted.
   - latest is stable-only.
   - Branch push workflows build and smoke-test images but do not publish public
     registry images.

## Constraints

- Do not imply production readiness for public alpha releases.
- Do not claim Wright bundles an LLM, hosted provider account, API key, paid
  engineering backend, or MCP-specific host software.
- GHCR must remain publishable without Docker Hub secrets.
- Docker Hub publishing must remain optional.
- Release automation must not deploy beyond publishing release artifacts.
- Release notes must name manual gates, skipped validation, and known limits.
