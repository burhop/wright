# Separate 130 mm wall-dock variant — checkpoint 088

10 October 2026. **Status: separate input revision and workflows saved. The first
run completed research but timed out producing intent. A material-handoff
correction is saved and software-tested; its live run remains pending.**

## User outcome

The user-selected 130 mm variant now has its own saved Wright workflow. Its
front lips and 20 mm cable notch follow the new front datum; the original width,
rear wall, mounting slots and other protected requirements remain. The original
75 mm design and run are unchanged.

[Open the corrected R5 workflow in Wright](http://127.0.0.1:5250/workspace/a6d46bd6-8b43-4263-ae5f-99d8d9924ee5?workflow=canonical&workflowPath=workflows%2Fbarcode-reader-wall-dock-130-native-inventory.workflow.wflow).
It has not yet run. The [initial attempt and preserved research](http://127.0.0.1:5250/workspace/a6d46bd6-8b43-4263-ae5f-99d8d9924ee5?workflow=canonical&workflowPath=workflows%2Fbarcode-reader-wall-dock-130-r5.workflow.wflow)
remain separately inspectable through **Open working view**.

## Prepared and exercised

- Added the full [R5 input amendment](../../../examples/process-interfaces/sheet-metal-wall-dock/shelf-depth-revision-r5.md)
  and [engineering brief](../../../examples/process-interfaces/sheet-metal-wall-dock/engineering-brief-r5.md).
  A separate input snapshot retains the original files byte for byte and appends
  the explicit new decision. Original concept dimensions are identified as historical.
- Instantiated the existing sheet-metal template and accepted a new source
  through Wright's existing services. The fourteen existing research/design/
  validation/review stages reuse the canonical runner and configured providers.
  No executor, vendor adapter or global behavior policy was changed.
- Created a distinct workspace validation profile and baseline. All twelve
  original checks and mandatory/review obligations remain; three STEP envelope
  checks enforce the revised 110 by 130 by 60 mm envelope. Selected stock/radius,
  K and relief text follows R1/R3 rather than the original concept placeholders.
  The local simulator destination is pinned to this exact new campaign.
- Read the actual Solid Edge provider: connected, version226.00.01.04, no open
  documents and one matching native5052 material identity. Read-only calls made
  no CAD changes. The existing native application was not terminated.
- Started one new isolated run. Research, the material summary and exact supplier
  evidence copy completed, retaining21 outputs. The intent step then failed with
  `MODEL_TIMEOUT`: the configured response transport did not finish in180 seconds.
  There is no completed intent or review checkpoint, and no CAD creation occurred.
  Completed evidence remains available; this failure is not a manufacturing verdict.
- Found a concrete handoff defect before CAD: the old profile expected
  `/materialsQuery/materials/0/name`, while the AI summary used
  `/material_query/materials/0/name`. The actual native provider returns
  `/materials/0/name`. A separate corrected source binds `cad.list_materials`
  directly and preserves its structured response; a new existing-validator gate
  checks identity, complete pagination and uniqueness before intent/CAD. No model
  reformats this inventory. Final engineering review obligations remain intact.
  See the [visible contract](../../../examples/process-interfaces/sheet-metal-wall-dock/material-inventory-contract.md).
- Ten targeted tests and Ruff pass. They retain original profile obligations,
  reject synthetic75mm and out-of-tolerance depths, and execute the shared validator
  with native-shape, AI-wrapper, incomplete and ambiguous inventory fixtures. Only
  the complete native shape releases the fixture consumer. These tests do not
  claim live native execution of the corrected workflow or measured CAD geometry.
- Sixty-five preserved files, including all54 earlier run records, the original
  scenario files and the75mm workflow source, match their pre-work hashes.

## Exact execution evidence

Private control folder:
`D:/repos/wright/.local-run/process-interfaces-083/mechanical-engineering-20261008`.

| Item | Identity / receipt |
| --- | --- |
| Accepted source | `workflows/barcode-reader-wall-dock-130-r5.workflow.wflow` |
| Source digest | `4ad34dc4b57d094cd2f3c2618266d47bb7f6a17bd1f91451a6882f9157549d2d` |
| New run | `4b28952f46424dbab031a0d4f10a1672` |
| Preparation / start | `dock-130-preparation-088.json`, `dock-130-start-088.json` |
| Final failed observation | `dock-130-stage-088-3266b2d7.json` |
| Corrected saved source | `workflows/barcode-reader-wall-dock-130-native-inventory.workflow.wflow` |
| Corrected source digest | `57f04f07118e96a3ae8688be9031d35ba266ec5628643d2e6079db869b57adde` |
| Corrected preparation | `dock-inventory-preparation-088c.json`, not started |
| Profile tests / final audit | `tests/dock-inventory-088c.xml`, `dock-130-audit-088.json` |
| Provider readback | `solid-edge-fabrication-probe-e8c133b5.json` |

The ordinary catalog readiness remains blocked on template qualification. The
existing integration authorization permits only this exact new digital subject
and its pinned tools/inputs; it does not promote the template to qualified or
authorize live supplier work. Current services remain API8067 and UI5250/build45.

## What still needs to happen

Address the observed model timeout before another full attempt; the transport's
180-second model limit is distinct from the compiled step's timeout. Evaluate
the existing configuration/owner before changing shared behavior. Prove the new
direct inventory handoff live. Inspect the new intent and supplier constraints before the declared
exact review. A synthetic response can be applied only after observing that
new checkpoint and checking its evidence; it is not human engineering approval.
Then retain actual native geometry, independent measurements, genuine flat
export, dimensioned drawing/inspection documents and all applicable holds.
No native model, manufacturing pass, final release or completed variant is
claimed by this checkpoint. Full goal, swim-lane integration and final fresh
cross-process regression remain open. Presentation work remains deferred.

Two read-only helper attempts had local issues: a wildcard path did not expand
and a source-text read initially used the Windows default encoding. Corrected
folder filtering and explicit UTF-8 reads preserved the source bytes; these
were not Wright or provider failures. The corrected-source preparation also
caught a duplicate assessment port and an AI-context input left on a direct tool
block; both were corrected before source acceptance. Restricted test execution
first failed to allocate a temporary folder, then stalled before its async cases.
Only its identified two Python processes were stopped. A fresh authorized run
outside that restriction completed all ten cases in2.8seconds. Fixtures and
earlier receipts remain preserved; no application or service was stopped.
