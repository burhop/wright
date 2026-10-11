# Fresh common-view original-input walkthrough

Prepared before navigation. This browser starts the distinct two-stage digital-only process through its normal common view. No integration policy or review authority is used. Private authenticated trace is not published.

## 2026-10-04T02:01:36.929Z UTC — Enter the workspace workflow editor

URL: http://127.0.0.1:5246/workspace/083-fresh-prompt-055?workflow=canonical
Action: Click Workflows
Controls: Click Workflows
Expected: Normal workspace entry preserves the workflow editor
Actual: The existing workflow editor opens in the workspace.
Status: PASS
Screenshots: screenshots/raw/S01.png; screenshots/annotated/S01.png

## 2026-10-04T02:01:38.117Z UTC — Open the supported saved digital process

URL: http://127.0.0.1:5246/workspace/083-fresh-prompt-055?workflow=canonical&workflowPath=workflows%2Fprinted-replacement-part-common-digital-083.workflow.wflow
Action: Open workflow and choose printed-replacement-part-common-digital-083.workflow.wflow
Controls: Open workflow and choose printed-replacement-part-common-digital-083.workflow.wflow
Expected: The exact two-stage accepted source opens
Actual: The mesh preparation process is open; its two configured provider operations are preserved.
Status: PASS
Screenshots: screenshots/raw/S02.png; screenshots/annotated/S02.png

## 2026-10-04T02:01:41.865Z UTC — Use the common working view

URL: http://127.0.0.1:5246/workspace/083-fresh-prompt-055?workflow=canonical&workflowPath=workflows%2Fprinted-replacement-part-common-digital-083.workflow.wflow&processView=e3b32197-aab0-4a46-ab48-d87ed461e6f5&processPath=workflows%2Fprinted-replacement-part-common-digital-083.workflow.wflow&processDigest=88edffded48c36532efc8c49d7e1a78206753d3b52d658d8d3b9d18b1684eb06
Action: Click Use saved process
Controls: Click Use saved process
Expected: No generated interface is needed
Actual: The shared common working view opens in a Wright workspace tab.
Status: PASS
Screenshots: screenshots/raw/S03.png; screenshots/annotated/S03.png

## 2026-10-04T02:01:52.427Z UTC — Check normal readiness

URL: http://127.0.0.1:5246/workspace/083-fresh-prompt-055?workflow=canonical&workflowPath=workflows%2Fprinted-replacement-part-common-digital-083.workflow.wflow&processView=e3b32197-aab0-4a46-ab48-d87ed461e6f5&processPath=workflows%2Fprinted-replacement-part-common-digital-083.workflow.wflow&processDigest=88edffded48c36532efc8c49d7e1a78206753d3b52d658d8d3b9d18b1684eb06
Action: Click Prepare and check inputs
Controls: Click Prepare and check inputs
Expected: Ordinary public readiness permits this bounded saved process
Actual: The configured native arguments and exact upstream-file dependency pass public readiness. No integration policy is used.
Status: PASS
Screenshots: screenshots/raw/S04.png; screenshots/annotated/S04.png

## 2026-10-04T02:01:56.873Z UTC — Start from the common view

URL: http://127.0.0.1:5246/workspace/083-fresh-prompt-055?workflow=canonical&workflowPath=workflows%2Fprinted-replacement-part-common-digital-083.workflow.wflow&processView=e3b32197-aab0-4a46-ab48-d87ed461e6f5&processPath=workflows%2Fprinted-replacement-part-common-digital-083.workflow.wflow&processDigest=88edffded48c36532efc8c49d7e1a78206753d3b52d658d8d3b9d18b1684eb06&processRun=8c042141e6c7422aa58ca1bbab14d86e
Action: Click Start process
Controls: Click Start process
Expected: One durable digital run is accepted by the backend
Actual: The normal UI receives one accepted run 8c042141e6c7422aa58ca1bbab14d86e; the common view follows backend-owned progress without a generated interface.
Status: PASS
Screenshots: screenshots/raw/S05.png; screenshots/annotated/S05.png

STOPPED: Error: expect(locator).toBeVisible() failed

Locator: locator('[data-testid="common-process-view"]:visible').getByText('Completed', { exact: true })
Expected: visible
Timeout: 45000ms
Error: element(s) not found

Call log:
  - Expect "to.be.visible" with timeout 45000ms
  - waiting for locator('[data-testid="common-process-view"]:visible').getByText('Completed', { exact: true })

    at captureRawStack (D:\repos\wright\node_modules\playwright-core\lib\coreBundle.js:9681:17)
    at callMatcherAsStep (D:\repos\wright\node_modules\playwright\lib\matchers\expect.js:13310:57)
    at Object.toBeVisible (D:\repos\wright\node_modules\playwright\lib\matchers\expect.js:13300:23)
    at D:\repos\wright\.local-run\process-interfaces-083\t056-common-digital-browser-089.mjs:60:165
