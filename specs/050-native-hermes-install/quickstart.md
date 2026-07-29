# Quickstart: Native Agent-Manager Candidate Validation

This quickstart validates locally built artifacts and thin manager adapters. It
does not publish to a public registry or manager marketplace.

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

The tests cover manager-neutral layout/state, compatibility, process identity,
runtime update/rollback, uninstall/purge, package contents, the stdlib-only
Hermes bootstrap, and the Codex MCP profile.

## 3. Build the candidate once

```bash
uv run python scripts/build-native-runtime.py \
  --output dist/native-candidate \
  --evidence dist/native-candidate/evidence.json
```

The builder runs the locked frontend build, packages only inspected static
output, and writes wheel/source hashes. Node/npm are build-time tools only.

## 4. Prove the real Hermes adapter boundary

```bash
python -m pip download --only-binary=:all: \
  --dest dist/native-wheelhouse \
  'dist/native-candidate/wright_engineering-0.1.6-py3-none-any.whl[runtime]'
TEMP_ROOT="$(mktemp -d)"
uv run python scripts/test-native-hermes-install.py \
  --wheel dist/native-candidate/wright_engineering-0.1.6-py3-none-any.whl \
  --wheelhouse dist/native-wheelhouse \
  --hermes-home "$TEMP_ROOT/hermes-home" \
  --wright-home "$TEMP_ROOT/wright-home" \
  --plugin-source hermes-plugin-wright \
  --evidence dist/native-base-local.json \
  --base-only
```

The harness installs the adapter through released Hermes' real Git plugin
command. Plugin import remains standard-library-only. After installation, the
harness removes Git from the audited runtime PATH.

## 5. Run the complete Wright lifecycle

```bash
uv run python scripts/test-native-hermes-install.py \
  --wheel dist/native-candidate/wright_engineering-0.1.6-py3-none-any.whl \
  --previous-wheel <previous-stable-or-lower-immutable-candidate-wheel> \
  --wheelhouse dist/native-wheelhouse \
  --hermes-home "$TEMP_ROOT/hermes-lifecycle" \
  --wright-home "$TEMP_ROOT/wright-lifecycle" \
  --plugin-source hermes-plugin-wright \
  --evidence dist/native-lifecycle-local.json
```

The harness must install/start/status/doctor/stop/update/rollback/uninstall,
remove/reinstall the Hermes adapter, preserve/reopen user data, and perform the
separately confirmed purge. Git may appear only in the Hermes adapter
install/update phase; no Wright lifecycle phase may invoke it.

## 6. Prove the direct Codex MCP profile

```bash
uv run python -m pytest -q \
  tests/native_runtime/test_manager_profiles.py \
  tests/native_runtime/test_mcp_bridge.py
```

The Codex profile launches the same installed Wright STDIO bridge or connects to
the same Streamable HTTP endpoint. It does not route through Hermes or store
Wright data beneath manager state. OpenClaw is future work and is not part of
this validation.

## 7. Run existing regressions

```bash
uv run python -m pytest
npm run test --workspace=apps/web
npm run build --workspace=apps/web
```

Engineering MCP catalog validation remains the separate clean-container process
in `docs/mcp-catalog/mcp-server-testing-process.md`; do not add host MCP software
to native or Docker base installations.

## 8. Run merge gates

```bash
scripts/check-dev-merge.sh
scripts/check-prod-merge.sh
```

Native acceptance has no skip flag. Production verification consumes the
published Hermes Git tag, published Wright artifact, and every other publicly
claimed manager-adapter identity.

## Expected Hermes experience

```text
hermes plugins install https://github.com/burhop/hermes-plugin-wright --enable
/wright start
```

Git is an explicit Hermes prerequisite. `/wright start` installs and starts the
packaged Wright runtime without repository detection, Docker, Node/npm, manual
Python package commands, or a frontend build.
