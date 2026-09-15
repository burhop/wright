# Sheet-metal CAD input completeness revision R3

2026-09-12. This is additive fictional input preparation and canonical setup,
not a CAD run or an engineering correctness qualification.

## Actual failure and prerequisites inspected

Sheet case 01 attempt 003 reached research, native material inventory, intent and
the local review, then blocked before native creation. Its retained
`manufacturing-intent.md` left relief width, outside/inside/virtual-sharp dimension
references and bend-deduction versus K-factor priority unresolved. It also called
runtime part names and indexed output paths missing human inputs, although those
belong to the prepared workflow and later CAD allocation respectively.

Read-only ordinary API tool discovery retained the exact native recipe schemas
in `.local-run/feature-081-live/campaign-execution/sheet-native-recipe-schemas-r3.json`:

- `cad.create_sheet_metal_from_recipe` schema digest
  `9d3a7add2ad9bba532aeec2aa55bd8dd869ea87665f43d196ee6fe01b13f99e6`.
- `cad.validate_sheet_metal_recipe` schema digest
  `145a04f3033e12b7ce14b9ee4335537f8df8e478d8c24b11efbd1d8db10d5b2e`.

The actual contract requires thickness, inside radius, neutral factor, relief
width/depth, explicit feature geometry and nine flat-pattern settings. It permits
square flange relief, and documents outside dimensions and native coordinate
conventions; a general one-flange offset is not evidence for arbitrary geometry.
No native CAD kernel or document operation was called for this audit.

## Human choices and research coverage

Each existing case now has `cad-design-choices-revision-r3.md`. The originals,
R1 stock bounds and R2 native C10 mapping remain byte-preserved. New explicit
company choices cover outside virtual-sharp datums; K-factor development priority
with conflicting listed deductions disclosed; bounded evaluated relief sizes;
all native flat-pattern settings; through-cut and corner interpretation; physical
bend order; and required part labels. They do not fabricate supplier properties,
temper equivalence, tolerances or certification.

The complex chassis additionally defines vent-bank coordinates, four clearance
holes forming two removable screw interfaces, open tray corners and lid height.
Its original ambiguous 2 mm clearance is explicitly revised to an outside-plane
offset, with actual bare-sheet air gap `2-T` and minimum 0.25 mm; it is never
reported as achieving 2 mm internal air clearance. The original 430/434 mm widths
and 84 mm height are preserved. Loose fasteners remain outside the sheet-metal
purchase and physical fit remains untested.

The research binding now retrieves eight pages. Detailed
[relief guidance](https://sendcutsend.com/faq/what-are-your-bend-relief-requirements/)
supplies the missing width/depth guidance, while
[channel requirements](https://sendcutsend.com/faq/what-are-your-channel-bend-requirements/)
describe conditional thin-sheet exceptions that the earlier overview omitted.
[Deformation guidance](https://sendcutsend.com/guidelines/bend-deformation/) and
[processing limits](https://sendcutsend.com/materials/processing-min-max/) complete
the declared research questions. Every new attempt must retrieve actual current
evidence and evaluate applicable conditions. A conditional exception is not a
supplier approval, and missing/failed mandatory DFM or native geometry still blocks.

All sixteen raw HTML/text files are declared research expected files, respecting
the runtime's existing per-step limit. Source-bound retrieval also creates and
hashes `supplier-evidence.json`; each paged read validates its exact digest.
The final collection explicitly includes that manifest and all sixteen raw files.
No retrieval page or artifact is dropped to fit the limit. Research observations
remain bounded; the retained raw material stays on disk.

The intent prompt now receives exact nominal part/output contracts and must
complete its native-rule table using R3. Final indexed file allocation remains
the owning CAD task's responsibility. The original six stages, six edges,
independent native measurement gates, revision bounds, real PSM/STEP/developed-DXF
requirements and all three approvals remain. Supplier gates still use explicit
test destinations and `manufacturing_release=HOLD`, `supplier_acceptance=unverified`.

## Revision identity and verification

Immutable prior manifests, prior dataset identities and retained original-file
hashes are recorded under
`tests/datasets/engineering-workflows/revisions/2026-09-12-sheet-cad-r3/`.
The publication receipt is
`.local-run/feature-081-live/campaign-execution/sheet-input-revision-r3-publication.json`.

| Case | Current dataset digest |
| --- | --- |
| sheet-metal-supplier-handoff-01 | `f18523eb2ffee3edceb65912229c89dc69cb0fc77a4f87bce12b0a79d64c08a5` |
| sheet-metal-supplier-handoff-02 | `0eeea4d90e5cda10100b9451c24dd32c2fb3a7c90cc60bf47353051daa1f30b0` |
| sheet-metal-supplier-handoff-03 | `60f051a5a088b83d747be4dcb957e1287873bfd1a8451ca0d79ed2d6fc2b2d87` |

The running observer registered all three revisions. Counters stayed
`30 / 12 / 2 / 0`; revision registration did not add a scenario or run.

Five isolated tests passed across `test_sheet_cad_input_preparation.py` and
`test_sheet_dataset_input_revision.py`; Ruff passed for both tests and changed
preparer/revision scripts. Tests exercise all three complete canonical graphs,
original stage/edge retention, actual staged input hashes and R3 normalization,
nominal output contracts, bounded source artifact declarations, approval scope,
unchanged old input bytes, historical identities and refusal before staging when
the revised input is undeclared. No API or native modeling occurred in these tests.

After the root task confirmed the coordinated API restart, all three fresh
attempt-004 instances were created through the normal template API, prepared,
saved and enrolled. The dispatch manifest is
`.local-run/feature-081-live/campaign-execution/sheet-metal-attempt-004.json`.
Read-only checks in `sheet-metal-attempt-004-staging-verification.json` prove
10/10/13 compiled stages, original API task IDs and edges retained, all 19 tool
pins current per case, exact source/dataset/input/grant hashes and empty output
directories. Attempt-003 sources and grants remain unchanged. No workflow was
dispatched and no new output-complete or run count was claimed.

## Case 01 storage-failure recovery: attempt 005

The root task reconciled case 01 attempt 004 after the C: drive filled during
research publication. Its retained run `672827db9d6e45deaf418f596650234a` had
completed twenty reference retrieval/read calls and retained seventeen source
files; no CAD, solver or handoff had begun. See
`campaign-execution/sheet004-storage-reconciliation.json`. That interrupted run,
its artifacts and grants remain unchanged.

Only case 01 received fresh attempt 005, using the same R3 dataset identity and
ten-stage graph. The enrollment utility now supports an explicit `--scenario`
selector. The single-case manifest is `campaign-execution/sheet-metal-attempt-005.json`.
It includes the complete `wright.input-bindings.v1` mapping emitted and validated
by the updated preparer/enroller, including original-to-normalized-to-consumer
relationships. Case 02/03 attempt-004 sources, grants and unstarted outputs were
preserved.

`sheet-metal-attempt-005-normal-preparation-verification.json` records successful
ordinary source/policy preflight, all eleven staged input hashes and nineteen
exact tool pins, original API IDs/edges, unchanged R3 identity and an empty new
output directory. CAD capability preflight requires three actual read-only
`cad.list_providers` calls; the probe allowed only that tool through the selected
native gateway and stopped its isolated child afterward. Modeling, saves,
exports, solver operations, supplier actions and workflow dispatch were prohibited.
The probe used the same selected executable directory prepended by the demo
launcher; the standalone diagnostic shell did not inherit that launcher's PATH.

The root task subsequently queued the immutable attempt-005 case for dispatch.
Verification did not alter that queued source, grant or manifest, and does not
claim a successful engineering run.
