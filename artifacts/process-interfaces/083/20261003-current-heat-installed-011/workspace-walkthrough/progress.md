# Heat workspace entry walkthrough

Prepared before navigation. Browser trace remains in the private proof root because authentication headers are sensitive.

## 2026-10-03T11:09:35.911Z UTC — Current installed workspace entry

URL: http://wright.localhost:62189/workspace/083-heat-repeat-013
Action: Open the isolated workspace.
Controls: Workflows
Expected: Normal workspace available.
Actual: Workflows is visible on the current installed host.
Status: pass
Screenshots: screenshots/raw/S01.png; screenshots/annotated/S01.png

## 2026-10-03T11:09:44.511Z UTC — Saved interface remains usable without a compiler

URL: http://wright.localhost:62189/workspace/083-heat-repeat-013?workflow=canonical&workflowPath=workflows%2Fheat-spreader-sizing-repeatable-default-013.workflow.wflow&processView=546fa809-f903-4a59-8b9d-68e8fe54fd5d&processPath=workflows%2Fheat-spreader-sizing-repeatable-default-013.workflow.wflow&processDigest=d941977f20b6ec345f0ec8959fddaa76833b9546278c2af5d9f0d71fede5536b&processRun=63b639c7a8f446cd90a9285921ab9072&processUIKind=working&processUI=ui-512d6109b37f4c0f89b86d86a34827b2&processUIRevision=revision-c4ac3eb3c1fb487aa14ac04c0b0cbda0
Action: Open Create or choose interface on the recorded working view.
Controls: Create interface, Open saved interface
Expected: Creation unavailable, existing saved assets available, no model request.
Actual: Create interface is disabled while Open saved interface stays enabled on the current installed package.
Status: pass
Screenshots: screenshots/raw/S13.png; screenshots/annotated/S13.png

## 2026-10-03T11:09:46.073Z UTC — Working and authoring accessibility

URL: http://wright.localhost:62189/workspace/083-heat-repeat-013?workflow=canonical&workflowPath=workflows%2Fheat-spreader-sizing-repeatable-default-013.workflow.wflow&processView=546fa809-f903-4a59-8b9d-68e8fe54fd5d&processPath=workflows%2Fheat-spreader-sizing-repeatable-default-013.workflow.wflow&processDigest=d941977f20b6ec345f0ec8959fddaa76833b9546278c2af5d9f0d71fede5536b&processRun=63b639c7a8f446cd90a9285921ab9072&processUIKind=working&processUI=ui-512d6109b37f4c0f89b86d86a34827b2&processUIRevision=revision-c4ac3eb3c1fb487aa14ac04c0b0cbda0
Action: Inspect active working-tab WCAG 2/2.1 A/AA semantics and contrast.
Controls: Working tab, Saved interface, Authoring controls
Expected: No detected A/AA violations; manual accessibility acceptance remains separate.
Actual: Automated axe scan reports no violations.
Status: pass
Screenshots: screenshots/raw/S14.png; screenshots/annotated/S14.png

## 2026-10-03T11:09:57.161Z UTC — Existing built preview is read-only in a workspace tab

URL: http://wright.localhost:62189/workspace/083-heat-repeat-013?workflow=canonical&workflowPath=workflows%2Fheat-spreader-sizing-repeatable-default-013.workflow.wflow&processView=view-installed-heat-preview-008&processPath=workflows%2Fheat-spreader-sizing-repeatable-default-013.workflow.wflow&processDigest=d941977f20b6ec345f0ec8959fddaa76833b9546278c2af5d9f0d71fede5536b&processRun=63b639c7a8f446cd90a9285921ab9072&processUIKind=preview&processUI=ui-512d6109b37f4c0f89b86d86a34827b2&processUIRevision=revision-c4ac3eb3c1fb487aa14ac04c0b0cbda0&processUIJob=job-1e03b43bc5664e6fa1d9fbea3a264299
Action: Open the retained preview link for the exact saved revision and recorded run.
Controls: Preview tab
Expected: Read-only preview and exact same eighteen result identities.
Actual: Preview banner, backend read-only context and exact engineering result parity verified.
Status: pass
Screenshots: screenshots/raw/S15.png; screenshots/annotated/S15.png

## 2026-10-03T11:09:57.373Z UTC — Entry stopped

URL: http://wright.localhost:62189/workspace/083-heat-repeat-013?workflow=canonical&workflowPath=workflows%2Fheat-spreader-sizing-repeatable-default-013.workflow.wflow&processView=view-installed-heat-preview-008&processPath=workflows%2Fheat-spreader-sizing-repeatable-default-013.workflow.wflow&processDigest=d941977f20b6ec345f0ec8959fddaa76833b9546278c2af5d9f0d71fede5536b&processRun=63b639c7a8f446cd90a9285921ab9072&processUIKind=preview&processUI=ui-512d6109b37f4c0f89b86d86a34827b2&processUIRevision=revision-c4ac3eb3c1fb487aa14ac04c0b0cbda0&processUIJob=job-1e03b43bc5664e6fa1d9fbea3a264299
Action: Stop at the unexpected entry state.
Controls: Workflows
Expected: Workspace and established editor available.
Actual: expect(locator).toBeVisible() failed

Locator: getByTestId('workspace-process-view')
Expected: visible
Error: strict mode violation: getByTestId('workspace-process-view') resolved to 2 elements:
    1) <section class="process-workspace-view" data-testid="workspace-process-view" data-run-id="63b639c7a8f446cd90a9285921ab9072" aria-label="heat-spreader-sizing-repeatable-default-013.wflow · working view" data-process-path="workflows/heat-spreader-sizing-repeatable-default-013.workflow.wflow">…</section> aka getByTestId('workspace-process-view').first()
    2) <section class="process-workspace-view" data-testid="workspace-process-view" data-run-id="63b639c7a8f446cd90a9285921ab9072" aria-label="heat-spreader-sizing-repeatable-default-013.wflow · interface preview" data-process-path="workflows/heat-spreader-sizing-repeatable-default-013.workflow.wflow">…</section> aka getByRole('region', { name: 'heat-spreader-sizing-' })

Call log:
  - Expect "to.be.visible" with timeout 5000ms
  - waiting for getByTestId('workspace-process-view')

Status: blocked
Screenshots: screenshots/raw/STOP.png; screenshots/annotated/STOP.png
