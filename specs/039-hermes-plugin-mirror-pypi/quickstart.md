# Quickstart: Hermes Plugin Mirror and PyPI Packages

This quickstart describes the intended maintainer validation path after the implementation tasks are complete. It assumes the main Wright repository remains the source of truth and the Hermes mirror repository is generated from `hermes-plugin-wright/`.

## 1. Confirm the Active Feature

```bash
git status --short --branch
cat .specify/feature.json
```

Expected feature directory:

```text
specs/039-hermes-plugin-mirror-pypi
```

## 2. Run Existing Python Quality Gates

```bash
uv sync --all-packages --all-groups
uv run ruff check apps/api packages/core packages/agent_adapters packages/tool_registry packages/data_vault packages/workspace_service hermes-plugin-wright
uv run ruff format --check apps/api packages/core packages/agent_adapters packages/tool_registry packages/data_vault packages/workspace_service hermes-plugin-wright
uv run pytest packages/core packages/tool_registry hermes-plugin-wright/tests
```

## 3. Build Initial Python Package Artifacts

```bash
scripts/build-python-distributions.sh packages/core packages/tool_registry
```

The helper should build source distributions and wheels, validate metadata, inspect artifacts, and prove clean installability without a Wright monorepo checkout.

Expected release order:

1. `wright-core`
2. `wright-tool-registry`
3. `hermes-plugin-wright` mirror release

## 4. Publish to TestPyPI First

Use the package publishing workflow against TestPyPI before any stable release. The workflow should use Trusted Publishing with the `testpypi` GitHub environment.

```bash
gh workflow run publish-python-packages.yml \
  -f package=wright-core \
  -f version=<version> \
  -f target=testpypi

gh workflow run publish-python-packages.yml \
  -f package=wright-tool-registry \
  -f version=<version> \
  -f target=testpypi
```

Then verify clean installation from TestPyPI in an isolated environment.

## 5. Publish Stable Packages to PyPI

After TestPyPI validation passes, tag or dispatch the package-scoped stable release. The PyPI environment should require manual approval.

```bash
git tag wright-core-v<version>
git tag wright-tool-registry-v<version>
git push origin wright-core-v<version> wright-tool-registry-v<version>
```

Confirm both package versions are visible on PyPI before creating the stable plugin mirror release.

## 6. Generate the Mirror Dry Run

```bash
scripts/sync-hermes-plugin-mirror.sh \
  --source hermes-plugin-wright \
  --mirror-url https://github.com/burhop/hermes-plugin-wright \
  --branch dev \
  --dry-run
```

The dry run should show only plugin files, tests, metadata, README, license, and provenance.

## 7. Validate Mirror Content

```bash
scripts/validate-hermes-plugin-mirror.sh \
  --mirror-dir <generated-mirror-dir> \
  --channel development
```

For stable validation, use:

```bash
scripts/validate-hermes-plugin-mirror.sh \
  --mirror-dir <generated-mirror-dir> \
  --channel stable
```

Stable validation must fail if dependencies are not published package versions.

## 8. Run Hermes Lifecycle Tests Against the Mirror

Development channel:

```bash
scripts/test-hermes-plugin-install.sh \
  --repo-url https://github.com/burhop/hermes-plugin-wright \
  --ref dev \
  --identifier https://github.com/burhop/hermes-plugin-wright/tree/dev

scripts/test-hermes-plugin-update.sh \
  --repo-url https://github.com/burhop/hermes-plugin-wright \
  --ref dev \
  --identifier https://github.com/burhop/hermes-plugin-wright/tree/dev

scripts/test-hermes-plugin-uninstall.sh \
  --repo-url https://github.com/burhop/hermes-plugin-wright \
  --ref dev \
  --identifier https://github.com/burhop/hermes-plugin-wright/tree/dev
```

Stable channel:

```bash
scripts/test-hermes-plugin-install.sh \
  --repo-url https://github.com/burhop/hermes-plugin-wright \
  --ref main \
  --identifier https://github.com/burhop/hermes-plugin-wright/tree/main

scripts/test-hermes-plugin-update.sh \
  --repo-url https://github.com/burhop/hermes-plugin-wright \
  --ref main \
  --identifier https://github.com/burhop/hermes-plugin-wright/tree/main

scripts/test-hermes-plugin-uninstall.sh \
  --repo-url https://github.com/burhop/hermes-plugin-wright \
  --ref main \
  --identifier https://github.com/burhop/hermes-plugin-wright/tree/main
```

The update test must confirm the installed plugin directory contains `.git` metadata.

## 9. Sync the Mirror

After package and lifecycle validation pass, run the mirror sync without `--dry-run`.

```bash
scripts/sync-hermes-plugin-mirror.sh \
  --source hermes-plugin-wright \
  --mirror-url https://github.com/burhop/hermes-plugin-wright \
  --branch dev
```

For a stable release, sync to the stable mirror branch and tag the mirror release after validation.

## 10. Customer Smoke Test

From a fresh Hermes home, run the commands exactly as documented in the mirror README:

```bash
hermes plugins install https://github.com/burhop/hermes-plugin-wright/tree/main --enable
hermes plugins list --user --plain
hermes plugins update wright
hermes plugins remove wright
```

A tester should be able to complete the path in under 10 minutes using only the mirror README.
