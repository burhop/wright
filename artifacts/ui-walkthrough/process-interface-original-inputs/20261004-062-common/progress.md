# Fresh common-view original-input walkthrough

Prepared before navigation. API start uses an exact locally enrolled integration-test policy. This browser does not start/approve/resume the run. Private authenticated trace is not published.

## 2026-10-04T01:19:37.614Z UTC — Normal workspace

URL: http://127.0.0.1:5246/workspace/083-fresh-prompt-055
Action: Open the isolated workspace
Controls: Open the isolated workspace
Expected: Existing workspace controls
Actual: Normal Workflows entry is available.
Status: PASS
Screenshots: screenshots/raw/S01.png; screenshots/annotated/S01.png

## 2026-10-04T01:19:39.078Z UTC — Existing editor entry

URL: http://127.0.0.1:5246/workspace/083-fresh-prompt-055?workflow=canonical
Action: Click Workflows
Controls: Click Workflows
Expected: Refined editor in the workspace
Actual: The existing editor and file controls are visible.
Status: PASS
Screenshots: screenshots/raw/S02.png; screenshots/annotated/S02.png

## 2026-10-04T01:19:40.206Z UTC — Exact saved process

URL: http://127.0.0.1:5246/workspace/083-fresh-prompt-055?workflow=canonical
Action: Click Workflow files then Open workflow
Controls: Click Workflow files then Open workflow
Expected: Named accepted source listed
Actual: The fresh original-input source is available through normal file selection.
Status: PASS
Screenshots: screenshots/raw/S03.png; screenshots/annotated/S03.png

## 2026-10-04T01:19:41.876Z UTC — Accepted diagram

URL: http://127.0.0.1:5246/workspace/083-fresh-prompt-055?workflow=canonical&workflowPath=workflows%2Fprinted-replacement-part-prompt-default-055.workflow.wflow
Action: Choose printed-replacement-part-prompt-default-055.workflow.wflow
Controls: Choose printed-replacement-part-prompt-default-055.workflow.wflow
Expected: Accepted source opens without execution
Actual: The existing diagram opens on the exact accepted source.
Status: PASS
Screenshots: screenshots/raw/S04.png; screenshots/annotated/S04.png

## 2026-10-04T01:20:20.640Z UTC — Common preparation view

URL: http://127.0.0.1:5246/workspace/083-fresh-prompt-055?workflow=canonical&workflowPath=workflows%2Fprinted-replacement-part-prompt-default-055.workflow.wflow&processView=2d9ba5c4-8951-4a8d-9830-89df384c03ec&processPath=workflows%2Fprinted-replacement-part-prompt-default-055.workflow.wflow&processDigest=17afd12596d230d549d0ff38d16834f994a07c41092576d3231f5e17597fb6f8
Action: Click Use saved process
Controls: Click Use saved process
Expected: Common inputs without generating an app
Actual: Original configured inputs are presented in the common workspace tab. The browser starts no process.
Status: PASS
Screenshots: screenshots/raw/S05.png; screenshots/annotated/S05.png

STOPPED: Error: expect(received).toBeTruthy()

Received: undefined
    at captureRawStack (D:\repos\wright\node_modules\playwright-core\lib\coreBundle.js:9681:17)
    at callMatcherAsStep (D:\repos\wright\node_modules\playwright\lib\matchers\expect.js:13310:57)
    at Object.toBeTruthy (D:\repos\wright\node_modules\playwright\lib\matchers\expect.js:13300:23)
    at D:\repos\wright\.local-run\process-interfaces-083\t047-fresh-prompt-common-062.mjs:40:341
