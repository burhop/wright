# Sheet-metal dataset binding preparation

## Current September 12 input revision and attempt-003

The three active packs now include an additive `stock-selection-revision-r1.md`.
Each permits bounded fictional stock changes selected from actual current
supplier evidence. The original prompt, context, policy, image and CSV bytes are
unchanged; exact prior manifests, file hashes and old/new dataset digests are in
`tests/datasets/engineering-workflows/revisions/2026-09-12-sheet-stock-r1/`.
Case 02 additionally includes `native-label-revision-r2.md`, with its prior R1
manifest and changed digest retained under `2026-09-12-sheet-native-r2/`.

R1 selects the closest eligible actual thickness, then radius, inside explicit
human bounds. Supplier K factor, effective radius, relief and feature/flange/
press limits remain sourced constraints for the selected stock; absent facts
stay unresolved. No fixed fictional K factor is active. R2 permits the actually
observed Materials-DIN `Steel - Unalloyed:1.0301 , C10` only as a geometric native
label; it does not assert rolling condition or supplier grade equivalence.
The 137-entry read-only native inventory is retained in
`.local-run/feature-081-live/sheet-material-r1-probe.json` and
`sheet-material-r1-probe-page2.json`. Both status observations had no active
document; no CAD creation occurred.

Fresh intent guidance prevents a sourced H32 offering from becoming an invented
customer requirement, separates missing unrequested physical properties from
required geometric identity, follows paginated native inventory and retains
runtime-authoritative indexed filenames. All original native DFM/geometry,
bounded correction, developed-DXF and exact approval gates remain. Both
simulated handoffs explicitly retain `manufacturing_release=HOLD` and
`supplier_acceptance=unverified`; HOLD cannot waive a mandatory failed check.

The current evidence provider is the separately installed paged server
`dde38145-6c72-492e-ba24-8cae07a770f1`, not the earlier two-tool evidence record.
`scripts/enroll-sheet-metal-dataset-campaign.py` creates actual template
instances, preserves request identity, prepares from their immutable original
stages, saves via the normal API and enrolls current source/input/tool pins.
It never dispatches a workflow. Attempt-003 retains 10/10/13 canonical stages.
The handoff manifest is
`.local-run/feature-081-live/campaign-execution/sheet-metal-attempt-003.json`.

The earlier sections below retain preparation history. The initial concept-only
proposal in `sheet-metal-concept-addenda/` was not activated; the stock-first
R1/R2 uploads above are authoritative for the new attempts.

Prepared 2026-09-12 using the live workspace tool discovery endpoint, checked-out
native provider contracts, and the original six-stage canonical template.
These are executable-source drafts, not completed dataset runs or public MCP
qualification. No sheet-metal geometry, supplier upload, cart, or purchase was
created during preparation.

## Prepared artifacts

- `scripts/prepare-sheet-metal-dataset-campaign.py`
- `tests/datasets/engineering-workflows/bindings/sheet-metal-supplier-handoff.json`
- `.local-run/feature-081-live/sheet-metal-bound-drafts/<scenario>/attempt-001/bound.workflow.wflow`
- The adjacent `staging-manifest.json` files contain exact discovered tool names,
  complete input/output schemas and SHA-256 identities, input/definition hashes,
  expected output roles, and the requested isolated approval destinations.

Each source preserves `intent_document`, `solid_edge_cad`,
`measured_design_check`, `export_and_verify`, `supplier_preview_approval`, and
`cart_quote_handoff`, including all six original control connections. The
existing CAD-to-check revision path remains bounded at two corrections. The
existing native inspection and developed-DXF integrity gates remain active;
passing them does not increment the campaign's deferred `valid_data` metric.

The preparer adds actual supplier research and installed-material inventory
before the intent document, an exact local intent approval before CAD, and a
real collection step after both supplier checkpoints. The base/lid case adds
separate lid creation, inspection and export. There are ten steps for the dock
and trough and thirteen for the chassis. No original stage is truncated.

All profiles, prompts, manufacturing policies and CSVs are combined with named
source boundaries into a staged human-context document. The original files
remain intact. The original PNG concept connects as an image to intent and
native design tasks; its SVG companion is retained as an original upload.
No shape recipe is pre-generated: the CAD stage must derive its actual native
recipe from the human inputs, reviewed intent and observed capabilities.

Scenario-specific scope is retained:

- Dock: open-sided shelf, back and split front lips, rounded mounting slots,
  cable notch and customer coordinate frame; four parts in the test preview.
- Trough: two walls, outward return flanges and four longitudinal bends, plus
  every mounting-table slot and interior service clearance; six parts.
- Instrument: separate base tray and skirted lid, authoritative panel CSV,
  styling/vent intent and the supplied 75 mm keepout resolution; two of each
  part. Additional output roles require both PSMs, both STEP files and both
  genuine developed DXFs, including indexed revision filenames.

## Exact execution contracts

The selected server is `solid-edge-mcp-burhop`, provider `solid_edge`.
Native `CadTask` binds a new `.psm` document, controls its identity and save/export
paths, and validates the sheet-metal recipe before creation. The measured
check uses the exact upstream native model; it cannot substitute a successful
model response for native observations. Exports target the checked document
and use `step`, `flat_dxf` and `screenshot_jpeg`.

Selected live schema identities (2026-09-12):

| Tool | SHA-256 |
| --- | --- |
| `cad.create_sheet_metal_from_recipe` | `9d3a7add2ad9bba532aeec2aa55bd8dd869ea87665f43d196ee6fe01b13f99e6` |
| `cad.validate_sheet_metal_recipe` | `145a04f3033e12b7ce14b9ee4335537f8df8e478d8c24b11efbd1d8db10d5b2e` |
| `cad.list_materials` | `2707a36f7201d6c46a58b0355141774d7deee29b7c72b92cb1859604ff417127` |
| `cad.verify_inspection_requirements` | `93dd4e6b074f4741e18f1ce442b61b06955d7c812b6b1f8058ade96d7e936773` |
| `cad.save_document` | `58f582fc5fc4665a49c92dc2af14b25f307ff894383f1b19df8b0b6a3964eff2` |
| `cad.export_document` | `8d60a573e82bf09cc9921a3ebce9df574b24ec8a7edafc2786d8d7daaeed9c86` |

The allowed tool set also includes provider/document discovery, connection,
material/feature/variable/face/frame inspection, and body-extents measurements.
The selected evidence server `7c9c0579-1b48-4b01-9f85-8104011edeb8` exposes
`retrieve_public_references` and `collect_artifact_manifest`. These fixed
operations require an exact staged copy of their executing source and confine
outputs to the same attempt. Retrieval retains actual raw HTML, source URLs,
timestamps/hashes and extracted text from configured HTTPS origins. Collection
hashes only named nonempty same-attempt outputs. Sheet metal uses no Blender
script execution. The separate Blender guard choice remains pending.

The creation schema explains native pre-flange spans, profile-relative flange
edges, full-thickness flange sketch offsets and explicit flat-pattern settings.
These are provider contract constraints, not precomputed geometry. A bare
installed `5052` label cannot establish the requested H32 temper or supplier
certification. Recipe fields never substitute for observed folded dimensions.

All approvals use the existing durable continuation mechanism. The intent gate
binds Wright's fixed `LOCAL_REVIEW_BINDING` and review-only destination. Preview
and quote gates bind the fixed `TEST_HANDOFF_BINDING` and:

`test://081-engineering-datasets-v1/supplier/<scenario-id>`

Receipt paths are confined beneath the scenario attempt output root, with
separate `supplier-preview.json` and `cart-quote-handoff.json`. Quantities and
part itemization are explicit. Price and delivery remain `not_quoted`;
simulated receipts never represent a supplier offer or acceptance.

## Current prerequisite evidence and gaps

The original native server exposed 55 tools. Its initial probe evidence was:

- Repository revision: `f58a783d2bfad4cff97c818bb63d42c1485d305a`.
- Binary SHA-256: `f52ad9d5cfceeda35dd3440d0f0900b80a0b82a0166c6006eb9e846815411cdc`.
- Tool-list SHA-256: `2eda3a3c240a8a0e8e5f93443f5432e08de99b37f184077733bd3187996bc4b4`.
- Evidence: `.local-run/feature-081-live/sheet-metal-status-probe.json`.

Read-only `cad.get_status` reported `isAvailable=false`, `isConnected=false`
and `MK_E_UNAVAILABLE (0x800401E3)`. The SDK additionally rejected that response:
the advertised schema requires nullable `version` and `activeDocument` fields,
but the disconnected response omitted them. This is a native contract issue,
not evidence of a successful backend probe.

An authorized hidden `cad.connect(startIfNeeded=true, visible=false)` attempt
timed out after 122 seconds; no `Edge` process was observed afterward. Evidence:
`.local-run/feature-081-live/sheet-metal-connect-probe.json`. No geometry was
created in that failed probe.

These two local prerequisites were repaired on September 12. Explicit hidden
native startup connected Solid Edge version226.00.01.04. A hashed isolated
working-tree snapshot of SolidEdgeMCP preserves required nullable JSON fields;
the external dirty repository was not changed. The selected build now exposes
59 tools. Actual native SDK and Wright Gateway status calls passed. Evidence:
`.local-run/feature-081-live/solid-edge-repaired-native-gateway-qualification.json`
and `docs/mcp-catalog/followups/2026-09-12-solid-edge-null-results.md`.
This proves local backend connectivity, not full sheet-metal execution.

The evidence operations passed actual retrieval of all four supplier URLs and
manifest generation through direct MCP and native Wright Gateway in a clean
selected container. Source SHA256 is
`f978c1bc58fe66aaf2e6fc39859f05a7317ece9c34a2b94c25a289a65130439e`.
Evidence is retained under
`.local-run/feature-081-live/engineering-evidence-qualification/attempt-002/`;
`installation.json` beside it records normal API registration and demo-only
enablement. No dependencies were added to the base Docker image.

All three real template API instances are saved and enrolled. The pending
serial batch is `campaign-execution/sheet-metal-attempt-001.json`; preparation
has not dispatched a CAD operation or incremented the campaign run counter.

The current server provides no native Draft or dimensioned drawing creation
tool. JPEG views are clearly labeled inspection views, not manufacturing
drawings. The three user prompts require PSM/STEP/developed DXF rather than a
native `.dft`; no unsupported drawing artifact is claimed. If native drawings
are added to acceptance later, that requires an actual drawing adapter.

The workspace must fall under the server's configured
`CADMCP_SOLID_EDGE_ALLOWED_ROOTS`; the draft workspace does not change that
credential/configuration. Current demo setup provides that isolated root.

The [clean-container MCP testing process](../../../docs/mcp-catalog/mcp-server-testing-process.md)
still applies to public qualification. This preparation neither runs that loop
nor changes catalog qualification, nor adds Solid Edge to Wright's base image.

## Reproduction and validation

Draft preparation only:

```powershell
.venv\Scripts\python.exe scripts/prepare-sheet-metal-dataset-campaign.py --attempt preparation-004 --evidence-server-id 7c9c0579-1b48-4b01-9f85-8104011edeb8
```

For an actual campaign workspace, first create the canonical instance through
the normal template API, then pass its saved source with `--instance-source`,
its scenario ID with `--scenario`, the correct `--workspace-root`, and a fresh
attempt. Save and enroll the resulting exact source through the campaign's
normal API/authority sequence. Preparation never dispatches, enrolls, or starts
a run and therefore cannot increment execution counters.

Three tests in `test_sheet_metal_campaign_preparer.py` pass. They prove canonical
compilation, original stage/control preservation, bounded revision and all three
approval gates, every human table/policy/prompt plus PNG ingestion, per-part
outputs, and absence of generated CAD artifacts. They do not prove host execution.

The supplied research stage retrieves current primary pages before freezing
design choices. SendCutSend states that bending requires material-specific
rules, file-format requirements and flange/bend limits; those facts are not
prevalidated customer dimensions. Relevant current primary entry points are the
[bending requirements](https://sendcutsend.com/faq/what-are-your-bending-requirements/),
[bending service](https://sendcutsend.com/services/cnc-bending/) and
[bending calculator](https://sendcutsend.com/bending-calculator/). No material
thickness, radius, finish, live price or lead time has been copied into the
fixtures as a claimed supplier fact.
