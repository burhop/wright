# Wright Hermes Git Plugin

This directory is the official production thin adapter between released Hermes
and the manager-neutral Wright runtime. It is mirrored at
`https://github.com/burhop/hermes-plugin-wright`; Wright's monorepo remains the
source of truth.

## Stable Install

Hermes installs and updates the adapter with its real Git plugin commands:

```text
hermes plugins install https://github.com/burhop/hermes-plugin-wright --enable
hermes plugins update wright
```

Git is a Hermes adapter prerequisite. The plugin itself imports only Python's
standard library, resolves a Wright-owned `WRIGHT_HOME` (default `~/.wright`),
installs the exact `wright-engineering` application artifact into an isolated
bootstrap environment, and projects `/wright` commands to Wright's public
lifecycle CLI. The Wright runtime never imports into the Hermes process.

After installation:

```text
/wright start
/wright status
/wright doctor
/wright stop
/wright update
/wright rollback
```

## Update and removal

Hermes retains the adapter's `plugin.yaml` and `.git` metadata so its standard update command can fetch and verify the current mirror commit. Wright runtime updates remain separate `/wright update` operations.

Hermes 0.19 has no plugin pre-remove callback. Safely remove Wright with:

```text
/wright uninstall
hermes plugins remove wright
```

Normal uninstall preserves `WRIGHT_HOME/data`. To delete Wright-owned data,
request `/wright purge`, inspect the disclosed path and confirmation code, then
repeat the command with that code before removing the adapter.

## Development validation

Feature and pull-request validation uses an isolated local Git repository and
candidate wheelhouse. Do not install an unreleased branch as a production
substitute. The release train verifies the mirror commit, its generated
`PROVENANCE.md`, and the exact compatible
[`wright-engineering`](https://pypi.org/project/wright-engineering/) artifact.

## Migration From the Monorepo Subdirectory

Remove an older subdirectory-installed adapter and reinstall from the stable
root mirror shown above. Component packages remain workspace-local development
projects; their application modules ship inside the one public Wright runtime.

- Source: <https://github.com/burhop/wright>
- Issues: <https://github.com/burhop/wright/issues>
- Releases: <https://github.com/burhop/wright/releases>
