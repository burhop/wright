# Contract: Python Package Publication

## Purpose

Defines the package metadata, build, and publication requirements for Wright Python packages that the Hermes plugin depends on outside the monorepo.

## Initial Packages

The first publication scope is:

```text
packages/core            -> distribution: wright-core, import package: core
packages/tool_registry   -> distribution: wright-tool-registry, import package: tool_registry
```

`wright-core` must be published before `wright-tool-registry`. `wright-tool-registry` stable releases must depend on a versioned `wright-core` release.

## Required Metadata

Each published package must declare:

- Distribution name.
- Version.
- Description.
- Supported Python versions.
- License.
- README suitable for package index display.
- Runtime dependencies with version constraints.
- Build backend.
- Project URLs for homepage, source, issues, documentation, and releases.

## Build Requirements

For each release candidate:

1. Build a source distribution.
2. Build a wheel.
3. Validate package metadata.
4. Inspect artifacts for prohibited files.
5. Install the artifact into a clean environment with no Wright monorepo checkout.
6. Import the package and run its relevant tests.

## Publication Requirements

Stable publication must use PyPI Trusted Publishing through GitHub Actions OIDC. Test publication must use TestPyPI Trusted Publishing.

The publishing workflow must:

- Use a package-scoped tag or explicit package input.
- Build artifacts before publishing.
- Store build artifacts for audit.
- Publish to TestPyPI before PyPI.
- Require manual approval for the PyPI environment.
- Use `id-token: write` for trusted publishing.
- Avoid long-lived PyPI or TestPyPI API tokens.

## Development Git Dependency Rules

A development plugin build may reference Wright packages from Git only when:

- The source is clearly marked development-only.
- The revision is an immutable commit SHA or tag.
- The mirror README explains that stable users should use the PyPI-backed install path.
- Lifecycle validation records the Git revisions used.

## Failure Conditions

Publication must be blocked when:

- Package metadata lacks required project links or license information.
- Package build fails.
- Clean install fails without the monorepo.
- Artifact inspection finds caches, local paths, credentials, or unrelated monorepo files.
- A package depends on a workspace-only source for a stable release.
- A required upstream package version is not available from the expected index.
