# Latest saved Heat output and navigation continuation

Prepared before navigation. Browser trace remains in the private proof root because authentication headers are sensitive.

## 2026-10-03T03:14:18.472Z UTC â€” Latest comparison matches completed engineering outputs

URL: http://127.0.0.1:5243/workspace/083-heat-live-005?workflow=canonical&workflowPath=workflows%2Fheat-spreader-sizing-live-default-model-002.workflow.wflow&processView=87dd3848-6197-4c21-92ad-474afec1dc2c&processPath=workflows%2Fheat-spreader-sizing-live-default-model-002.workflow.wflow&processDigest=e1ddaf65a1890060ad546ccc9604ea6f2a3ebfcdb9f0de7d1183bdeaadf20bf9&processRun=67abaa021ee44972a94e3c9cbaa3dbbe&processUIKind=working&processUI=ui-8858f2ec2bc24bc588ce5042626503ab&processUIRevision=revision-9c8c8b164ea34a9ba65910567b41b170
Action: Open the latest saved heat comparison for the completed run.
Controls: Run inputs, Open representation, Open assessment
Expected: Exact eighteen-result parity and original held assessment in a working context.
Actual: All eighteen identities match; exact working context and shared controls are present.
Status: pass
Screenshots: screenshots/raw/S01.png; screenshots/annotated/S01.png

## 2026-10-03T03:14:21.846Z UTC â€” Actual fine-field evidence and common parity

URL: http://127.0.0.1:5243/workspace/083-heat-live-005?workflow=canonical&workflowPath=workflows%2Fheat-spreader-sizing-live-default-model-002.workflow.wflow&processView=9f66ba74-c530-4d4f-984c-bfb4521e35b4&processPath=workflows%2Fheat-spreader-sizing-live-default-model-002.workflow.wflow&processDigest=e1ddaf65a1890060ad546ccc9604ea6f2a3ebfcdb9f0de7d1183bdeaadf20bf9&processRun=67abaa021ee44972a94e3c9cbaa3dbbe
Action: Open revision_60_fine, expand View numerical samples and select x_m, y_m, temperature_c.
Controls: Open representation, View numerical samples, Horizontal column, Vertical column, Value column
Expected: Exact common result parity and all 765 real supplied samples.
Actual: Eighteen exact common results and all fine-grid samples rendered; no interpolation or engineering approval.
Status: pass
Screenshots: screenshots/raw/S02.png; screenshots/annotated/S02.png

## 2026-10-03T03:14:34.083Z UTC â€” Exact full heat assessment remains held

URL: http://127.0.0.1:5243/workspace/083-heat-live-005?workflow=canonical&workflowPath=workflows%2Fheat-spreader-sizing-live-default-model-002.workflow.wflow&processView=9f66ba74-c530-4d4f-984c-bfb4521e35b4&processPath=workflows%2Fheat-spreader-sizing-live-default-model-002.workflow.wflow&processDigest=e1ddaf65a1890060ad546ccc9604ea6f2a3ebfcdb9f0de7d1183bdeaadf20bf9&processRun=67abaa021ee44972a94e3c9cbaa3dbbe
Action: Reopen the comparison and click Open assessment on revision_60_fine.
Controls: Open assessment, Representation
Expected: Original held assessment and exact fine-result focus.
Actual: Twenty-five passes, one blocked review and exact fine-result focus retained.
Status: pass
Screenshots: screenshots/raw/S03.png; screenshots/annotated/S03.png

## 2026-10-03T03:14:47.573Z UTC â€” Exact computation block selected

URL: http://127.0.0.1:5243/workspace/083-heat-live-005?workflow=canonical&workflowPath=workflows%2Fheat-spreader-sizing-live-default-model-002.workflow.wflow
Action: Reopen the comparison and click Open producing step on revision_60_fine.
Controls: Open producing step, Inspector
Expected: The exact accepted computation block selected.
Actual: Exact computation block and inspector selected; no stale-source warning.
Status: pass
Screenshots: screenshots/raw/S04.png; screenshots/annotated/S04.png

## 2026-10-03T03:17:00.234Z UTC â€” Latest heat interface check stopped

URL: http://127.0.0.1:5243/workspace/083-heat-live-005?workflow=canonical&workflowPath=workflows%2Fheat-spreader-sizing-live-default-model-002.workflow.wflow&processView=87dd3848-6197-4c21-92ad-474afec1dc2c&processPath=workflows%2Fheat-spreader-sizing-live-default-model-002.workflow.wflow&processDigest=e1ddaf65a1890060ad546ccc9604ea6f2a3ebfcdb9f0de7d1183bdeaadf20bf9&processRun=67abaa021ee44972a94e3c9cbaa3dbbe&processUIKind=working&processUI=ui-8858f2ec2bc24bc588ce5042626503ab&processUIRevision=revision-9c8c8b164ea34a9ba65910567b41b170
Action: Stop at the unexpected comparison state.
Controls: Open representation, Open assessment, Open producing step
Expected: Exact completed-output parity and useful navigation.
Actual: expect(locator).toBeVisible() failed

Locator: locator('[data-testid="surface-panel-host"]:visible').locator('iframe').contentFrame().getByText('Connected to Wright.', { exact: true })
Expected: visible
Timeout: 120000ms
Error: element(s) not found

Call log:
  - Expect "to.be.visible" with timeout 120000ms
  - waiting for locator('[data-testid="surface-panel-host"]:visible').locator('iframe').contentFrame().getByText('Connected to Wright.', { exact: true })

Status: blocked
Screenshots: screenshots/raw/STOP.png; screenshots/annotated/STOP.png
