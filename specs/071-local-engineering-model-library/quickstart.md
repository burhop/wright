# Quickstart: Local Engineering Model Library

This guide describes the intended implementation and verification sequence. The model library is distinct from **Model Setup**, which configures a conversational LLM provider.

## 1. Start with the bundled catalog offline

Launch Wright normally with networking disabled. Open **Engineering Models**.

Expected:

- The generated Wright test model, provisional external candidate, and representative blocked entries appear from bundled metadata.
- Each card shows engineering task, source revision, trust/readiness, license, artifact size, runtime, platform/resource needs, evidence, and limitations.
- The PointNet candidate remains **Needs review** until Gate D evidence is complete.
- Opening or filtering the catalog starts no download and no runtime.

## 2. Generate and import the deterministic fixture

Use the test helper to generate a small affine model package in a temporary directory outside Git. The archive contains a manifest, JSON coefficient data, typed test input/expected output, attribution, and digests.

Preview the import. Confirm that Wright shows:

- exact package, variant, files, digests, and total bytes;
- no network, token, license acceptance, runtime install, service, driver, or global setting effect;
- the already approved deterministic adapter identity;
- staging, verification, test, activation, rollback, and cleanup effects.

Confirm the plan. Expected lifecycle:

```text
prepared -> running -> verifying -> testing -> activating -> succeeded
```

The installation becomes **Ready** only after the exact mandatory vector passes.

## 3. Exercise typed inference through Wright

Enable the model's affine-prediction task for one test workspace, then open a reviewed Rivet workflow containing its typed Wright capability node.

Expected:

- discovery returns a namespaced capability such as `wright_model__wright-affine-test__predict`;
- Rivet sends typed input to Wright's gateway, not to the adapter process;
- gateway policy/audit binds the call to the immutable session, workspace, installation, adapter, and task;
- the adapter returns bounded typed output and unloads cleanly;
- another workspace, stale binding, disabled model, invalid input, and direct adapter attempt fail closed.

## 4. Prove interruption and recovery

Repeat import with injected truncation, wrong digest, excess bytes, cancellation, disk exhaustion, and restart at each durable transition.

Expected:

- no partial artifact is marked verified;
- no incomplete installation is visible or loadable;
- cancellation cannot later publish success;
- retry either safely resumes with a matching strong validator or restarts;
- startup reconciliation quarantines unknown bytes and reports missing verified content;
- cleanup reports `clean`, `residue`, or `unknown` truthfully.

## 5. Prove update, rollback, and reference-safe removal

Generate fixture revision 2 with changed coefficients and vectors. Preview the semantic diff, then inject a failing test.

Expected:

- revision 1 remains active when revision 2 fails;
- a successful revision 2 activation preserves revision 1 for rollback while referenced;
- rollback reuses verified cached bytes and reruns its standard test;
- disabling/removing a workspace binding does not delete content;
- uninstall removes active availability but preserves referenced content;
- purge identifies exact blocking workspace/workflow/run/export references and succeeds only after safe detach/archive and zero leases.

## 6. Prove deterministic offline portability

Export the public deterministic installation, inspect the archive, and import it into a fresh temporary Wright data root with networking disabled.

Expected:

- manifest, safe redistributable artifacts, license/attribution, digests, runtime requirement, vectors, and bounded evidence are present;
- secrets, host paths, source tokens, runtime endpoints/commands, mutable authority, and private catalog data are absent;
- the imported package passes the same verification/test path and produces the same result within declared tolerance.

## 7. External candidate evidence (explicit opt-in only)

External validation is not part of normal gates. If Gate D permits the bounded probe, use `.local-run/` for the exact `keras-io/PointNet` revision and never stage downloaded files.

Required evidence before approval:

1. exact selected paths, byte sizes, and SHA-256 digests match the manifest;
2. license/attribution and redistribution decision are explicit;
3. no repository code, pickle, native library, macro, plugin, or undeclared file is needed;
4. the separately reviewed adapter loads the artifact CPU-only within its resource envelope;
5. real deterministic vectors validate input shape/order/units, label order, finite output, tolerance, timing, and cleanup;
6. offline repeat uses zero network bytes;
7. removal cleans test state without touching unrelated user content.

If any item fails, keep the candidate evaluation-only or replace it. Do not weaken the general contracts.

## 8. Focused verification

The implementation loop should run, in order:

1. model package/schema/policy contract tests;
2. source, storage, migration, lifecycle, runtime, and gateway tests;
3. API and UI component/service tests;
4. mocked and local browser journeys, including accessibility;
5. schema/security/docs/package checks and all existing model/gateway regression tests;
6. Loop 071 focused gate and evidence record.

The authoritative `scripts/check-dev-merge.sh` remains deferred until Loops 069-073 are complete on `codex/rivet-engineering-program`, immediately before the single merge to `dev`.
