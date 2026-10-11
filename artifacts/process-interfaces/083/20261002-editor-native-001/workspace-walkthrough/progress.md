# Installed historical workflow walkthrough

Prepared before navigation. Browser trace remains in the private proof root because authentication headers are sensitive.

## 2026-10-02T22:16:32.551Z UTC â€” Normal workspace editor entry

URL: http://wright.localhost:8036/workspace/083-heat-live-005?workflow=canonical
Action: Click Workflows.
Controls: Workflow files
Expected: Existing editor and workflow file menu.
Actual: Editor and workflow file menu visible.
Status: pass
Screenshots: screenshots/raw/S01.png; screenshots/annotated/S01.png

## 2026-10-02T22:16:38.295Z UTC â€” New-workflow authoring stopped

URL: http://wright.localhost:8036/workspace/083-heat-live-005?workflow=canonical
Action: Stop before creation.
Controls: New workflow, Workflow name, Create workflow
Expected: Creation instructions match the actual blank workflow.
Actual: expect(locator).not.toContainText(expected) failed

Locator: getByRole('dialog')
Expected substring: not "Starts with the editable engineering example"
Received string: "New workflowStored in Heat-spreader comparison proof/workflows. Existing files are never replaced.Workflow nameStarts with the editable engineering example. The Run panel states which saved workflow capabilities are available.Create workflowCancel"
Timeout: 5000ms

Call log:
  - Expect "to.have.text" with timeout 5000ms
  - waiting for getByRole('dialog')
    14 × locator resolved to <dialog open="" aria-labelledby="_r_0_-title">…</dialog>
       - unexpected value "New workflowStored in Heat-spreader comparison proof/workflows. Existing files are never replaced.Workflow nameStarts with the editable engineering example. The Run panel states which saved workflow capabilities are available.Create workflowCancel"

Status: blocked
Screenshots: screenshots/raw/STOP.png; screenshots/annotated/STOP.png
