# CAD tasks in workspace workflows

The existing AI task with MCP block can work with a CAD model when its selected,
workspace-enabled server exposes the CAD document contract. It remains an AI task
with a prompt and optional references. CAD configuration lives in the same saved
`.workflow.wflow` file; there is no separate editor or model database.

## Model and file outputs

- **Create a new model** uses the native filename to select the supported creation
  family. The current Solid Edge adapter supports part, sheet metal and assembly.
- **File in this workspace** opens an explicit workspace file.
- **Open in Solid Edge** selects a specific open document, including unsaved work.
- **CAD model from another block** passes the live document identity through a
  typed connection on the same server. AI response text is a separate output.
- Existing models can be edited directly or copied with their current in-memory
  contents. Working copies leave the original open and unchanged.
- Native saves and exports use workspace-relative filenames, with indexed or
  overwrite policies. A final CAD step must save a native model or export a file.
  AI summary files are optional.

Export choices come from `cad.list_providers` capabilities. Wright does not claim
that every application exporter is exposed by its MCP server. The current local
Solid Edge server advertises Parasolid, STEP, STL, flat Parasolid, flat DXF and
JPEG screenshots; native saves support PAR, PSM, ASM and DFT. Availability can
also depend on document type and a persisted flat pattern.

## Execution contract

`workflow_cad.py` resolves and pins the target before the AI operates. It rejects
cross-server handles, closed documents, attempts to target another document,
unsupported formats and paths outside the workspace. CAD tasks on one server
execute serially. Source documents are checked before model calls and again when
the CAD step starts.

The Solid Edge server supplies opaque, process-lifetime document identities that
survive Save As. Restarting that server invalidates saved open-session selections;
refresh and select the document again. A workspace-file source can reopen a
saved model on later runs.

Creation recipes are validated in preview mode before a mutation is allowed.
The AI sees the server's field errors and suggested corrections. Unrelated
creation schemas are omitted from model requests. Wright performs native saves
and exports itself against the pinned document, then verifies workspace files,
size and digest. A narration claiming success is insufficient.

CAD results appear in the existing run details with native/export labels and
file-opening controls. The live model appears separately, including dirty state.
Run records retain prompt, tool arguments, results and produced files. Changes
that occurred before a failure are not rolled back automatically.

## Local integration

The served editor is the existing `codex/080-canonical-workflow-recovery` checkout
at `.local-run/epp-f02b-writer/wright`, web port 5227 and API port 8018.
The companion local `D:/repos/SolidEdgeMCP` changes add `cad.save_document`, native
copy handling, stable identities and the document/edit tools to creation mode.
Build that server before testing this feature; preserving the old executable
does not enable native save/copy.

Tests: `test_workflow_cad.py`, workflow execution/AI task regressions,
`CadTaskOptions.spec.ts`, existing graphical editor tests, and the companion
server's document identity and automation boundary tests. Live walkthroughs
under `artifacts/ui-walkthrough/cad-deliverables` preserve failures and repairs.
Their report distinguishes code-level verification from real CAD results.

## Verified locally — 2026-09-06

The real Solid Edge 2026 server created an ordered sheet-metal bracket with healthy
tab and flange features, saved `cad-test/bracket-001.psm` (286,720 bytes), and
exported `cad-test/bracket.step` (13,611 bytes). The run record reports completion.
An old browser check rejected non-text extensions after that completed run; its
CAD completion regression now passes.

`CAD working copy test` in Wright workflow evidence completed through the UI:
open `cad-test/bracket.psm`, make an indexed native copy, change MaterialThickness
from 2 to 2.5 mm, reread variables/rebuild, save
`cad-test/bracket-modified-002.psm` (278,528 bytes), and export
`cad-test/bracket-modified.step` (13,703 bytes). The original SHA-256 remained
`5e83159797ab19999742c59645b751d112e70fb4eb0e2e61fe0f1d3311fbfc08`.
Open-session selection and copy creation were also exercised; upstream live-model
passing and active-window protection have automated regression coverage.

The existing STEP text fallback opened the file after fixing its missing session
context. This does not establish a 3D STEP preview. Flange-length editing remains
limited: this recipe's 60 mm flange driver was not exposed reliably by the server;
the AI stopped without making that requested edit. Supported native variables can
be edited, as the thickness test demonstrates. Other export formats and CAD kinds
have not all been live-tested in this change.

Backend implemented, UI integrated, and the above browser paths verified locally.
User acceptance is pending. These working-tree changes have not been pushed,
merged, or released. The original three-block visual walkthrough remains saved
with CAD model and native/STEP deliverable controls.
