# Feature Brief: Release Engineering & Versioning

Establish a formal versioning strategy, automated release workflow, and changelog management so that Wright has predictable, well-documented releases that users and contributors can depend on. This is how the community knows the project is alive, maintained, and production-ready.

## What to build

### Versioning Strategy

1. **Semantic Versioning adoption** — Adopt SemVer (MAJOR.MINOR.PATCH) starting at `v0.1.0`:
   - MAJOR: Breaking API changes or architectural shifts
   - MINOR: New features, new MCP tools, new agent adapters
   - PATCH: Bug fixes, documentation improvements, dependency updates
   - Pre-1.0: All changes are considered potentially breaking (standard SemVer convention)
   - Document the versioning policy in a `docs/versioning.md` or as a section in CONTRIBUTING.md

2. **Version source of truth** — Define where the version number lives:
   - Python: `pyproject.toml` version field
   - Docker: image tag (e.g., `burhop/wright:v0.1.0`)
   - Git: annotated tags (e.g., `v0.1.0`)
   - All three must stay in sync via the release workflow

### Changelog

3. **CHANGELOG.md** — Create an initial changelog following the [Keep a Changelog](https://keepachangelog.com/) format:
   - Organize by version with date (e.g., `## [0.1.0] - 2026-06-xx`)
   - Categories: Added, Changed, Deprecated, Removed, Fixed, Security
   - Back-fill notable changes from the existing git history (features 001–010)
   - Include a link at the top explaining the format and SemVer adherence

### Release Automation

4. **Release workflow** (`.github/workflows/release.yml`) — A GitHub Actions workflow triggered when a version tag is pushed (e.g., `v0.1.0`):
   - Validate the tag matches SemVer format
   - Build the Docker image and tag with the version number (e.g., `burhop/wright:v0.1.0` AND `burhop/wright:latest`)
   - Create a GitHub Release with:
     - Auto-generated release notes from merged PRs since last tag
     - The relevant CHANGELOG.md section
     - Links to the Docker Hub image
   - Push the versioned Docker image to Docker Hub

5. **Release drafter** (`.github/workflows/release-drafter.yml` or `.github/release-drafter.yml`) — Automatically draft release notes as PRs are merged:
   - Categorize PRs by label (feature, bugfix, documentation, dependency, breaking change)
   - Use a template that groups changes into sections matching the CHANGELOG format
   - The draft is updated on every PR merge but only published manually or when a tag is pushed

### Tagging the First Release

6. **Initial release** — Tag the current state of the `main` branch as `v0.1.0`:
   - Create an annotated git tag: `git tag -a v0.1.0 -m "Initial release: Wright AI mechanical engineering platform"`
   - The GitHub Release should summarize the current capabilities:
     - FastAPI backend with agent adapters
     - Vite web frontend with engineering workspace UI
     - Hermes LLM integration
     - 34 MCP engineering tool servers
     - Docker production image with CI/CD
     - Backup/restore scripts
   - Document the release process so future releases are repeatable

### Docker Image Versioning

7. **Versioned Docker tags** — Update the existing `docker-build.yml` workflow to:
   - On version tag push: tag the image as `burhop/wright:vX.Y.Z` and `burhop/wright:latest`
   - On `main` push: tag as `burhop/wright:latest`
   - On `dev` push: tag as `burhop/wright:dev`
   - On PR: build but do not push (validation only)
   - Include the version number as a Docker LABEL in the image

## Constraints

- Do not modify any application source code
- The release workflow must not auto-deploy — it only builds, tags, and publishes artifacts
- The first release (v0.1.0) should represent the current state honestly — do not imply production-readiness if features are still in development
- Release drafter must not create noise — drafts are invisible until published
- The existing docker-build.yml should be extended, not replaced, for the versioned tagging
- All workflows must use pinned action versions for security
