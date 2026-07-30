# Wright Hermes Plugin Mirror

This is the official thin Wright Hermes plugin mirror for https://github.com/burhop/wright.
It is the production thin adapter for the Hermes Git plugin interface. The
adapter installs `wright-engineering` into manager-neutral `WRIGHT_HOME` state;
it does not contain the Wright application runtime.

## Install

Stable install command:

```bash
hermes plugins install https://github.com/burhop/hermes-plugin-wright/tree/main --enable
```

Development install command:

```bash
hermes plugins install https://github.com/burhop/hermes-plugin-wright/tree/dev --enable
```

## Update

```bash
hermes plugins update wright
```

## Remove

Preserve Wright data by running `/wright uninstall` first, then remove the
manager-owned adapter:

```bash
hermes plugins remove wright
```

## Migration

If you installed from the monorepo subdirectory, remove that copy and reinstall from this mirror root.

## Links

- Main repository: https://github.com/burhop/wright
- Issues: https://github.com/burhop/wright/issues
- Documentation: https://burhop.github.io/wright/
- Releases: https://github.com/burhop/wright/releases
- Alpha PyPI package: https://pypi.org/project/wright-engineering/
- Component packages remain workspace-local for alpha.
- Hermes plugin usage: https://github.com/burhop/wright/blob/main/docs/getting-started/hermes-plugin.md
- Source revision and provenance: PROVENANCE.md
