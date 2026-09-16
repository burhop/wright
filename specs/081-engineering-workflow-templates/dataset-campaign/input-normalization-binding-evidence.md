# Input normalization and binding acceptance

September 12, 2026. DC004/DC004A now have a uniform attempt-specific evidence
contract and negative acceptance coverage. This completes input preparation and
mapping acceptance only. It does not grant workflow completion, physical
engineering validation or deployment authority.

The separate latest observation at
`.local-run/feature-081-live/input-binding-observations/latest-attempts-001/summary.json`
contains **30 complete mappings**. Every selected saved source, staged file,
canonical connection and normalization relationship was re-read and verified.
All 30 observed dataset fingerprints match the current corpus. The selection
snapshot records exact attempt/source/report identities. Existing enrolled
inputs, source files, policies and execution manifests were not edited.

The original audit is retained: its separate observational replay at
`input-binding-observations/audit-snapshot-001/summary.json` yields 23 complete
maps and explicitly leaves the seven old encoding failures unresolved. The
later repaired attempts supply the complete current mappings; this does not
retroactively certify the earlier corrupted inputs.

## Contract

`scripts/engineering_dataset_input_bindings.py` records every declared uploaded
file and SHA-256, its unchanged staged identity, each normalized file identity,
and the actual canonical input block/output port, connection, consumer block and
input port. Full UTF-8 text aggregation is verified using exact LF-normalized
byte spans; a role label or broad `derived_from` declaration is insufficient.
Opaque image uploads are represented as actual reference consumers. Editable
SVG originals are retained as provenance and linked to consumed PNG companions
through independently verified conversion receipts.

All 30 existing PNG files exactly match fresh offline Chromium rasterization
of their SVG originals. `render-engineering-dataset-images.mjs --verify-lineage`
saved source/output/reproduced hashes, operation/version identity, renderer
configuration and observation time in the separate
`.local-run/feature-081-live/image-normalization-lineage` directory. This mode
does not overwrite PNGs or manifests. Receipts explicitly state that this was
a reproduction observed now, with **no historical execution claim**.

Future preparers emit immutable `input-bindings.json` sidecars and record their
hashes in staging reports. Enrollment validates the complete map before saving
or granting a new definition and adds the contract/evidence identity to the
new execution manifest. The persistent runner revalidates those maps before
any HTTP dispatch. Existing manifests remain immutable and legacy-compatible;
their complete mappings are separately observed, rather than silently added
to an existing grant or runner fingerprint.

Validation reconstructs mappings from actual staged bytes and the saved source.
It rejects omitted raw files, invented consumer ports, changed spans, changed
input hashes, corrupt image output or operation identities, missing retained
original relationships, encoding corruption and evidence from another attempt.
The runner tests assert zero HTTP calls when these checks fail.

## Verification and operation

The combined corpus, mapping/negative, persistent runner and affected canonical
preparer suites passed **83 tests**. Ruff passed for changed Python scripts.
All image comparisons ran with HTTP/HTTPS requests blocked. No native CAD,
solver, supplier or printer action was dispatched by this work.

For another installation, run the offline image verification once before
enrolling new mapped attempts:

```text
node scripts/render-engineering-dataset-images.mjs --verify-lineage
```

Missing or nonmatching conversion receipts remain unresolved and prevent new
mapped enrollment. `observe_engineering_input_bindings.py` can publish a new
dated read-only observation from an explicit audit/selection snapshot. It
requires a fresh output directory and never updates campaign run counters.
These preparation/runner changes require no API or Hermes restart.
