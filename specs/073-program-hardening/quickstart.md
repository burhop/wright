# Quickstart: Program Hardening Verification

All commands run from the repository root. Normal verification must remain
offline and must not require credentials, a GPU, proprietary applications,
hardware, or paid services.

## 1. Validate planning contracts

```bash
uv run python -m pytest -q tests/program_hardening/test_contracts.py
```

## 2. Exercise diagnostics and state compatibility

```bash
uv run python -m pytest -q \
  packages/workspace_service/tests/test_support_diagnostics.py \
  apps/api/tests/test_support_diagnostics_api.py \
  tests/native_runtime/test_program_state_compatibility.py \
  tests/program_hardening/test_docker_persistence.py
```

Expected: adversarial secrets/private payloads are absent, preview/export is
scope-bound and single-use, schema 16 is supported, predecessor state migrates,
newer unsupported state is preserved/quarantined, and every supported Compose
profile declares the durable named-volume contract.

When Docker is available, the persistence suite also replaces and restarts a
disposable Wright container while retaining its named volume. When Docker is
unavailable it records a non-supporting skipped host result; the deterministic
manifest contract still runs and cannot be promoted to live Docker evidence.

## 3. Exercise the UI tiers

```bash
npm run test --workspace=apps/web -- --run \
  SupportDiagnosticsPanel \
  RivetScenarioReport \
  CapabilityLibrary \
  EngineeringModelLibraryPage

npx playwright test tests/ui-integration/engineering-program-journey.spec.ts
```

The local API/system tier is the deterministic Python journey:

```bash
uv run python -m pytest -q tests/e2e/test_engineering_program_journey.py
```

## 4. Repeat the human walkthrough

Follow `docs/testing/engineering-program-usability.md`. Record exact browser,
viewport, artifact/runtime identity, elapsed time, failed step, recovery action,
and evidence level. Do not label this an external moderated study.

To capture the full human-repeatable report, set an ignored timestamped
`WRIGHT_WALKTHROUGH_ROOT`, enable the explicit walkthrough, and run only the
`@walkthrough` case in
`tests/ui-integration/engineering-program-walkthrough.spec.ts`.

## 5. Run non-publishing lifecycle/release checks

```bash
uv run python -m pytest -q tests/native_runtime tests/release
```

These tests/rehearsals may build local artifacts. They must not merge `main`,
publish a package/container, create a GitHub Release, or mutate production.

## 6. Run the authoritative development gate

```bash
scripts/check-dev-merge.sh
```

The exact tree that passes this command is the only tree eligible for the
single no-fast-forward merge into `dev`.
