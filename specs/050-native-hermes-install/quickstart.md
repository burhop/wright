# Quickstart: Native Hermes Candidate Validation

This quickstart validates locally built artifacts. It does not publish to a
public registry or claim that the current Git-only Hermes installer satisfies
the production contract.

## 1. Confirm the feature context

```bash
git rev-parse --abbrev-ref HEAD
cat .specify/feature.json
```

Expected branch: `050-native-hermes-install`.

## 2. Run focused tests first

```bash
uv run python -m pytest -q tests/native_runtime
uv run --package hermes-plugin-wright python -m pytest -q hermes-plugin-wright/tests
npm run test --workspace=apps/web
```

These tests must include lifecycle state, path containment, compatibility,
process identity, update/rollback, uninstall/purge, package contents, and command
projection. Test tasks are written before their implementation tasks.

## 3. Build the candidate once

```bash
uv run python scripts/build-native-runtime.py \
  --output dist/native-candidate \
  --evidence dist/native-candidate/evidence.json
```

The builder runs the locked frontend build, places only inspected static output
inside the distribution, builds one wheel and one source archive, verifies their
contents, and writes hashes. Do not run this command from the user installation
path; Node/npm are build-time CI tools only.

## 4. Prove base plugin isolation

```bash
python -m pip download --only-binary=:all: \
  --dest dist/native-wheelhouse \
  'dist/native-candidate/wright_engineering-0.1.5-py3-none-any.whl[runtime]'
TEMP_ROOT="$(mktemp -d)"
uv run python scripts/test-native-hermes-install.py \
  --wheel dist/native-candidate/wright_engineering-0.1.5-py3-none-any.whl \
  --wheelhouse dist/native-wheelhouse \
  --hermes-home "$TEMP_ROOT/hermes-home" \
  --evidence dist/native-base-local.json \
  --base-only
```

The clean Hermes environment installs the base wheel through the package-plugin
fixture. It must discover the `wright` entry point while FastAPI, Uvicorn, MCP,
and private Wright distributions remain absent from the Hermes environment.

## 5. Run the complete clean lifecycle

```bash
uv run python scripts/test-native-hermes-install.py \
  --wheel dist/native-candidate/wright_engineering-0.1.5-py3-none-any.whl \
  --previous-wheel <previous-stable-wheel> \
  --wheelhouse dist/native-wheelhouse \
  --hermes-home "$TEMP_ROOT/hermes-lifecycle" \
  --evidence dist/native-lifecycle-local.json
```

The harness must:

1. install and enable the plugin through the Hermes package-plugin contract;
2. run `/wright start` and observe automatic isolated runtime installation;
3. verify challenged API/UI identity, Hermes connection, MCP transport, and catalog;
4. create/reopen a workspace and exercise multiple Hermes sessions;
5. stop and restart;
6. update from the previous stable public version;
7. exercise successful and refused rollback cases;
8. uninstall while preserving data;
9. reinstall and recover the workspace;
10. explicitly purge and prove no out-of-scope deletion;
11. fail if any forbidden executable or source import is observed.

## 6. Run platform acceptance

Run the same base and complete lifecycle commands on every platform in
`src/wright_engineering/compatibility.json`. Pull-request CI creates a separate
platform-local wheelhouse and evidence file on Linux, Windows, and macOS. A
platform is not publicly supported until its complete native result is green.

## 7. Run existing regressions

```bash
uv run python -m pytest
npm run test --workspace=apps/web
npm run build --workspace=apps/web
```

Engineering MCP server catalog validation remains the separate clean-container
process in `docs/mcp-catalog/mcp-server-testing-process.md`; do not add host MCP
software to native or Docker base installations.

## 8. Run merge gates

```bash
scripts/check-dev-merge.sh
scripts/check-prod-merge.sh
```

Native acceptance has no skip flag. A documented local host limitation may move
one platform execution to CI, but CI must pass it before the pull request is
green. Production release behavior is not complete until real released Hermes
public-artifact verification replaces the fixture evidence.

## Expected user experience after release

The final public documentation will use the exact package-plugin command exposed
by the compatible Hermes release, followed by:

```text
/wright start
```

The command must install and start Wright without repository detection, Git,
Docker, Node/npm, manual Python package commands, or a frontend build. The
current `hermes plugins install owner/repo` Git path is a legacy migration path,
not this acceptance subject.
