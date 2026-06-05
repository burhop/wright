# Feature Specification: Release Engineering & Versioning

**Feature Branch**: `015-release-engineering`

**Created**: 2026-06-05

**Status**: Draft

**Input**: User description: "Built the specification for docs/community-features/015-release-engineering.md"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Adopt Semantic Versioning & Source of Truth (Priority: P1)

As a project maintainer and developer, I want a standardized versioning system (SemVer starting at v0.1.0) and a single source of truth for version definitions (`pyproject.toml`, Docker images, git tags) so that the codebase is predictably and transparently tracked.

**Why this priority**: Crucial baseline for release engineering. Ensures version numbers are meaningful, logical, and synchronized across package manifests, containers, and git history.

**Independent Test**:
* Verify `pyproject.toml` version field matches the current target release version.
* Run a git tag command and confirm tag names strictly adhere to SemVer prefix/format guidelines.

**Acceptance Scenarios**:
1. **Given** a new version is declared, **When** the developer changes the version in `pyproject.toml`, **Then** the git tag and Docker tag match this version exactly on release.

---

### User Story 2 - Adopt Keep a Changelog & Document Policy (Priority: P1)

As a developer and community member, I want a clear, well-structured `CHANGELOG.md` following "Keep a Changelog" formatting, and a documented versioning policy, so that I can easily understand what changes have been made in each version.

**Why this priority**: Critical for repository communication and transparency. Helps users and contributors understand change impact before upgrading.

**Independent Test**:
* Verify that `CHANGELOG.md` is present at the repository root and is valid markdown.
* Review `CHANGELOG.md` to ensure previous developments (features 001-010) are summarized.

**Acceptance Scenarios**:
1. **Given** a new version is released, **When** developers read `CHANGELOG.md`, **Then** they see changes cleanly divided into Added, Changed, and Fixed categories.

---

### User Story 3 - Automate Version Tagged Releases (Priority: P2)

As a maintainer, I want pushing a version tag (e.g. `v0.1.0`) to automatically run a release workflow that validates SemVer, builds and pushes versioned Docker images to Docker Hub (e.g., `vX.Y.Z` and `latest`), and generates a GitHub Release with auto-generated release notes.

**Why this priority**: Simplifies release logistics, eliminates manual image uploading errors, and ensures that tags are always backed by verified built containers.

**Independent Test**:
* Verify that pushing a tag matching `v*` triggers `.github/workflows/release.yml`.
* Check that the release workflow pushes to Docker Hub with tags `v0.1.0` and `latest` and publishes a GitHub Release.

**Acceptance Scenarios**:
1. **Given** a release tag `v0.1.0` is pushed, **When** GHA runs, **Then** a GitHub Release is created and the built Docker image is tagged and pushed as `latest` and `v0.1.0`.

---

### User Story 4 - Automated Release Drafting on PR Merge (Priority: P2)

As a maintainer, I want release drafts to be automatically compiled as PRs are merged, grouping changes into sections (added, fixed, breaking change, etc.) based on PR labels, to eliminate manual release notes overhead.

**Why this priority**: High utility for developers. Keeps release notes up to date continuously and reduces the work needed to compile changelogs at release time.

**Independent Test**:
* Merge a pull request labeled `bugfix` and check that the draft release notes section under "Fixed" is automatically updated.

**Acceptance Scenarios**:
1. **Given** a merged pull request, **When** release drafter runs, **Then** the draft release notes are updated under the appropriate category header.

---

### User Story 5 - Versioned Docker Builds on dev/main pushes (Priority: P2)

As a user pulling container images, I want pushes to `main` to tag Docker images as `latest`, pushes to `dev` to tag as `dev`, and PRs to build without pushing, so that my container deployments always align with the branch stability guarantees.

**Why this priority**: Keeps Docker Hub images fresh and synchronized with the Git development branch workflow rules.

**Independent Test**:
* Push a commit to `dev` and verify GHA builds and pushes the image with the tag `dev`.
* Push a commit to `main` and verify GHA builds and pushes the image with the tag `latest`.

**Acceptance Scenarios**:
1. **Given** a push to `dev`, **When** the workflow executes, **Then** the Docker image is pushed to Docker Hub as `dev` only.

---

### Edge Cases

- **Tag format mismatch**: If a tag does not match the SemVer format (e.g., `v0.1` or `release-1`), the release workflow should fail gracefully with an informative error rather than pushing invalid Docker images.
- **Docker login secrets missing**: If credentials for Docker Hub are missing or expired in GHA secrets, image push will fail. The workflow must fail securely and log the error context without exposing secrets.

## Requirements *(mandatory)*

### Functional Requirements

* **FR-001**: The project MUST adopt Semantic Versioning (SemVer) starting at `v0.1.0` with `pyproject.toml` version field as the single source of truth.
* **FR-002**: The project MUST maintain a `CHANGELOG.md` at the root following the "Keep a Changelog" conventions (Added, Changed, Deprecated, Removed, Fixed, Security), pre-populated with summary changes from previous features (001-010).
* **FR-003**: The versioning policy MUST be fully documented in a dedicated section in `CONTRIBUTING.md`.
* **FR-004**: Pushing an annotated Git tag of format `vX.Y.Z` MUST trigger an automated GitHub Actions release workflow (`.github/workflows/release.yml`) that builds and pushes versioned Docker images to Docker Hub, and publishes a GitHub Release.
* **FR-005**: An automated Release Drafter workflow (`.github/workflows/release-drafter.yml`) MUST manage and draft releases as pull requests are merged, using labels to categorize commits.
* **FR-006**: The existing `.github/workflows/docker-build.yml` workflow MUST be updated to push versioned tag builds on tags, `latest` on `main` push, `dev` on `dev` push, and run validation-only builds on pull requests.
* **FR-007**: None of the changes made by this feature may modify application code or core business logic.
* **FR-008**: GitHub Release workflows must use pinned action versions for security.

### Key Entities

- **Semantic Version**: MAJOR.MINOR.PATCH format tracking code changes.
- **Release GHA Workflow**: Automation building, tagging, and pushing Docker images on tags.
- **Release Drafter**: Automation updating draft release notes based on PR categories.
- **Changelog File**: Markdown file tracking additions, changes, and bug fixes chronologically.

## Success Criteria *(mandatory)*

### Measurable Outcomes

* **SC-001**: Version tags push triggers GHA workflows that build and tag Docker images correctly.
* **SC-002**: `CHANGELOG.md` exists in the root and follows "Keep a Changelog" format.
* **SC-003**: `docker-build.yml` successfully pushes `latest` on `main`, `dev` on `dev`, and `vX.Y.Z` on tag pushes.
* **SC-004**: Release drafter workflow successfully creates and updates drafts based on PR labels.
* **SC-005**: Versioning rules are documented inside the repository.

## Assumptions

- Maintainers configure Docker Hub credentials (`DOCKER_USERNAME`, `DOCKER_PASSWORD`) as Repository Secrets in GitHub.
- Annotated Git tags will be created manually on release milestones.
