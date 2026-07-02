# Contract: Mirror Repository

## Purpose

Defines the required shape of the standalone Wright Hermes plugin mirror repository. The mirror exists so customers can install and update the Wright plugin through the standard Hermes plugin lifecycle without cloning the full Wright monorepo.

## Required Root Files

The mirror repository root must contain:

```text
plugin.yaml
__init__.py
bridge.py
catalog.py
catalog.yaml
commands.py
schemas.py
pyproject.toml
README.md
LICENSE or LICENSE.md
PROVENANCE.md or provenance.json
verify_plugin.py
tests/
```

## Required README Content

The mirror README must include:

- A first-screen statement that this is the official thin Wright Hermes plugin mirror.
- Stable install command.
- Development install command.
- Update command.
- Remove command.
- Migration guidance for users who installed from the monorepo subdirectory.
- Link to the main Wright repository.
- Link to the main Wright issue tracker.
- Link to the main Wright documentation or docs index.
- Link to main Wright releases.
- Links to `wright-core` and `wright-tool-registry` package pages.
- Link to Hermes plugin usage guidance.
- Source revision or release provenance for the mirrored state.

## Prohibited Content

The mirror repository must not contain:

```text
apps/
packages/
docker/
docs/ except mirror-specific documentation
specs/
registry/
node_modules/
.venv/
__pycache__/
.pytest_cache/
*.pyc
.env
.env.*
uv.lock unless explicitly approved for mirror reproducibility
machine-specific absolute paths
private credentials or tokens
large generated application assets
```

## Provenance Requirements

Every mirrored state must record:

- Main Wright repository URL.
- Full main repository commit SHA.
- Source branch.
- Generated timestamp in UTC.
- Workflow run URL when generated in CI.
- Plugin version.
- `wright-core` version.
- `wright-tool-registry` version.
- Allowlisted source paths copied into the mirror.

## Validation Behavior

A mirror validation run must fail when:

- `plugin.yaml` is missing from repository root.
- A required root file is missing.
- Prohibited content appears in the mirror.
- README required sections or required links are missing.
- Provenance is missing or uses a branch name instead of a full commit SHA.
- Stable dependency declarations reference workspace paths or unpinned Git sources.

## Compatibility Notes

- The mirror root is the Hermes install target.
- The mirror must preserve Git metadata when installed by Hermes so `hermes plugins update wright` can run a normal Git update.
- The mirror is not a development fork. Feature work should happen in the main Wright repository first.
