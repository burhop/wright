# Quickstart: Chatter and Model-Enabled Rivet Scenarios

## Purpose

This loop has two evidence paths:

1. **Normal gates** use a tiny generated forest plus deterministic CAD/CAM fixtures. They prove contracts, runtime isolation, gateway mediation, Rivet execution, cancellation, reporting, UI, and packaging without private data or weights.
2. **Real local qualification** is explicit and opt-in. It consumes reviewed user-owned source/data outside the Wright repository, writes all outputs to an ignored external directory, and produces a non-redistributable offline Wright model package only after parity passes.

Neither path generates G-code, controller settings, spindle commands, or physical action.

## Normal offline verification

Run the focused model, gateway, scenario, API, and UI tests from the Wright checkout:

```powershell
uv run pytest packages/model_registry/tests packages/workspace_service/tests/test_rivet_capabilities.py packages/workspace_service/tests/test_rivet_run_evidence.py packages/workspace_service/tests/test_engineering_scenario_contracts.py packages/workspace_service/tests/test_engineering_scenario_service.py tests/e2e/test_chatter_model_scenario.py tests/security/test_chatter_boundaries.py tests/packaging/test_chatter_distribution.py
pnpm --dir apps/web test -- --run
```

The generated fixture must live only in test-owned temporary state. No `.npz`, model archive, private dataset, or qualification environment may appear in Git status.

## Inspect the bundled source record

Open **Engineering Models**, search for **Wright Chatter**, and verify that it is visible but not installable before local qualification. The entry must show:

- private/offline-only source;
- exact source and Dataset 2 identities;
- internal-use, non-redistributable terms;
- serving artifact/runtime/test evidence absent;
- the explicit local qualification recovery action.

No download or environment change occurs during inspection.

## Run real local qualification explicitly

Prerequisites are independently reviewed local paths:

- a clean source checkout at the exact pinned revision;
- Dataset 2 with the exact pinned digest;
- exact feature-095 evaluation/environment-lock evidence; qualification deterministically derives and freezes the 80/20 seed-42 membership from the immutable Dataset 2 bytes;
- a trusted qualification Python environment containing the reviewed Data Vault training stack;
- a new output directory outside the Wright checkout.

Example shape (replace every placeholder deliberately):

```powershell
uv run python scripts/qualification/qualify-chatter-model.py `
  --source <clean-pinned-chatter-source> `
  --data-vault-source <reviewed-data-vault-source> `
  --dataset <immutable-dataset2-parquet> `
  --reference-evidence <reviewed-feature-095-evidence-json> `
  --environment-lock <reviewed-environment-lock> `
  --output <outside-repository-output-directory> `
  --acknowledge-internal-only I-UNDERSTAND-NO-REDISTRIBUTION
```

The command must stop before training/export when any identity differs. It must not contact AWS, MLflow, another cloud service, or a paid resource. On success the output directory contains bounded evidence and one `.wright-model.zip`; none is copied into Git.

## Import and enable the exact package

In **Engineering Models**:

1. Choose **Import offline package**.
2. Select the produced archive.
3. Review internal-use terms, exact byte effects, artifact digests, adapter/resource compatibility, limitations, and parity evidence.
4. Confirm the one-use import plan.
5. Run every mandatory vector.
6. Enable the exact `screen_chatter_candidates` task for the selected workspace.

Export remains blocked because redistribution is prohibited. A failed vector, incompatible adapter, or stale evidence keeps the installation unready.

## Review and run the scenario

In the Rivet engineering scenario library:

1. Open **Chatter candidate review**.
2. Review the exact CAD MCP, simulated CAM MCP, and engineering-model capability separately.
3. Confirm that preflight reports all three ready, resources available, simulation-only status, and no physical authority.
4. Start the reviewed graph.
5. Inspect each discrete candidate's invariants, uncalibrated score, threshold, margin, applicability, warnings, and provider evidence.

The only possible selection label is **selected for human review**. Near-threshold, out-of-population, or invariant-failing candidates cannot be selected. The report contains no machine instructions.

## Cancellation and recovery

Cancel during load or inference to verify:

- run authority is revoked first;
- the active adapter receives cancellation within one second;
- late output is ignored;
- model and MCP resources are released;
- the run ends cancelled with `clean` cleanup or explicit possible residue and an inspect-before-retry action.

After any package, adapter, vector, schema, MCP validation, workflow, fixture, threshold, resource, or policy change, create and review a fresh preflight. Wright must not silently rebind the old run.

## Final hygiene checks

```powershell
git status --short
git ls-files | Select-String -Pattern '\.(joblib|pickle|pkl|npz|onnx|pth|pt|wright-model\.zip)$'
git diff --check
```

Expected result: only reviewed source/contracts/tests/docs are tracked, and no private or generated model payload is present.
