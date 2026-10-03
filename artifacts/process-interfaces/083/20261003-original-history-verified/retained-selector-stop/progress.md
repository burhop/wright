# Installed original-history walkthrough

Prepared before navigation. Browser trace remains in the private proof root because authentication headers are sensitive. Expected unavailable-model responses are disclosed; original and copied run/evidence files are checked independently.

## 2026-10-03T04:16:18.521Z UTC â€” Installed workspace entry

URL: http://wright.localhost:8038/workspace/083-heat-live-005
Action: Open workspace.
Controls: Workflows
Expected: Workflows visible.
Actual: Workflows visible.
Status: pass
Screenshots: screenshots/raw/S01.png; screenshots/annotated/S01.png

## 2026-10-03T04:16:19.227Z UTC â€” Shared authoring entry

URL: http://wright.localhost:8038/workspace/083-heat-live-005?workflow=canonical
Action: Click Workflows.
Controls: Workflow files
Expected: Editor controls without active print demo.
Actual: Editor controls present; Print a part demo absent.
Status: pass
Screenshots: screenshots/raw/S02.png; screenshots/annotated/S02.png

## 2026-10-03T04:16:20.546Z UTC â€” Original failed pumpkin — exact history

URL: http://wright.localhost:8038/workspace/083-heat-live-005?workflow=canonical&workflowPath=workflows%2Fprompt-to-print-ce662210b77a.workflow.wflow&printDemoRun=runs%2Fprompt-to-print-ce662210b77a%2F20260926T165217Z-b6f67611dec7.json
Action: Open exact historical workspace link.
Controls: Back to workflow, Open saved artifact, Open saved run record
Expected: Exact recorded run/status/error and result links; no execution controls.
Actual: 997873e33f2143ac90d6bfb9fe02c2e2; failed; 3 exact results and 3 artifact links.
Status: pass
Screenshots: screenshots/raw/S03.png; screenshots/annotated/S03.png

## 2026-10-03T04:16:20.787Z UTC â€” Original failed pumpkin — editor return

URL: http://wright.localhost:8038/workspace/083-heat-live-005?workflow=canonical&workflowPath=workflows%2Fprompt-to-print-ce662210b77a.workflow.wflow&printDemoRun=runs%2Fprompt-to-print-ce662210b77a%2F20260926T165217Z-b6f67611dec7.json
Action: Click Back to workflow.
Controls: View saved result, Workflow files
Expected: Exact workflow editor restored.
Actual: Exact workflow editor and saved-result reopen control visible.
Status: pass
Screenshots: screenshots/raw/S04.png; screenshots/annotated/S04.png

## 2026-10-03T04:16:21.365Z UTC â€” Original failed pumpkin — read-only reopen

URL: http://wright.localhost:8038/workspace/083-heat-live-005?workflow=canonical&workflowPath=workflows%2Fprompt-to-print-ce662210b77a.workflow.wflow&printDemoRun=runs%2Fprompt-to-print-ce662210b77a%2F20260926T165217Z-b6f67611dec7.json
Action: Click View saved result.
Controls: Open saved run record, Open saved artifact
Expected: Same retained run and outputs.
Actual: Same exact retained run restored.
Status: pass
Screenshots: screenshots/raw/S05.png; screenshots/annotated/S05.png

## 2026-10-03T04:16:21.796Z UTC â€” Original failed pumpkin — recorder file tab

URL: http://wright.localhost:8038/workspace/083-heat-live-005?workflow=canonical&workflowPath=workflows%2Fprompt-to-print-ce662210b77a.workflow.wflow&printDemoRun=runs%2Fprompt-to-print-ce662210b77a%2F20260926T165217Z-b6f67611dec7.json
Action: Click Open saved run record.
Controls: runs/prompt-to-print-ce662210b77a/20260926T165217Z-b6f67611dec7.json
Expected: Exact recorder tab selected; no external window.
Actual: Exact recorder tab selected; one browser page.
Status: pass
Screenshots: screenshots/raw/S06.png; screenshots/annotated/S06.png

## 2026-10-03T04:16:52.024Z UTC â€” Original-history proof stopped

URL: http://wright.localhost:8038/workspace/083-heat-live-005?workflow=canonical&workflowPath=workflows%2Fprompt-to-print-ce662210b77a.workflow.wflow&printDemoRun=runs%2Fprompt-to-print-ce662210b77a%2F20260926T165217Z-b6f67611dec7.json
Action: Stop at unexpected state.
Controls: Historical result
Expected: Exact original history and workspace navigation.
Actual: locator.click: Timeout 30000ms exceeded.
Call log:
[2m  - waiting for getByTestId('editor-tab-workflows/prompt-to-print-ce662210b77a.workflow.wflow')[22m

Status: blocked
Screenshots: screenshots/raw/STOP.png; screenshots/annotated/STOP.png
