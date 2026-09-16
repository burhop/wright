# Thirty-pack input and binding acceptance audit

**Follow-up:** the original snapshot and findings below remain historical.
The later [normalization and mapping acceptance](input-normalization-binding-evidence.md)
records 30 complete current-revision maps, verified image replay lineage and
negative runner tests, completing DC004/DC004A's input-preparation scope.

September 12, 2026. This bounded read-only audit covers the 30 current input
packs and the latest enrolled case found for each scenario. It does not execute
tools, alter sources/grants, validate engineering results or update counters.
The exact snapshot is
`.local-run/feature-081-live/campaign-execution/thirty-input-binding-audit.json`.
The selection records its manifest, attempt, source, input and policy identities;
newer preparations remain separate revisions.

| Requirement | Evidence | Disposition |
| --- | --- | --- |
| DC004: normalize uploads, preserve originals and snapshot identities | 30/30 retain every declared original file under its original basename with exact granted SHA-256. All source/dataset/template and staged-file identities match. PNGs are canonical image inputs. Seven assembled contexts have a confirmed encoding error. | Open |
| DC004A: every input mapped, normalized provenance recorded, negative runner coverage | All 30 manifest `input_bindings` maps remain empty. Individual staging reports record many aggregation relationships, but use inconsistent shapes and do not provide a complete per-file graph mapping. Existing corpus/runner tests do not prove missing-map rejection or SVG-to-PNG lineage. | Open |
| DC005D: preserve every original block and bind output roles/exact operations | 30/30 preserve exact original task IDs reconstructed from each normal API template-origin record. All required step lists match; every expected role has at least one declared output path. Every direct tool and all enrolled allowlists match current ordinary tools API identities. Existing preparers/selected-host evidence retain operation sources/contracts and revisions. | Complete for binding preparation |

This closes DC005D's preparation work, not DC005's remaining complete readiness
work, DC010's actual executions, DC011's served editor acceptance or parent
engineering qualification. File-name role coverage is a declaration check; it
does not claim that those files exist or that their contents are correct.

## Findings

**I30-1 — HIGH: seven normalized human contexts contain mojibake.**
The originals are intact, but each listed canonical `assembled-context.md`
contains the exact text produced by decoding its UTF-8 `context.md` bytes as
CP1252 and then staging that altered text. The audit compares the actual bytes;
this is not an inference from a tool being installed.

- `lightweight-equipment-bracket-01/02/03`, attempt-002.
- `robot-tracking-diagnosis-02`, attempt-003.
- `sensor-fan-harness-01/02/03`, attempt-002.

Their preparers use `read_text()` without explicit UTF-8 in the context assembly
path. Repair the reusable text-reading boundary and add a regression containing
the relevant non-ASCII engineering characters. Stage fresh attempts rather
than editing enrolled contexts or grants. This is input preservation work,
independent of later engineering-output content validation.

**I30-2 — MEDIUM: input-to-canonical provenance is not complete and uniform.**
The runtime validates all granted file hashes and every declared canonical
input, but neither that nor complete file inventory proves that each manifest
input has an explicit consumer or recorded normalization edge. Heat/bracket
reports label assembled context by role without listing source documents.
Other preparers use basename lists, full staged-path lists, or the complete
`manifest.files` object as `derived_from`. Robot/harness/Pi assembly reads the
text fields, although that broad metadata object also lists images. Thus its
image entries must not be interpreted as actual text aggregation.

All 30 SVG originals and PNG companions are retained; the canonical graph uses
the PNG. `scripts/render-engineering-dataset-images.mjs` contains a deterministic
offline rasterization path, but does not emit a source-image SHA, output-image
SHA and operation/version relationship for each conversion. The corpus test
checks SVG/PNG presence and PNG magic bytes, not that normalization lineage.
Record explicit raw-file/normalized-file/canonical-block-and-port relationships,
including source/output hashes and transformation identity. Do not equate an
unused editable original with a missing engineering operation; its role is
retained original provenance, which should be represented explicitly.

**I30-3 — MEDIUM: DC004A's requested negative acceptance tests remain absent.**
`test_engineering_dataset_corpus.py` proves 10×3 complete uploadable packs.
`test_run_engineering_dataset_campaign.py` proves persistent dispatch/recovery
identity and refusals, and policy tests reject ungranted canonical inputs.
These do not test a manifest file omitted from a binding map, corrupted
normalization lineage or retained original image/document relationships.
Add those focused cases when the complete mapping contract is implemented.
No broad test rerun was used as a substitute for these missing requirements.

## Current selected attempts

| Family | Selected attempt |
| --- | --- |
| Printed replacement part | 001 |
| Raspberry Pi enclosure | 002; source-authoring repair for 003 remains separate |
| Sheet metal supplier handoff | 003 |
| Lightweight equipment bracket | 002 |
| Sensor interface PCB | 001 |
| Parametric drill jig | 004 |
| Robot tracking diagnosis | 003 |
| Heat spreader sizing | 004 |
| Sensor fan harness | 002 |
| Water heater sizing | 002 |

The printing execution guard and Pi authoring ambiguity are actual execution
prerequisites; current explicit graph/pin/role declarations do not resolve them.
The one completed robot chain is useful normalization/execution evidence for
that case, but cannot close all 30 input-binding requirements.
