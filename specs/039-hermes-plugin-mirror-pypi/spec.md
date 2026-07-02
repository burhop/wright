# Feature Specification: Hermes Plugin Mirror and PyPI Packages

**Feature Branch**: `039-hermes-plugin-mirror-pypi`

**Created**: 2026-07-02

**Status**: Draft

**Input**: User description: "Define Option A for Wright as a thin Hermes plugin mirror repository plus published Python packages. The mirror contains only plugin files. Dependencies like wright-tool-registry are published to PyPI or installed from Git. Include PyPI setup. Make sure the repo has a clear README and many links to the main repo."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Install and Update Wright from the Mirror (Priority: P1)

A Hermes user can install the Wright plugin from a standalone mirror repository, enable it, use the Wright slash commands, update it through the standard Hermes plugin update path, and remove it cleanly without knowing the Wright monorepo layout.

**Why this priority**: This is the primary customer path. It removes the current subdirectory-install update failure and makes Wright behave like a normal Hermes plugin.

**Independent Test**: Can be fully tested in a fresh environment by installing from the mirror repository, confirming the Wright plugin loads, running a basic Wright command, updating the plugin, and uninstalling it.

**Acceptance Scenarios**:

1. **Given** a fresh Hermes installation and no Wright plugin installed, **When** the user follows the mirror README install instructions, **Then** Hermes installs the Wright plugin from a repository root and the Wright command group is available.
2. **Given** the Wright plugin was installed from the mirror repository, **When** the user runs the standard Hermes plugin update flow, **Then** the plugin updates successfully without requiring manual deletion or a monorepo checkout.
3. **Given** the Wright plugin is installed and enabled, **When** the user removes it through the standard Hermes plugin removal flow, **Then** Hermes no longer lists or loads the plugin.

---

### User Story 2 - Publish Wright Dependencies for Clean Installs (Priority: P2)

A Wright maintainer can release the plugin only after the Wright package dependencies needed by the plugin are available from a public package registry, or from an explicitly documented Git reference for development testing.

**Why this priority**: The mirror can only stay thin if shared Wright packages are distributed separately and install correctly outside the monorepo.

**Independent Test**: Can be fully tested by creating a clean environment with no monorepo workspace paths, installing the plugin dependencies from the declared release source, and confirming the plugin imports and loads.

**Acceptance Scenarios**:

1. **Given** a planned stable plugin release, **When** the release readiness checks run, **Then** every Wright package dependency required by the plugin is available from PyPI with compatible metadata and versions.
2. **Given** a development plugin test, **When** a dependency is intentionally installed from Git instead of PyPI, **Then** the Git source and revision are explicit, reproducible, and documented as non-stable.
3. **Given** a dependency version is missing, unpublished, or incompatible, **When** a mirror release is attempted, **Then** the release is blocked with a clear explanation of the missing package.

---

### User Story 3 - Navigate from the Mirror to the Main Wright Project (Priority: P3)

A user who lands on the mirror repository can quickly understand that it is a distribution mirror, find the main Wright repository, learn where to report issues, and locate the full documentation and release history.

**Why this priority**: The mirror must be easy for customers while preventing confusion about where development, support, and broader documentation live.

**Independent Test**: Can be fully tested by reviewing the mirror README and verifying that a user can reach the main repository, install/update/remove instructions, issue tracker, documentation, releases, and package pages without searching elsewhere.

**Acceptance Scenarios**:

1. **Given** a user opens the mirror README, **When** they read the first screen, **Then** they can tell the repository is the official thin Hermes plugin mirror for Wright and can reach the main Wright repository.
2. **Given** a user needs help, **When** they use links in the mirror README, **Then** they can reach the main issue tracker, documentation, release notes, and package pages.
3. **Given** a maintainer publishes a mirror release, **When** the user views the release notes or README, **Then** they can identify the corresponding main repository source revision and dependency versions.

### Edge Cases

- A user previously installed Wright from the monorepo subdirectory and then tries to update through Hermes.
- The mirror repository accidentally includes monorepo-only files, large application assets, generated caches, or unrelated packages.
- A plugin release references a Wright package version that has not been published or cannot be installed in a clean environment.
- A development install uses a moving branch instead of a pinned Git revision, making results non-reproducible.
- The mirror README links drift from the main repository paths, issue tracker, package pages, or release notes.
- The mirror is synced from the main repository, but the source revision is not recorded in the mirror release.
- A package name is unavailable on PyPI or conflicts with an unrelated project.
- The user has no network access after initial installation; local Wright usage should still work wherever Wright itself supports offline operation.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Wright MUST provide a standalone Hermes plugin mirror repository whose repository root is installable through the standard Hermes plugin lifecycle.
- **FR-002**: The mirror repository MUST contain only the files required to distribute, document, test, and release the Hermes plugin; it MUST NOT vendor the full Wright monorepo, application services, Docker appliance content, or unrelated packages.
- **FR-003**: A plugin installed from the mirror MUST retain the repository metadata required for standard Hermes updates.
- **FR-004**: Stable mirror releases MUST depend on published Wright packages rather than monorepo workspace paths.
- **FR-005**: `wright-core` and `wright-tool-registry` MUST be prepared for PyPI publication as the initial package set required by the current plugin dependency chain.
- **FR-006**: Any future Wright package required by the plugin MUST be published or explicitly documented as a Git-based development dependency before the mirror can depend on it.
- **FR-007**: Stable dependency declarations MUST use versioned package releases; Git dependency sources MUST be limited to documented development, testing, or pre-release channels.
- **FR-008**: The package publication process MUST verify package metadata, license information, project links, dependency resolution, and clean-environment installability before packages are announced for plugin use.
- **FR-009**: The mirror release process MUST verify install, enable, command discovery, update, disable or remove, and reinstall flows for the Wright plugin.
- **FR-010**: The mirror MUST support a stable customer channel and a development testing channel that correspond to the main Wright project's release and development flow.
- **FR-011**: The mirror README MUST clearly state that the mirror is a thin distribution repository and that the main Wright repository remains the source of truth for development, issues, roadmap, and broader documentation.
- **FR-012**: The mirror README MUST link to the main Wright repository, issue tracker, release notes, relevant documentation, package pages, Hermes plugin usage guidance, and the source revision represented by each mirror release.
- **FR-013**: Mirror releases MUST record which main Wright source revision and Wright package versions they were produced from.
- **FR-014**: Release checks MUST fail when the mirror contains prohibited non-plugin content, missing required documentation links, unavailable package versions, or dependency declarations that only work inside the monorepo.
- **FR-015**: Migration guidance MUST explain how users move from a monorepo subdirectory installation to the mirror installation when standard update cannot repair the older layout.
- **FR-016**: Published package and mirror artifacts MUST NOT contain local credentials, personal paths, generated caches, or machine-specific configuration.

### Key Entities

- **Mirror Repository**: The standalone public repository that distributes the Wright Hermes plugin and points users back to the main Wright project.
- **Published Wright Package**: A separately installable Wright dependency used by the plugin, including its package metadata, version, license, project links, and release status.
- **Plugin Release**: A versioned mirror state that users can install or update to, tied to a main repository source revision and a set of dependency versions.
- **Release Channel**: A user-facing path for stable customer installs or development testing installs.
- **Source Revision Record**: The traceability information connecting a mirror release to the main Wright repository state that produced it.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A new tester can install the Wright plugin from the mirror, confirm the Wright command group is available, update it, and remove it in under 10 minutes using only the mirror README.
- **SC-002**: Fresh-environment lifecycle validation passes for install, update, and remove on both stable and development channels for three consecutive runs before the mirror is announced.
- **SC-003**: 100% of stable mirror releases identify the matching main repository source revision and every Wright package version required by the plugin.
- **SC-004**: 100% of stable plugin dependency installs succeed in an environment with no Wright monorepo checkout or workspace paths.
- **SC-005**: Documentation review confirms that users can reach the main repository, issue tracker, release notes, package pages, and install/update/remove instructions from the mirror README in less than 60 seconds.
- **SC-006**: Release readiness checks catch missing package publications, missing required README links, and accidental non-plugin mirror content before a public mirror release is created.

## Assumptions

- The main Wright repository remains the source of truth; the mirror is a distribution surface, not a second development home.
- The first stable mirror path tracks the main Wright release channel, and the development testing path tracks the Wright `dev` flow.
- The current plugin dependency chain requires `wright-tool-registry`, which depends on `wright-core`; those two packages are the minimum initial PyPI publication scope.
- If an intended PyPI project name is unavailable, maintainers will choose a clear alternate package name and document the relationship from the mirror and main repository.
- Internet access is acceptable for initial installation and update, while Wright's local engineering workflows should remain usable offline after required software and packages are installed.
- Hermes 0.18 is the minimum supported Hermes baseline for this distribution work.
