# Installed workflow authoring continuation

Prepared before navigation. Browser trace remains in the private proof root because authentication headers are sensitive.

## 2026-10-02T22:39:12.010Z UTC â€” Compact keyboard and scale

URL: http://wright.localhost:8037/workspace/083-heat-live-005?workflow=canonical&workflowPath=workflows%2Feditor-verification-083-004.workflow.wflow
Action: Use a 720 by 550 viewport at two-times page scale, then select Text input with Enter.
Controls: Workflow view, Fit workflow to view, Text input
Expected: Compact view and keyboard inspector remain available.
Actual: Measured visual viewport scale is 2; view selector, Fit control and keyboard-selected input inspector are available.
Status: pass
Screenshots: screenshots/raw/S13.png; screenshots/annotated/S13.png

## 2026-10-02T22:39:12.565Z UTC â€” Concurrent save protects both edits

URL: http://wright.localhost:8037/workspace/083-heat-live-005?workflow=canonical&workflowPath=workflows%2Feditor-verification-083-004.workflow.wflow
Action: Change local specimen text, update the same scratch source through its real CAS endpoint, then Save.
Controls: Source, Apply, Save
Expected: Conflict retains local text and does not overwrite the other saved edit.
Actual: A real 409 conflict preserves the 102 mm local edit and the 101 mm concurrent saved edit.
Status: pass
Screenshots: screenshots/raw/S14.png; screenshots/annotated/S14.png
