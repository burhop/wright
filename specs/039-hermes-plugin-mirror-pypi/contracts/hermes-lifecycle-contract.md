# Contract: Hermes Plugin Lifecycle

## Purpose

Defines the customer-visible Hermes lifecycle behavior the Wright plugin mirror must satisfy.

## Supported Channels

### Stable

- Source: stable mirror branch or release tag.
- Dependencies: versioned PyPI releases only.
- Target users: customer testing and stable users.

### Development

- Source: development mirror branch.
- Dependencies: TestPyPI releases or pinned Git revisions are allowed.
- Target users: maintainers and early testers.

## Install Contract

Given a fresh Hermes home and Hermes Agent 0.18+, installing the mirror must:

1. Clone or install from the mirror repository root.
2. Create a Wright plugin directory under the Hermes plugin home.
3. Preserve Git metadata needed by the update flow.
4. Load `plugin.yaml` from the plugin directory root.
5. Enable the plugin when requested.
6. Show the Wright plugin in Hermes plugin listings.
7. Make the Wright slash command group discoverable.

## Update Contract

Given a Wright plugin installed from the mirror repository, updating must:

1. Detect the installed plugin as a Git checkout.
2. Fetch or pull from the configured mirror remote.
3. Keep `plugin.yaml` and runtime files present after update.
4. Preserve plugin enablement state where Hermes supports it.
5. Leave the plugin usable without manual deletion or reinstall.

## Remove Contract

Given a Wright plugin installed from the mirror repository, removing must:

1. Remove the plugin from Hermes plugin listings.
2. Stop loading the Wright command group.
3. Remove or disable the plugin directory according to Hermes behavior.
4. Allow a clean reinstall from the same mirror identifier.

## Migration Contract

Given a user previously installed Wright from the monorepo subdirectory, the documentation must explain:

1. Why standard update cannot repair that install layout.
2. How to remove the old plugin installation.
3. How to install from the mirror repository root.
4. How to confirm the new install can update.

## Validation Commands

Lifecycle validation must exercise these behaviors through Hermes commands, not only Python imports:

```text
hermes plugins install <mirror-identifier> --enable
hermes plugins list --user --plain
hermes plugins update wright
hermes plugins remove wright
hermes plugins install <mirror-identifier> --enable
```

## Failure Conditions

Lifecycle validation must fail when:

- The installed plugin directory lacks `.git` metadata.
- `plugin.yaml` is not at the plugin root.
- `hermes plugins update wright` fails after mirror installation.
- The plugin is listed but the Wright command group is not discoverable.
- Remove leaves Hermes listing the plugin as active.
- Reinstall after remove fails.
