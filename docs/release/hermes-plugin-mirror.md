# Hermes Git Adapter Mirror Release Runbook

`https://github.com/burhop/hermes-plugin-wright` is Wright's production thin
adapter for Hermes' released Git plugin interface. It is not a second Wright
runtime and cannot replace PyPI, platform lifecycle, or Docker evidence.

The main Wright repository is the source of truth. The mirror is generated from
`hermes-plugin-wright/`; do not develop features directly in it.

## Channels

| Channel | Mirror branch | Use |
| --- | --- | --- |
| Development | `dev` | Wright integration and pull-request testing |
| Stable | `main` | Production Hermes installations |

The adapter is standard-library-only at import time. It resolves the exact
public `wright-engineering` version into `WRIGHT_HOME`; private component
packages such as `wright-core` and `wright-tool-registry` are neither bundled
nor installed from an index.

## Automation and credentials

`.github/workflows/sync-hermes-plugin-mirror.yml` generates, validates, and
publishes the matching mirror branch. Configure a read-write deploy key on the
mirror and store its private key as `HERMES_PLUGIN_MIRROR_SSH_KEY` in Wright.
PyPI publication remains separate and uses Trusted Publishing through the
`testpypi` and `pypi` environments.

## Local generation and validation

```bash
scripts/sync-hermes-plugin-mirror.sh \
  --source hermes-plugin-wright \
  --mirror-url https://github.com/burhop/hermes-plugin-wright \
  --branch dev \
  --dry-run

tmp_dir=$(mktemp -d)
scripts/sync-hermes-plugin-mirror.sh \
  --source hermes-plugin-wright \
  --mirror-url https://github.com/burhop/hermes-plugin-wright \
  --branch dev \
  --channel development \
  --output-dir "$tmp_dir"
scripts/validate-hermes-plugin-mirror.sh \
  --mirror-dir "$tmp_dir" \
  --channel development
```

Stable validation uses `--branch main --channel stable`. Validation rejects
workspace-only dependencies, Git dependencies in the adapter package metadata,
private Wright component dependencies, missing provenance, prohibited paths,
and missing root plugin files.

## Production identity

Hermes accepts a repository URL but does not select an immutable Git ref during
install. The release workflow therefore must:

1. resolve the mirror `main` commit;
2. run `hermes plugins install` with the repository URL;
3. verify the installed `.git` `HEAD` equals that commit;
4. verify `provenance.json` names the Wright release commit;
5. repeat the identity check after `hermes plugins update wright`;
6. only then run the Wright lifecycle.

Any mismatch is a release failure, not a warning.

## User Lifecycle and Migration Guidance

The migration path uses the same production root mirror.

Install or migrate to the stable root mirror:

```text
hermes plugins install https://github.com/burhop/hermes-plugin-wright --enable
hermes plugins update wright
```

Hermes provides no pre-remove hook. To remove Wright runtime code while
preserving data, then remove the adapter:

```text
/wright uninstall
hermes plugins remove wright
```

An older subdirectory install from the Wright monorepo should be removed and
reinstalled from the mirror root so standard Hermes updates retain `.git`
metadata. `/wright purge` remains a separately confirmed Wright operation.
