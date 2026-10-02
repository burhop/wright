# Heat workspace entry walkthrough

Prepared before navigation. Browser trace remains in the private proof root because authentication headers are sensitive.

## 2026-10-02T15:58:57.719Z UTC â€” Workspace entry

URL: http://127.0.0.1:5243/workspace/083-heat-live-005
Action: Open workspace.
Controls: Workflows
Expected: Workflows visible.
Actual: Workflows visible.
Status: pass
Screenshots: screenshots/raw/S01.png; screenshots/annotated/S01.png

## 2026-10-02T15:59:01.014Z UTC â€” Shared authoring entry

URL: http://127.0.0.1:5243/workspace/083-heat-live-005?workflow=canonical
Action: Click Workflows.
Controls: Workflow files
Expected: Editor controls without active print demo.
Actual: Editor controls present; Print a part demo absent.
Status: pass
Screenshots: screenshots/raw/S02.png; screenshots/annotated/S02.png

## 2026-10-02T16:00:04.044Z UTC â€” History stopped

URL: http://127.0.0.1:5243/workspace/083-heat-live-005?workflow=canonical&workflowPath=workflows%2Fprinted-replacement-part-retained-consumer-001.workflow.wflow&printDemoRun=runs%2Fprinted-replacement-part-retained-consumer-001%2Fa87d84b40a244bcaa035d9ed8308ac5a.json
Action: Stop at unexpected state.
Controls: Historical result
Expected: Exact saved history and workspace navigation.
Actual: expect(locator).toBeVisible() failed

Locator: getByText('Recorded run: a87d84b40a244bcaa035d9ed8308ac5a · failed', { exact: true })
Expected: visible
Timeout: 60000ms
Error: element(s) not found

Call log:
  - Expect "to.be.visible" with timeout 60000ms
  - waiting for getByText('Recorded run: a87d84b40a244bcaa035d9ed8308ac5a · failed', { exact: true })

Status: blocked
Screenshots: screenshots/raw/STOP.png; screenshots/annotated/STOP.png
