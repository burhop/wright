# Hermes Plugin Mirror Release Runbook

This runbook covers the thin `hermes-plugin-wright` mirror and the package strategy used by the Wright Hermes plugin. For public alpha, only the user-facing `wright-engineering` package is published to PyPI/TestPyPI; component package publication for the mirror is deferred.

## Ownership

The main Wright repository remains the source of truth:

- Source: https://github.com/burhop/wright
- Issues: https://github.com/burhop/wright/issues
- Documentation: https://burhop.github.io/wright/
- Releases: https://github.com/burhop/wright/releases

The mirror repository is a distribution surface only. Do not develop features directly in the mirror.

## Release Channels

| Channel | Mirror branch | Dependency policy | User |
| --- | --- | --- | --- |
| Development | `dev` | TestPyPI packages or pinned Git revisions | Maintainers and early testers |
| Stable | `main` | Versioned PyPI releases only | Customer testers and stable users |

## Package Publication Order

For public alpha, publish the root `wright-engineering` package before using the mirror in public installation docs. Component packages such as `wright-core` and `wright-tool-registry` remain workspace-local until their package names, dependency boundaries, and mirror install strategy are revisited.

Use the alpha package tag when publishing the PyPI helper package:

```bash
git tag wright-engineering-v0.1.0-alpha.1
git push origin wright-engineering-v0.1.0-alpha.1
```

The `.github/workflows/publish-python-packages.yml` workflow uses PyPI Trusted Publishing through GitHub Actions OIDC. Configure pending publishers in PyPI and TestPyPI with these environments:

- `testpypi` for TestPyPI publication
- `pypi` for stable PyPI publication

Require manual approval on the `pypi` GitHub environment before stable uploads.

## Local Package Validation

```bash
scripts/build-python-distributions.sh --dry-run .
```

For a full local build, install `build` into the active Python environment and run:

```bash
scripts/build-python-distributions.sh --skip-clean-install .
```

Clean install validation is the release gate that proves package artifacts can install without a Wright monorepo checkout.

## Mirror Update Automation

The mirror repository is https://github.com/burhop/hermes-plugin-wright. It is updated from the main Wright repository by `.github/workflows/sync-hermes-plugin-mirror.yml`.

Required GitHub setup:

- Add a read-write deploy key named `wright mirror sync` to `burhop/hermes-plugin-wright`.
- Store the private key as the `HERMES_PLUGIN_MIRROR_SSH_KEY` Actions secret on `burhop/wright`.

Publishing behavior:

- Pushes to the Wright `dev` branch generate, validate, and publish the mirror `dev` branch.
- Pushes to the Wright `main` branch generate, validate, and publish the mirror `main` branch.
- Manual workflow dispatch can validate without publishing, or publish when `publish` is set to true.
- The workflow clones an existing mirror branch before committing generated files, so branch history is preserved for Hermes update compatibility. It does not force-push unrelated orphan history.

## Mirror Generation

Preview mirror contents:

```bash
scripts/sync-hermes-plugin-mirror.sh \
  --source hermes-plugin-wright \
  --mirror-url https://github.com/burhop/hermes-plugin-wright \
  --branch dev \
  --dry-run
```

Generate a local development mirror:

```bash
tmp_dir=$(mktemp -d)
scripts/sync-hermes-plugin-mirror.sh \
  --source hermes-plugin-wright \
  --mirror-url https://github.com/burhop/hermes-plugin-wright \
  --branch dev \
  --channel development \
  --output-dir "$tmp_dir"
```

## Mirror Validation

```bash
scripts/validate-hermes-plugin-mirror.sh --mirror-dir "$tmp_dir" --channel development
scripts/validate-hermes-plugin-mirror.sh --mirror-dir "$tmp_dir" --channel stable
```

Stable validation must fail if the mirror has workspace-only dependencies, unpinned Git dependencies, missing README links, missing provenance, prohibited paths, or missing root-level plugin files.

## Hermes Lifecycle Validation

Development mirror path:

```bash
scripts/test-hermes-plugin-install.sh --mirror-root --repo-url https://github.com/burhop/hermes-plugin-wright --ref dev
scripts/test-hermes-plugin-update.sh --mirror-root --repo-url https://github.com/burhop/hermes-plugin-wright --ref dev
scripts/test-hermes-plugin-uninstall.sh --mirror-root --repo-url https://github.com/burhop/hermes-plugin-wright --ref dev
```

Stable mirror path:

```bash
scripts/test-hermes-plugin-install.sh --mirror-root --repo-url https://github.com/burhop/hermes-plugin-wright --ref main
scripts/test-hermes-plugin-update.sh --mirror-root --repo-url https://github.com/burhop/hermes-plugin-wright --ref main
scripts/test-hermes-plugin-uninstall.sh --mirror-root --repo-url https://github.com/burhop/hermes-plugin-wright --ref main
```

The update validation must confirm the installed plugin directory contains `.git` metadata.

## Customer Commands

Stable install:

```bash
hermes plugins install https://github.com/burhop/hermes-plugin-wright/tree/main --enable
```

Development install:

```bash
hermes plugins install https://github.com/burhop/hermes-plugin-wright/tree/dev --enable
```

Update:

```bash
hermes plugins update wright
```

Remove:

```bash
hermes plugins remove wright
```

## Migration Guidance

If a user installed from `https://github.com/burhop/wright/tree/dev/hermes-plugin-wright`, ask them to remove that plugin and reinstall from the mirror root. Subdirectory installs can lack plugin-directory `.git` metadata, which prevents standard Hermes updates.

## Validation Results

Use this section to record release candidate validation runs.

### US1 Mirror Lifecycle

2026-07-02 local validation passed:

- `scripts/sync-hermes-plugin-mirror.sh --source hermes-plugin-wright --mirror-url https://github.com/burhop/hermes-plugin-wright --branch dev --channel development --dry-run` listed only allowlisted plugin, test, metadata, license, README, and provenance files.
- `scripts/sync-hermes-plugin-mirror.sh --source hermes-plugin-wright --mirror-url https://github.com/burhop/hermes-plugin-wright --branch dev --channel development --output-dir /tmp/wright-mirror-dev.pY8s1V` generated a development mirror export.
- `scripts/validate-hermes-plugin-mirror.sh --mirror-dir /tmp/wright-mirror-dev.pY8s1V --channel development` passed.
- `uv run pytest ... tests/test_hermes_plugin_mirror_sync.py tests/test_hermes_plugin_mirror_validation.py tests/test_hermes_plugin_lifecycle_contract.py ...` passed as part of the 151-test release suite.

2026-07-02 GitHub mirror lifecycle validation passed:

- Created public mirror repository `https://github.com/burhop/hermes-plugin-wright` and set `main` as the default branch.
- Added read-write deploy key `wright mirror sync` to the mirror and stored `HERMES_PLUGIN_MIRROR_SSH_KEY` as a `burhop/wright` Actions secret.
- Published mirror `dev` and `main` branches. `git ls-remote --heads https://github.com/burhop/hermes-plugin-wright dev main` returned both branch heads.
- Published a second generated `dev` commit and verified an existing clone updated with `git pull --ff-only` from `31d0115` to `66981ff`, proving generated updates preserve branch history.
- Development mirror dependencies are rewritten to pinned Git references until PyPI packages are published; stable mirror dependencies remain PyPI-only.
- `scripts/test-hermes-plugin-install.sh --mirror-root --repo-url https://github.com/burhop/hermes-plugin-wright --ref dev` passed in the Hermes 0.18 Docker image.
- `scripts/test-hermes-plugin-update.sh --mirror-root --repo-url https://github.com/burhop/hermes-plugin-wright --ref dev` passed in the Hermes 0.18 Docker image.
- `scripts/test-hermes-plugin-uninstall.sh --mirror-root --repo-url https://github.com/burhop/hermes-plugin-wright --ref dev` passed in the Hermes 0.18 Docker image.

### US2 Package Build and Clean Install

2026-07-02 validation passed:

- `scripts/build-python-distributions.sh --dry-run packages/core packages/tool_registry` passed metadata validation for `wright-core 0.1.0` and `wright-tool-registry 0.1.0`.
- `scripts/build-python-distributions.sh --dist-root /tmp/wright-python-dist packages/core packages/tool_registry` built source distributions and wheels, installed both wheels in an isolated environment, and imported `core` and `tool_registry` successfully.
- The clean-install gate exposed missing `opentelemetry-api` and `PyYAML` package dependencies; both are now declared and covered by `tests/test_python_package_metadata.py`.

### US3 Documentation and Link Validation

2026-07-02 validation passed:

- `uv run pytest ... tests/test_hermes_plugin_mirror_readme.py tests/test_hermes_plugin_mirror_provenance.py tests/test_hermes_plugin_mirror_docs.py` passed as part of the 151-test release suite.
- `scripts/validate-hermes-plugin-mirror.sh --mirror-dir tests/fixtures/hermes_plugin_mirror --channel stable` passed, including README and provenance checks.

### Final Release Gate

2026-07-02 validation passed for the development mirror lifecycle and stable mirror content gates:

- `uv run ruff check ...` passed for package, plugin, and release-engineering Python surfaces.
- `uv run ruff format --check ...` passed for the same surfaces.
- `uv run pytest packages/core/tests packages/tool_registry/tests hermes-plugin-wright/tests tests/test_release_engineering_scripts.py tests/test_hermes_plugin_mirror_sync.py tests/test_hermes_plugin_mirror_validation.py tests/test_hermes_plugin_lifecycle_contract.py tests/test_python_package_metadata.py tests/test_python_package_distribution_build.py tests/test_publish_python_packages_workflow.py tests/test_sync_hermes_plugin_mirror_workflow.py tests/test_hermes_plugin_mirror_readme.py tests/test_hermes_plugin_mirror_provenance.py tests/test_hermes_plugin_mirror_docs.py` passed: 151 tests in 101.29 seconds.
- `scripts/sync-hermes-plugin-mirror.sh --source hermes-plugin-wright --mirror-url https://github.com/burhop/hermes-plugin-wright --branch main --channel stable --output-dir /tmp/wright-mirror-stable-final.TftFem` generated a stable mirror export.
- `scripts/validate-hermes-plugin-mirror.sh --mirror-dir /tmp/wright-mirror-stable-final.TftFem --channel stable` passed.

Stable mirror release through `https://github.com/burhop/hermes-plugin-wright/tree/main` remains gated on a later decision about component package publication. Public alpha customer testing should use the Docker paths and the `wright-engineering` helper package; development mirror testing can use `https://github.com/burhop/hermes-plugin-wright/tree/dev`.
