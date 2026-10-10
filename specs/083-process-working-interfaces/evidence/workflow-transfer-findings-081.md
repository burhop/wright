# Identify setup requirements when reusing a workflow

10 October 2026. Shared product repair and retained portability reconciliation.
Slide-deck work remains deferred.

## What changed for the user

The import inspection previously repeated setup warnings without showing which
file or capability each warning concerned. The backend supplied the exact
dependency identity, but the dialog omitted it. Users had to search technical
JSON to associate the warning with the process.

The existing dialog now presents each finding with its affected dependency,
the backend's explanation, and a readable severity label. Technical codes and
complete requirements remain in expandable details. Long identities wrap within
the existing dialog. The client checks the optional dependency field and the
backend's two allowed severity values before displaying them.

This uses the existing export/inspect/import service, source revision identities
and Wright styling. Importability, local qualification and execution readiness
remain backend-owned. Changing the destination invalidates the displayed
inspection; an existing destination still disables import. The UI introduces no
capability substitution, permission, execution or instruction policy. It shows
exact identities; friendly capability names and direct setup navigation are not
implemented by this repair.

## Before and after

- [Original failure](../../../artifacts/ui-walkthrough/mechanical-engineering/20261010-200-transfer-diagnostics-before/report.html):
  the saved wheel definition exports and inspects, but the warning's dependency
  is absent from the displayed findings. The recording stops at that defect.
- [Wheel transfer inspection](../../../artifacts/ui-walkthrough/mechanical-engineering/20261010-201-transfer-diagnostics-wheel/report.html):
  seven steps enter through Workflows, open the existing saved process, download
  its source/manifest, inspect at a fresh destination, see named requirements,
  recheck an existing destination and return to the editor.
- [Thermal transfer inspection](../../../artifacts/ui-walkthrough/mechanical-engineering/20261010-202-transfer-diagnostics-thermal/report.html):
  the same seven steps pass on the different existing analysis workflow at a
  1159-pixel viewport. Actual raw screenshots were visually inspected.

These two UI journeys perform source-only export and read-only inspection.
They do not import, edit the original definitions, execute engineering work or
qualify provider health. Three fresh blank workflows were created across the
recordings through the normal Workflows entry. Backend diagnostic content is
retained verbatim; it is not an agent-generated engineering assessment.

44 affected tests pass without skips, including exact dependency association,
findings without a dependency, malformed diagnostic rejection, stale-inspection
clearing, backend-held import, selected export contents and source-page
integration. Type checking and production build43 pass. Served HTML and three
entry assets match the build. All walkthrough structures validate and browser
diagnostics are empty. The existing large-chunk build advisory remains.

## Retained portability evidence reconciled

The interrupted audit076 was confirmed stopped and then completed without a
second import or engineering run. It checks the retained actual transfer:

- 34 saved instruction bodies and typed policy remain unchanged despite different
  destination defaults and a later local source revision.
- 44 reference files match their bundled bytes and both workspace copies.
  Six pinned validation profiles and their requirement baselines match.
- Provider/model dependencies remain external and require local qualification.
- The saved working interface arrived as an inactive candidate. The destination's
  later saved interface has its own local workspace, interface and revision
  identity. Initial import created no trusted build or run.
- The actual earlier browser inspection/import requests agree with the import
  receipt. JSON transport changed 32 integral float spellings; numeric values,
  source bytes, file bytes and the inspected/imported digest relationship agree.
- Current repeat-import inspection rejects existing assets and publishes no
  source. All 54 prior run records remain unchanged.

The schema excludes live authority records. The audit additionally checks the
known private token and selected prior run identities; this is not universal
secret detection for arbitrary user-authored content. Historical transfer and
local UI rebuilding retain their original evidence scopes. A matching file hash
does not establish live tool availability or engineering correctness.

Exact receipts are in
`.local-run/process-interfaces-083/mechanical-engineering-20261008/workflow-portability-audit-076.json`
and `transfer-audit-081.json`. The latter also verifies all 64 latest wheel outputs
and both original engineering sources remain byte-identical. Only the existing
Solid Edge process22448 was observed; it was left untouched. No CAD application
was launched. API8067/PID84296 is unchanged; UI5250/PID69612 serves build43.

## Where to try it

Open the [isolated Wright workspace](http://127.0.0.1:5250/workspace/a6d46bd6-8b43-4263-ae5f-99d8d9924ee5),
open a saved workflow, and choose **Export / import workflow**. Download its
source and dependency manifest, select that downloaded file, enter a fresh
destination filename, and choose **Inspect before importing**. The findings
should identify the affected files and capabilities. Import remains a separate
explicit action and does not establish run readiness.

The full goal remains incomplete. This closes the retained audit interruption
and repairs one transfer usability defect. Reload/disconnect recovery, the dock
requirement decision, actual swim-lane integration and the remaining goal-wide
acceptance work retain their separate scope.
