# Research: Release Engineering & Versioning

**Branch**: `015-release-engineering` | **Date**: 2026-06-05

## Technical Decisions & Rationale

### 1. Semantic Versioning starting at `v0.1.0`
* **Decision**: Adopt Semantic Versioning (MAJOR.MINOR.PATCH) format. The source of truth for the codebase version will reside in the `version` field of `pyproject.toml` in the repository root.
* **Rationale**:
  - Semantic Versioning is the industry standard, providing clear rules on breaking changes (MAJOR), additions (MINOR), and bug fixes (PATCH).
  - Pinned versions in `pyproject.toml` provide programmatic access to the version number for backend logging, health reports, and system audits.
* **Alternatives Considered**:
  - *CalVer (Calendar Versioning)*: Standard for SaaS apps, but SemVer is more appropriate for developer toolkits where breaking API changes need to be signaled clearly.

### 2. Changelog Structure (Keep a Changelog)
* **Decision**: Implement a root `CHANGELOG.md` following the "Keep a Changelog" formatting style.
* **Rationale**:
  - Restricts changelogs to human-readable summaries rather than git commit dumps.
  - Groups changes under clear action headers (Added, Changed, Fixed, etc.) and provides anchors to specific tag comparisons.
  - Backfilling previous features (001-010) preserves history and highlights platform progress.

### 3. Release Drafting Automation (Release Drafter)
* **Decision**: Use `release-drafter/release-drafter` to automatically maintain a GitHub release draft as PRs are merged.
* **Rationale**:
  - Eliminates the manual burden of compiling release notes on milestones.
  - Grouping by labels (e.g. `feature` -> Added, `bugfix` -> Fixed) maps perfectly to the Keep a Changelog categories.
* **Alternatives Considered**:
  - *GitHub Native Release Generator*: Less customizable and doesn't update draft notes incrementally.

### 4. Continuous Integration Tag-Driven Releases
* **Decision**: Create a tag-triggered GHA workflow (`release.yml`) that validates the Git tag against `v[0-9]+\.[0-9]+\.[0-9]+` schema, builds the Docker image, tags it as `<tag>` and `latest`, and pushes it to Docker Hub, while publishing the draft GitHub release.
* **Rationale**:
  - Enforces automated gating and quality checks (requires tags to be pushed to run).
  - Automates release deployment.
