# Passive engineering representations — T044

**Date:** 1 October 2026. **Scope:** shared readers, exact-subject owners,
native/managed transport, client and UI controls. Full engineering workflow and
rendered-browser proof remains T047.

`ProcessArtifactAccess.preview` first uses the existing recorded-result or
prepared-input reader, including source/run membership and exact byte hash. It
then parses and serializes in the existing workspace bounded executor, with a
30-second administrative deadline. It does not execute tools, interpret firmware,
alter files, review results or replay work. Raw downloads retain original bytes.
The native endpoint and managed presentation bridge share this operation and
the `process.results` permission; foreign runs and revoked grants remain denied.

## Supported view and limits

- STL retains the existing shared 3D geometry reader.
- UTF-8 G-code: nominal G0/G1 and planar XY G2/G3 extrusion; explicit layer
  comments or actual extrusion heights, relative/absolute axes and extrusion,
  inch/mm units, resets and per-tool extrusion state. Arc chord error is bounded
  to 0.02 mm. Extruding helical or unsupported coordinate semantics refuse the
  view. Non-extruding travel updates position without inventing extrusion.
- A 3MF is read in memory without extracting files. One explicit G-code entry is
  required when multiple plates exist. Duplicate, unsafe, encrypted, excessive or
  unsupported archive entries refuse the view. Original entry names are checked
  before Windows ZIP filename normalization.
- Bounds: 32 MiB source, 20 MiB G-code, 10,000 layers, one million segments,
  two million bounded lines, 2,048 archive entries and 100 MiB total declared
  uncompressed archive bytes. Passive serialized views are at most 64 MiB.
  Feature evidence has separate count/length bounds.
  Motion command text is at most 4 KiB; inert comment lines may be up to 64 KiB.
  The first read of the correctly configured actual package exposed two valid
  long preset comments (5,725 and 6,850 characters). Separate command/comment
  bounds retain those comments without executing their embedded text; dedicated
  tests preserve motion, total line and feature-evidence rejection.
- Known model/support comment labels are a small format allowlist. Other labels
  remain unclassified. The displayed evidence includes package/entry hashes,
  parser version, method, arc approximation, unknown labels and excluded
  unlayered extrusion. A preview establishes no machine/material approval.
- Scalar CSV reader: at most 2 MiB, 10,000 rows and 50 columns. Explicit x/y/z/value
  fields must be distinct, finite and present. The UI retains the actual table
  and requires explicit numerical display axes. It does not infer units,
  interpolate a field, invent geometry or mark solver output accepted.
- Unsupported formats/conditions retain exact download and a useful explanation.
  STEP and compressed VTU are not claimed as supported mesh previews here.

## Checks and actual data

```powershell
.venv/Scripts/python.exe -m pytest packages/workspace_service/tests/test_process_representations.py packages/workspace_service/tests/test_process_artifact_access.py apps/api/tests/test_process_interface_artifacts.py -q -p no:cacheprovider --tb=short --basetemp=.local-run/process-interfaces-083/t044-final-qualified --junitxml=.local-run/process-interfaces-083/t044-final-qualified.xml
.venv/Scripts/python.exe -m pytest apps/api/tests/test_process_ui_surface_authority.py -q -p no:cacheprovider --tb=short --basetemp=.local-run/process-interfaces-083/t044-surface --junitxml=.local-run/process-interfaces-083/t044-surface.xml
```

78 passes in 20.33 seconds and 32 passes in 41.04 seconds; two existing
Starlette/httpx/AnyIO deprecation warnings in each group. No skips.

From `apps/web`:

```powershell
node ../../node_modules/vitest/vitest.mjs run src/components/common/ProcessUIKit.spec.tsx src/services/process-client.spec.ts src/components/process-interfaces/CommonProcessView.spec.tsx
node ../../node_modules/typescript/bin/tsc --noEmit -p tsconfig.app.json
```

157 passes across three files in 30.77 seconds; TypeScript passed. Positive
component proof includes a 30-layer slider, true Z positions and evidence.
The test environment reports unavailable canvas/WebGL; it checks controls and
fallback, not rendered 3D pixels. Ruff on owned Python files passed.

An actual backend-produced sliced package and OASiS scalar CSV were read separately;
their exact hashes, counts, ranges and parser provenance are retained in
`artifacts/process-interfaces/083/20261001-engineering-readers/reader-smoke.json`.
The package is tiny provider qualification geometry, not the assigned
replacement part. Solver data is a tiny qualification case, not the assigned
heat comparison or accepted engineering result. Parser/API tests use clearly
controlled recorded-run fixtures. Required live engineering/UI proof stays open.

The package successfully read is the first backend probe with default settings;
it is **not** the correctly configured PETG package. The latter includes an
unsupported `G380` motion command, so its passive preview correctly refuses the
entire view and retains the raw download. Its exact digest and diagnostic are
also recorded in `reader-smoke.json`. Vendor command support was not invented to
turn that fallback into a pass.
