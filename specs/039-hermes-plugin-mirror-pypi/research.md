# Research: Hermes Plugin Mirror and PyPI Packages

## Decision: Use a root-level standalone mirror repository

**Decision**: Create and maintain a dedicated Wright Hermes plugin mirror repository whose root contains `plugin.yaml` and the plugin files. The customer install identifier points at the mirror repository root, not a subdirectory of the Wright monorepo.

**Rationale**: Hermes plugin update expects the installed plugin directory to be a Git checkout. Installing a monorepo subdirectory leaves the copied plugin directory without `.git` metadata, so `hermes plugins update wright` cannot work. A root-level mirror aligns the install, update, and remove paths with normal Hermes plugin behavior.

**Alternatives considered**:

- Continue installing from `burhop/wright/tree/dev/hermes-plugin-wright`: rejected because update cannot work reliably after subdirectory extraction.
- Mirror the whole Wright monorepo: rejected because it confuses customers, increases clone size, and violates the thin mirror requirement.
- Publish only a Python package entry point: rejected as the primary path because the user testing target is the standard Hermes plugin lifecycle.

## Decision: Keep the monorepo as source of truth and generate the mirror

**Decision**: Treat `hermes-plugin-wright/` in the Wright monorepo as the development source of truth, then sync an allowlisted file set to the mirror root. The sync must write a provenance record that includes the main repository URL, source commit, source branch, plugin version, dependency versions, and workflow run.

**Rationale**: This keeps normal Wright development, tests, and review in one place while giving Hermes users a clean plugin repository. An allowlist prevents generated caches, workspace files, Docker content, docs unrelated to plugin usage, and personal paths from leaking into the mirror.

**Alternatives considered**:

- Manual copy to the mirror: rejected because it is easy to drift and hard to audit.
- Independent mirror development: rejected because it creates two sources of truth.
- Git subtree split only: useful as an implementation option, but still needs content validation, README checks, and provenance output.

## Decision: Publish package dependencies before stable mirror releases

**Decision**: Publish `wright-core` first and `wright-tool-registry` second as the initial PyPI package set, because the plugin depends on `wright-tool-registry`, and `wright-tool-registry` depends on `wright-core`. Stable plugin releases must depend on versioned package releases. Git dependencies are allowed only for development testing and must be pinned to an immutable revision.

**Rationale**: The mirror can stay thin only if shared Wright code is installable without a workspace checkout. Versioned package dependencies also make customer installs reproducible and let release checks fail before a broken plugin reaches the mirror.

**Alternatives considered**:

- Keep `[tool.uv.sources]` workspace dependencies in mirror releases: rejected because they only work inside the monorepo.
- Vendor `wright-core` and `wright-tool-registry` into the mirror: rejected because it makes the mirror a second package source and increases drift risk.
- Publish every Wright package at once: rejected for this phase because only `wright-core` and `wright-tool-registry` are required by the current plugin dependency chain.

## Decision: Use PyPI/TestPyPI Trusted Publishing

**Decision**: Add a GitHub Actions package publishing workflow that builds source distributions and wheels, publishes every release candidate to TestPyPI, and publishes stable tagged releases to PyPI through Trusted Publishing/OIDC. The PyPI environment requires manual approval; TestPyPI does not.

**Rationale**: PyPI Trusted Publishing exchanges GitHub Actions OIDC identity for short-lived package upload credentials, removing long-lived PyPI API tokens from repository secrets. The Python Packaging User Guide recommends building distributions in CI, storing the distribution artifact, and publishing with `pypa/gh-action-pypi-publish` using `id-token: write` permissions. TestPyPI gives maintainers a rehearsal lane before stable PyPI publication.

**Sources**:

- PyPI Trusted Publishing documentation: https://docs.pypi.org/trusted-publishers/
- PyPA GitHub Actions publishing guide: https://packaging.python.org/en/latest/guides/publishing-package-distribution-releases-using-github-actions-ci-cd-workflows/
- Python Packaging project tutorial and metadata guidance: https://packaging.python.org/en/latest/tutorials/packaging-projects/

**Alternatives considered**:

- Long-lived PyPI API tokens in GitHub secrets: rejected because they are higher risk and are no longer the preferred automation path.
- Manual local uploads: rejected because they are not repeatable enough for customer-facing dependency releases.
- TestPyPI only: rejected because stable customer installs require PyPI availability.

## Decision: Use package-scoped release tags and explicit dependency ordering

**Decision**: Use package-scoped release triggers for Python package publication, such as `wright-core-vX.Y.Z` and `wright-tool-registry-vX.Y.Z`, and a plugin-scoped mirror release trigger, such as `hermes-plugin-wright-vX.Y.Z`. The release workflow must verify that dependent package versions are already available before mirroring or tagging the plugin.

**Rationale**: The repository is a monorepo with independently versioned packages. Package-scoped tags avoid publishing unrelated packages, make rollback clearer, and keep the plugin mirror release tied to the exact dependency set it declares.

**Alternatives considered**:

- One global `vX.Y.Z` tag for all packages and Docker: rejected because Docker appliance releases and plugin/package releases may not always move together.
- Manual workflow dispatch only: useful for emergency reruns, but rejected as the sole release path because tags give stronger auditability.

## Decision: Validate the mirror as a customer would use it

**Decision**: Update the Hermes lifecycle scripts so they can target either the monorepo development subdirectory or the root-level mirror repository. The release gate for the mirror must use the root-level mirror path and run install, command discovery, update, remove, and reinstall checks inside the Hermes 0.18 Docker image.

**Rationale**: The bug this feature prevents is specifically an install/update lifecycle mismatch. Validation must therefore exercise Hermes through the same repository shape and commands customers use, not a local path or editable workspace install.

**Alternatives considered**:

- Keep only monorepo subdirectory lifecycle tests: rejected because those tests intentionally preserve the failing update shape.
- Validate only Python importability: rejected because Hermes plugin lifecycle compatibility is the customer-visible behavior.

## Decision: Make the mirror README the customer landing page

**Decision**: The mirror README must start by identifying itself as the official thin Wright Hermes plugin mirror, then provide install, update, remove, migration, stable/dev channel, package dependency, support, and provenance links. The main Wright repository remains the support and development home.

**Rationale**: Users may discover the mirror directly through GitHub or Hermes commands. Clear first-screen messaging prevents them from filing issues or looking for full Wright development docs in the mirror.

**Alternatives considered**:

- Keep the current plugin README with minor edits: rejected because it is monorepo-oriented and does not fully explain mirror ownership, update behavior, or package links.
- Put detailed docs only in the main repo: rejected because the mirror must be self-sufficient for customer install/update/remove testing.
