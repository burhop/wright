# Heat workspace entry walkthrough

Prepared before navigation. Browser trace remains in the private proof root because authentication headers are sensitive.

## 2026-10-02T16:04:17.568Z UTC â€” Workspace entry

URL: http://127.0.0.1:5243/workspace/083-heat-live-005
Action: Open workspace.
Controls: Workflows
Expected: Workflows visible.
Actual: Workflows visible.
Status: pass
Screenshots: screenshots/raw/S01.png; screenshots/annotated/S01.png

## 2026-10-02T16:04:20.499Z UTC â€” Shared authoring entry

URL: http://127.0.0.1:5243/workspace/083-heat-live-005?workflow=canonical
Action: Click Workflows.
Controls: Workflow files
Expected: Editor controls without active print demo.
Actual: Editor controls present; Print a part demo absent.
Status: pass
Screenshots: screenshots/raw/S02.png; screenshots/annotated/S02.png

## 2026-10-02T16:04:27.114Z UTC â€” Exact read-only history

URL: http://127.0.0.1:5243/workspace/083-heat-live-005?workflow=canonical&workflowPath=workflows%2Fprinted-replacement-part-retained-consumer-001.workflow.wflow&printDemoRun=runs%2Fprinted-replacement-part-retained-consumer-001%2Fa87d84b40a244bcaa035d9ed8308ac5a.json
Action: Open historical workspace link.
Controls: Back to workflow, Open saved artifact, Open saved run record
Expected: Exact failed run, original error and saved outputs; no print controls.
Actual: Exact retained failed run/error and artifact links verified.
Status: pass
Screenshots: screenshots/raw/S03.png; screenshots/annotated/S03.png

## 2026-10-02T16:04:29.559Z UTC â€” Return to its editor

URL: http://127.0.0.1:5243/workspace/083-heat-live-005?workflow=canonical&workflowPath=workflows%2Fprinted-replacement-part-retained-consumer-001.workflow.wflow&printDemoRun=runs%2Fprinted-replacement-part-retained-consumer-001%2Fa87d84b40a244bcaa035d9ed8308ac5a.json
Action: Click Back to workflow.
Controls: View saved result, Workflow files
Expected: Exact workflow editor restored.
Actual: Exact workflow editor and history reopen control visible.
Status: pass
Screenshots: screenshots/raw/S04.png; screenshots/annotated/S04.png

## 2026-10-02T16:04:30.762Z UTC â€” Reopen saved history

URL: http://127.0.0.1:5243/workspace/083-heat-live-005?workflow=canonical&workflowPath=workflows%2Fprinted-replacement-part-retained-consumer-001.workflow.wflow&printDemoRun=runs%2Fprinted-replacement-part-retained-consumer-001%2Fa87d84b40a244bcaa035d9ed8308ac5a.json
Action: Click View saved result.
Controls: Open saved run record
Expected: Same retained run.
Actual: Same retained run restored.
Status: pass
Screenshots: screenshots/raw/S05.png; screenshots/annotated/S05.png

## 2026-10-02T16:05:31.784Z UTC â€” History stopped

URL: http://127.0.0.1:5243/workspace/083-heat-live-005?workflow=canonical&workflowPath=workflows%2Fprinted-replacement-part-retained-consumer-001.workflow.wflow&printDemoRun=runs%2Fprinted-replacement-part-retained-consumer-001%2Fa87d84b40a244bcaa035d9ed8308ac5a.json
Action: Stop at unexpected state.
Controls: Historical result
Expected: Exact saved history and workspace navigation.
Actual: expect(locator).toHaveAttribute(expected) failed

Locator: getByTestId('editor-tab-runs/printed-replacement-part-retained-consumer-001/a87d84b40a244bcaa035d9ed8308ac5a.json')
Expected: "true"
Timeout: 60000ms
Error: element(s) not found

Call log:
  - Expect "to.have.attribute.value" with timeout 60000ms
  - waiting for getByTestId('editor-tab-runs/printed-replacement-part-retained-consumer-001/a87d84b40a244bcaa035d9ed8308ac5a.json')

Status: blocked
Screenshots: screenshots/raw/STOP.png; screenshots/annotated/STOP.png
