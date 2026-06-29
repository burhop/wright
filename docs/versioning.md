# Versioning Strategy & Policy

Wright adopts [Semantic Versioning (SemVer) 2.0.0](https://semver.org/spec/v2.0.0.html) to manage package versions, API contracts, and container image releases.

## 1. Version Format

Stable versions are formatted as `vMAJOR.MINOR.PATCH` (e.g. `v0.1.0`):

- **MAJOR**: Signifies breaking API contracts, database schema changes that require migrations, or core runtime architecture shifts.
- **MINOR**: Signifies new feature additions, new tool integrations (e.g. new MCP tool servers), or new agent profile adapter options.
- **PATCH**: Signifies backwards-compatible bug fixes, minor documentation updates, dependency bumps, or chore edits.

Alpha, beta, and release-candidate builds use SemVer prerelease suffixes, for
example:

- `v0.1.0-alpha.1`
- `v0.1.0-beta.1`
- `v0.1.0-rc.1`

*Note on Pre-1.0 Releases*: In the `v0.x.x` lifecycle, the project is in active bootstrap development. Minor versions may introduce breaking changes, and patch versions signify incremental feature additions and bug fixes.

---

## 2. Version Source of Truth

To ensure absolute consistency, the version version source of truth is declared in:
- **Python Manifest**: The `version` field in the root `pyproject.toml` file.

All Git release tags and Docker Hub container registry tags must stay in sync with this version number.

---

## 3. Automated Release Lifecycle

Wright automates package builds and image publication:

1. **Tag Push**: Pushing a tag matching `v*` (e.g. `v0.1.0` or `v0.1.0-alpha.1`) triggers the Automated Release workflow.
2. **Build and Tag**: The workflow builds the container image and tags it with the exact version tag.
3. **Latest Policy**: Stable tags also update `latest`. Prerelease tags containing `-alpha`, `-beta`, or `-rc` do not update `latest`.
4. **Publishing**: The tagged container is pushed to Docker Hub, and a GitHub Release is published containing generated notes. Prerelease tags are marked as GitHub prereleases.

Alpha releases must continue to state that Wright is alpha and bring-your-own-AI.
They should include known manual gates, untested architectures, Docker smoke
results, and any skipped MCP validation.
