# Sheet01 forming-input repair and attempt-007 preparation

2026-09-12. This change supplies additive fictional engineering inputs and
prepares a fresh integration attempt. It does not claim CAD completion,
manufacturability, supplier acceptance or a successful full workflow.

## Preserved failure and diagnosed cause

Run `99a0e8f5cdae44a3afa87e644c888abc`, Sheet01 attempt-006, reached research,
installed material inventory, intent generation and its exact automatic test
review, then stopped before CAD. Its intent recorded incomplete forming/tool
access for the split front lip, a notch/relief in the 5.9944 mm half-die-width
caution region, and a 0.0879 mm-per-bend difference between selected K-based
development and the separately listed supplier deduction. Approval did not
override its explicit needs_input status. No native document was created.

The original intent and run remain at
`artifacts/engineering-workflow-datasets/output/sheet-metal-supplier-handoff-01/attempt-006/`.
The original supplier and dimensional requirements were not removed to obtain
a passing result. The new revision changes which supplied company criteria
support nominal CAD evaluation and which supplier confirmations remain later.

## Additive company policy and preparer changes

`tests/datasets/engineering-workflows/scenarios/sheet-metal-supplier-handoff/01-barcode-reader-wall-dock/company-fabrication-capabilities-r4.md`
is an explicitly fictional, human-uploadable Parcelwood prototype capability
statement. It adds a declared small-brake/segmented-tool setup, numerical
clearance criteria and the actual sequence: left short lip, right short lip,
then rear wall. The two front intervals and rear interval belong to two
parallel stations, not a four-wall box or four-bend returned channel. Tool
support terminates at the interrupted bend ends; it never bridges the notch.

The policy preserves all original geometry and R1/R3 inputs. It requires
current stock evidence, distinguishes unsupported-bend relief provisions
from distortion-free feature criteria, retains all die-width cautions, and
does not override known applicable supplier hard limits. The current
[supplier deformation guide](https://sendcutsend.com/guidelines/bend-deformation/)
discusses both reliefs for unsupported bends and distortion around die lines;
neither is supplier approval of this part. Native inspection must establish
the actual remaining bend intervals, relief/cut topology, dimensions and
developed geometry. Declared scalar clearances are not measured tool sweeps.

R4 reconfirms one controlling K-based CAD method. The source deduction
difference is retained as a supplier confirmation issue, never silently
averaged, excused as tolerance or represented as source agreement. The new
intent can be ready_for_geometry_verification only with complete applicable
inputs and no known mandatory conflict. Physical fabrication and supplier
acceptance remain unperformed/unverified.

`scripts/prepare-sheet-metal-dataset-campaign.py` now applies the actual uploaded
company sequence instead of hardcoding the Sheet03 sequence. Conditional
guidance preserves the company/supplier/observed-evidence distinctions through
intent, CAD and independent inspection. It cannot transfer one company's
permissions to another or override needs_input. Six original tasks and six
connections, bounded rework, native PSM/STEP/genuine-DXF outputs, exact intent
review and both simulated supplier gates remain intact. No runtime gate was
weakened and no supplier action was enabled.

## Input identity, tests and staging evidence

The existing additive-input publisher preserved the original manifest and
original-file hashes under
`tests/datasets/engineering-workflows/revisions/2026-09-12-sheet-capabilities-r4/sheet-metal-supplier-handoff-01/`.

- Prior dataset: `f18523eb2ffee3edceb65912229c89dc69cb0fc77a4f87bce12b0a79d64c08a5`.
- Revised dataset: `33d0e09a773f7941fe83c1daafd34524c82e87d5b0254825b25d8b0ae62e0bb8`.
- R4 upload: `ed73ef7775bcfe77c5c6f998036cc64791b9bbe9eaecbf9c72730f49da447bd1`.

All 15 focused tests passed across `test_sheet_company_capabilities.py`,
`test_sheet_cad_input_preparation.py`, `test_sheet_dataset_input_revision.py`
and `test_sheet_metal_campaign_preparer.py`. They check additive lineage,
arithmetic/bounds, all three prepared graphs, exact inputs, stages, approvals,
source retrieval and unknown/failed-evidence restrictions. Ruff passed for
the changed preparer/tests and bounded verification scripts. A first test
asserted a formula spelling absent from otherwise equivalent prose; the test
was corrected without changing the published input or any engineering gate.

Following coordinated authorization while the API was idle, attempt-007 was
created through the normal template API, prepared, saved and enrolled. Its
immutable replacement manifest is
`.local-run/feature-081-live/campaign-execution/sheet-metal-capabilities-replacement-01-007.json`,
SHA-256 `715555cd872b5f9c4955c2079ec036f33e3dfcfe507d2146849d597bcab78200`.
Source digest is `84a6eef639a75f65d3fad1579b0bb39fcee90b3b8324e815233172021720df54`;
grant digest is `27ce1f6319387b5a3ae370bf5c8f524a8ccab105e1692753c2341139a58e09b6`.

Evidence beside that manifest uses the same stem:

- `-staging-verification.json`: 10 compiled stages, 19 current tool pins,
  12 exact inputs, original tasks/edges and three approvals retained; 221
  prior files and six prior grants unchanged; empty output directory.
- `-normal-preparation-verification.json`: the production preparation and
  grant-authorization path passed. Its isolated MCP allowed only three
  read-only cad.list_providers calls after initialization and stopped cleanly.
  No CAD model call, workflow dispatch or supplier/browser call occurred.
- `-preflight.json`: zero errors, four static output-role warnings. The generic
  scanner omits structured CAD save/export and approval receipt declarations.
- `-output-route-review.json`: all four warned roles are declared by the actual
  native-save, STEP/DXF export and simulated-receipt routes inside the exact
  output root. This is a route review, not evidence those files were produced.

Attempt-007 is prepared for a new root-controlled execution. The independent
checks may still identify a genuine CAD construction, measurement or supplier
conflict. No run, output-completion or engineering-validity count is advanced
by this preparation; manufacturing_release=HOLD remains mandatory.
