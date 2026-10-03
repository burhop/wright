# UI evidence negative walkthrough

Prepared before the first browser action. The authenticated trace is kept privately; published diagnostics omit credentials. Synthetic authoring and producer responses are fixture scaffolding, not live AI or engineering acceptance.

## 2026-10-03T19:31:39.129Z UTC — Normal workspace entry

URL: http://wright.localhost:54345/workspace/06ac6649-2ca2-4b6c-88db-02cc9b69ff4e
Action: Open isolated workspace
Expected: Workflows available in normal workspace
Actual: Normal Wright workspace and Workflows control are visible.
Status: PASS
Screenshots: screenshots/raw/S01.png; screenshots/annotated/S01.png

## 2026-10-03T19:31:40.367Z UTC — Refined editor

URL: http://wright.localhost:54345/workspace/06ac6649-2ca2-4b6c-88db-02cc9b69ff4e?workflow=canonical
Action: Click Workflows
Expected: Established editor and Workflow files controls
Actual: Editor opens inside Wright.
Status: PASS
Screenshots: screenshots/raw/S02.png; screenshots/annotated/S02.png

## 2026-10-03T19:31:40.945Z UTC — Choose saved process

URL: http://wright.localhost:54345/workspace/06ac6649-2ca2-4b6c-88db-02cc9b69ff4e?workflow=canonical
Action: Click Workflow files then Open workflow
Expected: Exact fixture workflow listed
Actual: Named synthetic workflow is available.
Status: PASS
Screenshots: screenshots/raw/S03.png; screenshots/annotated/S03.png

## 2026-10-03T19:31:41.752Z UTC — Accepted process

URL: http://wright.localhost:54345/workspace/06ac6649-2ca2-4b6c-88db-02cc9b69ff4e?workflow=canonical&workflowPath=workflows%2Fui-evidence-negative-001.workflow.wflow
Action: Choose ui-evidence-negative-001.workflow.wflow
Expected: Connected source opens without executing
Actual: Actual accepted diagram opens; no process starts.
Status: PASS
Screenshots: screenshots/raw/S04.png; screenshots/annotated/S04.png

## 2026-10-03T19:31:42.142Z UTC — Common view in workspace tab

URL: http://wright.localhost:54345/workspace/06ac6649-2ca2-4b6c-88db-02cc9b69ff4e?workflow=canonical&workflowPath=workflows%2Fui-evidence-negative-001.workflow.wflow&processView=0351d761-d445-42e7-9177-b006d4e6a378&processPath=workflows%2Fui-evidence-negative-001.workflow.wflow&processDigest=93289359a42dd8ec077255622aa337b5361686875f77579494eeeb48feec2cb7
Action: Click Use saved process
Expected: Common working view opens
Actual: The common view is hosted beside the editor.
Status: PASS
Screenshots: screenshots/raw/S05.png; screenshots/annotated/S05.png

## 2026-10-03T19:31:44.484Z UTC — Exact run review available

URL: http://wright.localhost:54345/workspace/06ac6649-2ca2-4b6c-88db-02cc9b69ff4e?processView=view-negative-common-001&processPath=workflows%2Fui-evidence-negative-001.workflow.wflow&processDigest=93289359a42dd8ec077255622aa337b5361686875f77579494eeeb48feec2cb7&processRun=1ed6c2e1302a4eb18ff7575a3fbe5be0
Action: Open prepared run link
Expected: Existing exact review available without another run
Actual: Approve is available for the one recorded synthetic document. No decision is submitted.
Status: PASS
Screenshots: screenshots/raw/S06.png; screenshots/annotated/S06.png

## 2026-10-03T19:31:51.953Z UTC — Actual read-only preview

URL: http://wright.localhost:54345/workspace/06ac6649-2ca2-4b6c-88db-02cc9b69ff4e?processView=view-negative-preview-001&processPath=workflows%2Fui-evidence-negative-001.workflow.wflow&processDigest=93289359a42dd8ec077255622aa337b5361686875f77579494eeeb48feec2cb7&processRun=1ed6c2e1302a4eb18ff7575a3fbe5be0&processUIKind=preview&processUI=ui-f1ca33c61df74d2ea8a96a3f284f2692&processUIRevision=revision-619a6260b1e64c51807c7fb2ed823879&processUIJob=job-40baffa08c454c9cac2790e8dfe8c0ec
Action: Open prepared preview link
Expected: Exact preview loads; reviews are read-only
Actual: Loaded preview renders shared controls and disables Approve.
Status: PASS
Screenshots: screenshots/raw/S07.png; screenshots/annotated/S07.png

## 2026-10-03T19:31:52.490Z UTC — Preview ready to save

URL: http://wright.localhost:54345/workspace/06ac6649-2ca2-4b6c-88db-02cc9b69ff4e?processView=view-negative-preview-001&processPath=workflows%2Fui-evidence-negative-001.workflow.wflow&processDigest=93289359a42dd8ec077255622aa337b5361686875f77579494eeeb48feec2cb7&processRun=1ed6c2e1302a4eb18ff7575a3fbe5be0&processUIKind=preview&processUI=ui-f1ca33c61df74d2ea8a96a3f284f2692&processUIRevision=revision-619a6260b1e64c51807c7fb2ed823879&processUIJob=job-40baffa08c454c9cac2790e8dfe8c0ec
Action: Click Create or choose interface
Expected: Save available only after exact preview loaded
Actual: Backend-loaded preview enables Save interface.
Status: PASS
Screenshots: screenshots/raw/S08.png; screenshots/annotated/S08.png

## 2026-10-03T19:31:53.584Z UTC — Immutable saved interface

URL: http://wright.localhost:54345/workspace/06ac6649-2ca2-4b6c-88db-02cc9b69ff4e?processView=view-negative-preview-001&processPath=workflows%2Fui-evidence-negative-001.workflow.wflow&processDigest=93289359a42dd8ec077255622aa337b5361686875f77579494eeeb48feec2cb7&processRun=1ed6c2e1302a4eb18ff7575a3fbe5be0&processUIKind=preview&processUI=ui-f1ca33c61df74d2ea8a96a3f284f2692&processUIRevision=revision-619a6260b1e64c51807c7fb2ed823879&processUIJob=job-40baffa08c454c9cac2790e8dfe8c0ec
Action: Click Save interface
Expected: Saved interface available
Actual: The real save owner records the built revision after preview.
Status: PASS
Screenshots: screenshots/raw/S09.png; screenshots/annotated/S09.png

## 2026-10-03T19:31:58.874Z UTC — Saved tailored view authority

URL: http://wright.localhost:54345/workspace/06ac6649-2ca2-4b6c-88db-02cc9b69ff4e?processView=c164f313-2fb9-4119-8a8e-72fe3ebe64e0&processPath=workflows%2Fui-evidence-negative-001.workflow.wflow&processDigest=93289359a42dd8ec077255622aa337b5361686875f77579494eeeb48feec2cb7&processRun=1ed6c2e1302a4eb18ff7575a3fbe5be0&processUIKind=working&processUI=ui-f1ca33c61df74d2ea8a96a3f284f2692&processUIRevision=revision-619a6260b1e64c51807c7fb2ed823879
Action: Click Open saved interface
Expected: Same exact available review as common view
Actual: Saved interface presents the same prepared document and available Approve. No review or action is sent.
Status: PASS
Screenshots: screenshots/raw/S10.png; screenshots/annotated/S10.png

STOPPED: Error: expect(locator).toBeVisible() failed

Locator: locator('[data-testid="common-process-view"]:visible').getByText('The review evidence changed or is unavailable.', { exact: true })
Expected: visible
Error: strict mode violation: locator('[data-testid="common-process-view"]:visible').getByText('The review evidence changed or is unavailable.', { exact: true }) resolved to 2 elements:
    1) <p>The review evidence changed or is unavailable.</p> aka locator('[id="_r_b_"]').getByText('The review evidence changed')
    2) <p>The review evidence changed or is unavailable.</p> aka locator('[id="_r_c_"]').getByText('The review evidence changed')

Call log:
  - Expect "to.be.visible" with timeout 5000ms
  - waiting for locator('[data-testid="common-process-view"]:visible').getByText('The review evidence changed or is unavailable.', { exact: true })

    at captureRawStack (D:\repos\wright\node_modules\playwright-core\lib\coreBundle.js:9681:17)
    at callMatcherAsStep (D:\repos\wright\node_modules\playwright\lib\matchers\expect.js:13310:57)
    at Object.toBeVisible (D:\repos\wright\node_modules\playwright\lib\matchers\expect.js:13300:23)
    at D:\repos\wright\.local-run\process-interfaces-083\t056-negative-ui-browser-003.mjs:50:303
