# Heat workspace entry walkthrough

Prepared before navigation. Browser trace remains in the private proof root because authentication headers are sensitive.

## 2026-10-03T11:23:10.305Z UTC — Current installed workspace entry

URL: http://wright.localhost:62189/workspace/083-heat-repeat-013
Action: Open the isolated workspace.
Controls: Workflows
Expected: Normal workspace available.
Actual: Workflows is visible on the current installed host.
Status: pass
Screenshots: screenshots/raw/S01.png; screenshots/annotated/S01.png

## 2026-10-03T11:24:41.653Z UTC — Entry stopped

URL: http://wright.localhost:62189/workspace/083-heat-repeat-013?workflow=canonical&workflowPath=workflows%2Fheat-spreader-sizing-repeatable-default-013.workflow.wflow&processView=view-installed-heat-preview-014&processPath=workflows%2Fheat-spreader-sizing-repeatable-default-013.workflow.wflow&processDigest=d941977f20b6ec345f0ec8959fddaa76833b9546278c2af5d9f0d71fede5536b&processRun=63b639c7a8f446cd90a9285921ab9072&processUIKind=preview&processUI=ui-512d6109b37f4c0f89b86d86a34827b2&processUIRevision=revision-c4ac3eb3c1fb487aa14ac04c0b0cbda0&processUIJob=job-1e03b43bc5664e6fa1d9fbea3a264299
Action: Stop at the unexpected entry state.
Controls: Workflows
Expected: Workspace and established editor available.
Actual: expect(locator).toBeVisible() failed

Locator: locator('[data-testid="surface-panel-host"]:visible').locator('iframe').contentFrame().getByText('Preview - process controls are read-only.', { exact: true })
Expected: visible
Timeout: 90000ms
Error: element(s) not found

Call log:
  - Expect "to.be.visible" with timeout 90000ms
  - waiting for locator('[data-testid="surface-panel-host"]:visible').locator('iframe').contentFrame().getByText('Preview - process controls are read-only.', { exact: true })

Status: blocked
Screenshots: screenshots/raw/STOP.png; screenshots/annotated/STOP.png
