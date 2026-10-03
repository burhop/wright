# UI evidence negative walkthrough

Prepared before the first browser action. The authenticated trace is kept privately; published diagnostics omit credentials. Synthetic authoring and producer responses are fixture scaffolding, not live AI or engineering acceptance.

## 2026-10-03T19:25:32.518Z UTC — Normal workspace entry

URL: http://wright.localhost:63932/workspace/06ac6649-2ca2-4b6c-88db-02cc9b69ff4e
Action: Open isolated workspace
Expected: Workflows available in normal workspace
Actual: Normal Wright workspace and Workflows control are visible.
Status: PASS
Screenshots: screenshots/raw/S01.png; screenshots/annotated/S01.png

## 2026-10-03T19:25:34.406Z UTC — Refined editor

URL: http://wright.localhost:63932/workspace/06ac6649-2ca2-4b6c-88db-02cc9b69ff4e?workflow=canonical
Action: Click Workflows
Expected: Established editor and Workflow files controls
Actual: Editor opens inside Wright.
Status: PASS
Screenshots: screenshots/raw/S02.png; screenshots/annotated/S02.png

## 2026-10-03T19:25:35.253Z UTC — Choose saved process

URL: http://wright.localhost:63932/workspace/06ac6649-2ca2-4b6c-88db-02cc9b69ff4e?workflow=canonical
Action: Click Workflow files then Open workflow
Expected: Exact fixture workflow listed
Actual: Named synthetic workflow is available.
Status: PASS
Screenshots: screenshots/raw/S03.png; screenshots/annotated/S03.png

STOPPED: Error: expect(locator).toBeEnabled() failed

Locator: locator('[data-workflow-file="workflows/ui-evidence-negative-001.workflow.wflow"]:visible').getByTestId('workflow-working-view-open')
Expected: enabled
Timeout: 45000ms
Error: element(s) not found

Call log:
  - Expect "to.be.enabled" with timeout 45000ms
  - waiting for locator('[data-workflow-file="workflows/ui-evidence-negative-001.workflow.wflow"]:visible').getByTestId('workflow-working-view-open')

    at captureRawStack (D:\repos\wright\node_modules\playwright-core\lib\coreBundle.js:9681:17)
    at callMatcherAsStep (D:\repos\wright\node_modules\playwright\lib\matchers\expect.js:13310:57)
    at Object.toBeEnabled (D:\repos\wright\node_modules\playwright\lib\matchers\expect.js:13300:23)
    at D:\repos\wright\.local-run\process-interfaces-083\t056-negative-ui-browser-002.mjs:42:241
