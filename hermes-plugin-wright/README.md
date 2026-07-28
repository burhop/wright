# Wright Hermes Plugin — Legacy Migration Delegate

This directory is the official thin Wright Hermes plugin mirror for one release
of migration support. It no longer builds or launches Wright from a repository.
New users install the complete public
[`wright-engineering`](https://pypi.org/project/wright-engineering/) application
through Hermes' package-plugin channel and then run `/wright start`.

## Stable Install (legacy only)

Existing Git-channel users may temporarily use:

```text
hermes plugins install https://github.com/burhop/hermes-plugin-wright/tree/main --enable
```

The mirror installs and delegates to the exact public Wright application version.
It is not accepted as Wright's production no-Git native-install evidence.

## Development Install (legacy only)

```text
hermes plugins install https://github.com/burhop/hermes-plugin-wright/tree/dev --enable
```

Do not use this channel for a production Wright installation.

## Update and removal

Legacy `.git` installations can still use the standard update command during the
migration window:

```text
hermes plugins update wright
hermes plugins remove wright
```

The `plugin.yaml` manifest identifies this mirror as deprecated. Normal removal
preserves Wright user data; `/wright purge` remains a separate confirmed action.

## Migration From the Monorepo Subdirectory

Remove the old Git-installed plugin, install Wright through Hermes' supported
package-plugin interface, and run `/wright start`. No Wright checkout,
`WRIGHT_REPO_DIR`, frontend build, or private component package is used. Component
packages remain workspace-local development projects and are bundled as modules
inside the one public application artifact.

- Source: <https://github.com/burhop/wright>
- Issues: <https://github.com/burhop/wright/issues>
- Releases: <https://github.com/burhop/wright/releases>
Provenance: [PROVENANCE.md](PROVENANCE.md)
