# Contract: Release Validation

## Purpose

Defines the gate that must pass before a Wright Hermes plugin mirror release is considered customer-testable.

## Inputs

A release validation run receives:

- Main repository URL.
- Main repository commit SHA.
- Source branch.
- Mirror repository URL.
- Mirror branch or tag.
- Release channel.
- Plugin version.
- Hermes expected version.
- `wright-core` version or Git revision.
- `wright-tool-registry` version or Git revision.
- Docker image tag for Hermes lifecycle validation.

## Required Checks

### Package Checks

- Build `wright-core` source distribution and wheel.
- Build `wright-tool-registry` source distribution and wheel.
- Validate package metadata.
- Install packages in dependency order in a clean environment.
- Import `core` and `tool_registry` without a monorepo checkout.
- Run relevant package tests.

### Mirror Content Checks

- Export only allowlisted plugin files.
- Confirm required root files exist.
- Confirm prohibited paths do not exist.
- Confirm stable dependency declarations do not use workspace paths.
- Confirm development Git dependencies are pinned.
- Confirm provenance references a full main repository commit SHA.

### README Checks

- Confirm install, update, remove, migration, stable channel, and development channel sections exist.
- Confirm required links are present.
- Confirm package links point at the expected package names.
- Confirm main repository support links point back to the main Wright repository.

### Hermes Lifecycle Checks

- Run install from the mirror repository root.
- Confirm plugin is listed and enabled.
- Confirm Wright command group discovery.
- Run update.
- Run remove.
- Run reinstall.

## Outputs

A release validation run must produce:

- Pass/fail status.
- Release channel.
- Main repository commit SHA.
- Mirror repository URL and branch/tag.
- Package versions or Git revisions.
- Hermes version used.
- Artifact links for package distributions.
- Link or path to lifecycle logs.
- Human-readable failure reason when failed.

## Failure Policy

Validation must fail closed. Missing inputs, missing artifacts, missing README sections, missing provenance, unavailable package versions, failed package imports, and failed Hermes lifecycle commands all block release.

## Stable Channel Rules

Stable channel validation additionally requires:

- Published PyPI versions for every Wright dependency used by the plugin.
- No Git dependencies in plugin metadata.
- PyPI environment approval before publication.
- Release notes that include source revision and dependency versions.

## Development Channel Rules

Development channel validation allows:

- TestPyPI packages.
- Pinned Git dependency revisions.
- Development mirror branch targets.

Development channel validation still requires mirror content, README, provenance, and Hermes lifecycle checks.
