# Versioning Strategy & Policy

Wright adopts [Semantic Versioning (SemVer) 2.0.0](https://semver.org/spec/v2.0.0.html) to manage package versions, API contracts, and container image releases.

## 1. Version Format

Versions are formatted as `vMAJOR.MINOR.PATCH` (e.g. `v0.1.0`):

- **MAJOR**: Signifies breaking API contracts, database schema changes that require migrations, or core runtime architecture shifts.
- **MINOR**: Signifies new feature additions, new tool integrations (e.g. new MCP tool servers), or new agent profile adapter options.
- **PATCH**: Signifies backwards-compatible bug fixes, minor documentation updates, dependency bumps, or chore edits.

*Note on Pre-1.0 Releases*: In the `v0.x.x` lifecycle, the project is in active bootstrap development. Minor versions may introduce breaking changes, and patch versions signify incremental feature additions and bug fixes.

---

## 2. Version Source of Truth

To ensure absolute consistency, the version version source of truth is declared in:
- **Python Manifest**: The `version` field in the root `pyproject.toml` file.

All Git release tags and Docker Hub container registry tags must stay in sync with this version number.

---

## 3. Automated Release Lifecycle

Wright automates package builds and image publication:

1. **Tag Push**: Pushing a tag matching `v*` (e.g. `v0.1.0`) triggers the Automated Release workflow.
2. **Build and Tag**: The workflow builds the container image and tags it with both the version tag (e.g. `v0.1.0`) and `latest` tag.
3. **Publishing**: The tagged container is pushed to Docker Hub, and a GitHub Release is published containing draft notes categorized by PR labels.
