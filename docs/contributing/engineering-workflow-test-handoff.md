# Engineering workflow test handoff — September 7, 2026

This is the local development build, not a release or user-acceptance claim.
Open **Wright workflow evidence** in Wright, then click **Workflows** and
**Open workflow**. All examples below are ordinary files in its `workflows/`
folder. Agent/API runs use the same saved source and executor as the Run button.

- Workspace ID: `85cbd6b3-e9d1-474d-add2-36f6e95a7b51`
- UI: <http://127.0.0.1:5227/workspace/85cbd6b3-e9d1-474d-add2-36f6e95a7b51>
- Existing dashboard: <http://127.0.0.1:8765/#workflow-campaign>
- Working checkout: `D:/repos/wright/.local-run/epp-f02b-writer/wright`
- Branch: `codex/080-canonical-workflow-recovery`; changes remain a local batch.

## Start with these three workflows

| Open this file | Displayed name | What to do | What to inspect |
|---|---|---|---|
| `prompt-to-html.workflow.wflow` | Prompt to HTML | Select the prompt block, edit its prompt, and click Save & run (or Run when saved). | Open the generated HTML from Run details using the existing viewer. Review the prompt/response record. |
| `cad-working-copy-test.workflow.wflow` | CAD working copy test | Confirm the input is `cad-test/bracket.psm`, Edit is a working copy, and Solid Edge Local is selected. Run. | A copied sheet-metal model with 2.5 mm MaterialThickness, its native file and STEP export. The original file must remain unchanged. |
| `cad-result-handoff.workflow.wflow` | CAD result handoff | Select each block. The first modifies a working copy; the second takes its CAD model and exports it. Run. | Both tasks refer to the same copied model. Run details groups native representation and STEP under the model. Readbacks from both tasks must report 2.5 mm. |

Use the configured indexed naming policy for repeated tests. Review the explicit
overwrite option before selecting it. A green completion is not engineering
approval: inspect the model/result as well as the execution record.

## Additional verified examples

| File | Purpose and evidence | Repeat prerequisite |
|---|---|---|
| `cad-model-exports-test.workflow.wflow` | Fresh Solid Edge sheet-metal creation and native/STEP exports; native feature calls, file structure/digests and existing STEP viewer verified. | Solid Edge Local running. |
| `cad-unsaved-session-test.workflow.wflow` | Copy explicitly selected unsaved model content, then change thickness from 2.25 to 2.75 mm; original session and saved file preserved. | Select the intended owned open test model again. Its starting unsaved thickness must be 2.25 mm for this assertion. |
| `image-to-mcp-test.workflow.wflow` | Image to AI task to real Autodesk help search, then a Markdown report with tool-backed URLs. | Configured vision-capable model, Autodesk Product Help MCP, and bundled `engineering-help-image-test.png`. |
| `cad-export-review.workflow.wflow` | Export a CAD JPEG and feed its actual image contents into AI review; produces `reports/cad-preview-review.md`. | Select the intended owned `unsaved-copy.psm` in Solid Edge. Screenshot export can mark the open model modified. |
| `cad-export-state-test.workflow.wflow` | Copy the selected model, save its native file, export JPEG, and accurately report the provider's post-export modified state. | Reselect the owned source document after an MCP reconnect. Do not silently save or clear an unrelated dirty document. |

Open-document IDs are session identities. Reconnecting the MCP process may assign
new IDs while Solid Edge still has the documents open. Reselect the model in the
block instead of reusing an old ID. The workspace-file examples above avoid this
setup dependency. The native file and live document are representations of one
CAD result; a screenshot-induced modified state is reported without an implicit save.

## Repeatable campaign commands

Run from the working checkout using its `.venv/Scripts/python.exe`. The manifest
contains the actual workspace folder, so these commands target the registered
workspace rather than an unrelated temporary folder. Inventory is read-only;
`--run` and `--subset` execute the selected workflows.

```powershell
$campaign = 'artifacts/workflow-campaign'
$workspacePath = (Get-Content "$campaign/manifest.json" -Raw | ConvertFrom-Json).workspace
& .venv/Scripts/python.exe scripts/workflow-campaign.py --workspace $workspacePath --manifest "$campaign/manifest.json" --oracles "$campaign/oracles.json"
& .venv/Scripts/python.exe scripts/workflow-campaign.py --manifest "$campaign/manifest.json" --subset prompt-smoke --session api_1788293353_e8f8a9e8 --max-runs 1 --max-model-calls 1 --timeout 180 --concurrency 1
& .venv/Scripts/python.exe scripts/workflow-campaign.py --manifest "$campaign/manifest.json" --subset cad-handoff --oracles "$campaign/oracles.json" --session api_1788293353_e8f8a9e8 --max-runs 1 --max-model-calls 22 --timeout 600 --concurrency 1
```

The session shown is the existing local workspace session. A new workspace
session must use its actual ID. If the source changed, review and update the
source-bound assertions; do not bypass the mismatch check. Model-call limits are
execution bounds, not a vendor dollar-cost guarantee. Per-application leases
serialize cooperating runs; keep CAD batch concurrency at one.

Other named subsets: `cad-copy`, `image-mcp`, `cad-export-review`,
`cad-export-state`, and `workspace-smoke`. The two session-export subsets require
model reselection and fresh inventory first. `workspace-smoke` runs prompt,
working-copy and handoff cases with the default 40-call aggregate limit.

Portable bundles are in `artifacts/workflow-campaign/fixtures/smoke-20260907`
and `fixtures/image-mcp-20260907`. To restore into an **already registered** test
workspace, use `--restore <bundle> --workspace <its-folder> --manifest <manifest>`.
Restoration verifies digests and never overwrites different content. Re-inventory
that workspace before running. A fixture directory alone is not a Wright workspace.
Session IDs, application identities and credentials are not portable fixtures.

Every campaign attempt is a separate JSON record. `live-record-recheck` means
existing live evidence was checked again; it is not another application run.
Image and CAD file signature checks establish structure/digest only. Dimensional
and analysis assertions use recorded provider evidence, explicit units and
revision-bound numerical values, not an AI's description of success.

## Next actual batch

1. Repeat the three starter workflows above and review their UI together.
2. Run `image-mcp`, then the two session-export cases after selecting the owned
   source. Inspect the image, report, grouped outputs and modified-state notice.
3. Migrate the existing **Structural bracket** scenario once a solver is available.
   Its preserved criteria include mass 0.05–0.5 kg, density consistency at
   2700 kg/m³, convergence, and maximum stress 120 MPa. Bind those criteria to
   actual solver fields, units, resource revision, loads and boundary conditions.
4. Continue with the existing **Electronics enclosure cooling**, **Parametric
   manufacturing**, and **Chatter candidate review** manifests. Their original
   assertions remain in `manifest.json` under `planned_cases`; they are not
   represented as authored native workflows or live-qualified cases.

The existing benchmark plan specifies a target and domain quotas, not 100 ready
workflow definitions. Discovery found **30 saved files, 18 compiling**, including
authoring rehearsals, plus **four actual legacy scenarios** to migrate. We do not
duplicate examples to reach 100. The next campaign must author and review the
remaining distinct cases; historical benchmark qualification counts stay unchanged.

## Integration limits

- Solid Edge Local and Autodesk Product Help MCP have the live evidence listed
  above. The catalog also enables legacy Rivet, but native workflow execution
  does not use it.
- Onshape MCP is inactive/uninstalled in this workspace configuration, with
  `ONSHAPE_ACCESS_KEY` and `ONSHAPE_SECRET_KEY` unconfigured. No live cloud CAD
  operation is claimed.
- PyFluent MCP is inactive/uninstalled here. Recorded catalog validation requires
  a licensed Fluent session and gateway evidence. No live FEA/CFD solve is claimed.
- Cloud results, revision-aware modification/copy, remote export, async monitoring,
  cancellation and partial failure have separately labeled contract/simulated-browser
  evidence. A provider must expose the documented Wright adapter capabilities;
  arbitrary MCP servers are not automatically resource-aware applications.
- Generic local workspace export requires the provider's declared shared-filesystem
  export-path capability. Verified files are atomically published; failed or
  cancelled exports retain incomplete staging evidence and earlier verified files.
- Local CAD has no provider revision token. Wright pins document identity and uses
  cooperating-process leases, but cannot detect every external manual edit or
  enforce cross-host concurrency without provider revision support.
- Cancellation can stop observation before an external job stops. Inspect the
  job and retained run evidence before retrying; no automatic mutation replay.
- No new user acceptance, merged development build, or production release is claimed.

The requirement audit and exact regression/evidence references are in
`specs/080-canonical-workflow-recovery/evidence/engineering-results-audit.md`.
