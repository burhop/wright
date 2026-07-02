# Data Model: Hermes Plugin Mirror and PyPI Packages

## MirrorRepository

Represents the standalone repository customers install with Hermes.

**Fields**:

- `name`: Repository name, expected to be `hermes-plugin-wright` or another approved Wright-owned mirror name.
- `remote_url`: Public Git remote URL used in customer install commands.
- `default_branch`: Stable branch, expected to track released plugin versions.
- `development_branch`: Development testing branch, expected to track Wright `dev` plugin exports.
- `required_root_files`: Allowlist of files that must exist at repository root.
- `allowed_paths`: File and directory allowlist copied from `hermes-plugin-wright/`.
- `prohibited_paths`: Monorepo-only, generated, cache, Docker, secret, or unrelated paths that must never appear in the mirror.
- `readme_links`: Required links back to the main Wright repository, issue tracker, docs, releases, package pages, and provenance.
- `provenance_record`: SourceRevisionRecord for the current mirrored state.

**Validation Rules**:

- `plugin.yaml` must exist at the repository root.
- The mirror must include plugin runtime files, README, package metadata, tests, and provenance.
- The mirror must not include `.pytest_cache`, `__pycache__`, workspace lockfiles unless explicitly approved, Docker image content, application services, local credentials, or personal paths.
- README links must resolve to intended Wright-owned targets during release validation.

## PublishedWrightPackage

Represents a Wright Python distribution required by the plugin.

**Fields**:

- `distribution_name`: PyPI project name, initially `wright-core` or `wright-tool-registry`.
- `import_package`: Python import package, initially `core` or `tool_registry`.
- `source_path`: Monorepo source directory.
- `version`: Published package version.
- `requires_python`: Supported Python range.
- `runtime_dependencies`: Versioned runtime package requirements.
- `build_backend`: Package build backend.
- `project_urls`: Homepage, source, issues, documentation, and release links shown on package pages.
- `license`: License expression or text included in distribution artifacts.
- `publication_status`: Current release state.
- `testpypi_url`: TestPyPI package URL when available.
- `pypi_url`: PyPI package URL when available.

**Validation Rules**:

- Stable releases must build both source distribution and wheel artifacts.
- Stable releases must install in an environment with no Wright monorepo checkout.
- `wright-tool-registry` stable releases must depend on a versioned `wright-core` release.
- Package metadata must include readme, license, project links, version, and Python compatibility.
- Distribution artifacts must not include caches, local paths, or unrelated monorepo files.

**State Transitions**:

```text
Draft -> Built -> TestPyPIPublished -> CleanInstallVerified -> PyPIPublished -> Available
Draft -> Built -> FailedValidation
TestPyPIPublished -> FailedValidation
```

## PluginRelease

Represents a customer-visible Wright Hermes plugin release.

**Fields**:

- `plugin_name`: Hermes plugin name, expected `wright`.
- `plugin_version`: Version from plugin metadata.
- `min_hermes_version`: Minimum supported Hermes version, expected `0.18.0` for this feature.
- `mirror_branch`: Mirror branch that receives the release.
- `mirror_tag`: Mirror tag created for the release.
- `source_revision`: SourceRevisionRecord for the monorepo commit.
- `package_versions`: Exact PublishedWrightPackage versions used by the release.
- `release_channel`: Stable or development channel.
- `lifecycle_validation`: ValidationRun covering install, update, remove, and reinstall.
- `readme_validation`: ValidationRun covering customer documentation links and instructions.

**Validation Rules**:

- Stable release dependencies must be PyPI versions, not workspace sources.
- Development release dependencies may use Git only when pinned to immutable revisions.
- The release must pass lifecycle validation from a fresh Hermes home.
- The release must include source revision and dependency versions in provenance.

**State Transitions**:

```text
Draft -> DependenciesVerified -> Mirrored -> LifecycleValidated -> Released
Draft -> DependenciesVerified -> Mirrored -> FailedValidation
Released -> Superseded
Released -> YankedOrDeprecated
```

## ReleaseChannel

Represents a user-facing install/update lane.

**Fields**:

- `name`: `stable` or `development`.
- `main_repo_branch`: Source branch in the Wright monorepo.
- `mirror_branch`: Destination branch in the mirror repository.
- `dependency_source_policy`: PyPI-only for stable, pinned Git allowed for development.
- `install_identifier`: Hermes install identifier shown to users.
- `promotion_rule`: Conditions required to move from development to stable.

**Validation Rules**:

- Stable channel must only reference published package versions.
- Development channel must identify branch and dependency revisions clearly.
- Both channels must run install/update/remove validation before public instructions change.

## SourceRevisionRecord

Represents traceability between the mirror and the main repository.

**Fields**:

- `main_repo_url`: Canonical Wright repository URL.
- `commit_sha`: Full source commit SHA.
- `branch`: Source branch name.
- `generated_at`: UTC timestamp of mirror generation.
- `workflow_run_url`: CI run URL that generated the mirror.
- `source_paths`: Allowlisted monorepo paths exported to the mirror.
- `package_versions`: Published package versions used by this mirror state.

**Validation Rules**:

- `commit_sha` must be a full immutable SHA, not a branch name.
- `source_paths` must be restricted to plugin and release metadata paths.
- Stable records must include PyPI package versions.

## ValidationRun

Represents the result of a release or mirror gate.

**Fields**:

- `name`: Validation name, such as `mirror-content`, `package-clean-install`, or `hermes-lifecycle`.
- `environment`: Runtime environment, such as GitHub Actions runner or Wright Hermes Docker image.
- `inputs`: Repository URL, branch, tag, package versions, and Hermes version used.
- `checks`: Ordered list of assertions performed.
- `status`: `passed`, `failed`, or `skipped`.
- `failure_reason`: Human-readable failure summary when status is `failed`.
- `artifact_links`: Logs, build artifacts, package artifacts, or workflow URLs.

**Validation Rules**:

- Release-blocking validation must fail closed when required inputs are missing.
- Failure output must identify which package, mirror path, README link, or lifecycle command failed.
- Passing validation must record the exact inputs used so results are reproducible.
