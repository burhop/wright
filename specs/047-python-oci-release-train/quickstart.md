# Quickstart: Release Train Rehearsal

This feature never authorizes public publication. Run only the rehearsal and local validation paths.

## 1. Verify the active release identity

```bash
uv run python scripts/release-preflight.py --dry-run --tag v0.1.0 --source-commit "$(git rev-parse HEAD)"
```

Expected: normalized product/Python versions and a preflight evidence manifest. A dirty tree or mismatch fails.

## 2. Build and validate Python artifacts once

```bash
scripts/build-python-distributions.sh --dist-root dist/python-packages .
uv run python scripts/verify-release-evidence.py dist/release-evidence.json
```

Expected: exactly one wheel and one sdist, safe content manifests, strict metadata checks, and independent clean installs. CI repeats installs on Python 3.11-3.14.

## 3. Run the complete no-publication rehearsal

```bash
uv run python scripts/release-rehearsal.py \
  --dry-run \
  --tag v0.1.0 \
  --python-dist dist/python-packages \
  --output test-results/release-rehearsal
```

Expected: stage transitions, simulated promotion records, recovery decisions, and a self-consistent terminal `release_ready` manifest with `mode: dry-run`. No registry credentials are accepted and no external mutation occurs.

## 4. Run focused release tests

```bash
uv run pytest -q tests/release tests/test_python_package_metadata.py tests/test_python_package_distribution_build.py tests/test_publish_python_packages_workflow.py tests/test_release_policy.py
```

## 5. Validate the dev merge gate

```bash
bash scripts/check-dev-merge.sh
```

If Docker is available, the gate must build/smoke the exact local candidate. Clean-container engineering MCP validation remains separate under `docs/mcp-catalog/mcp-server-testing-process.md`.

## Failure drills

Use the rehearsal fixtures to inject a conflicting Python hash, bad OCI digest, blocking vulnerability, expired exception, mirror mismatch, partial promotion, and premature GitHub Release. Each must fail closed and write a redacted recovery decision without rebuilding or overwriting an immutable subject.
