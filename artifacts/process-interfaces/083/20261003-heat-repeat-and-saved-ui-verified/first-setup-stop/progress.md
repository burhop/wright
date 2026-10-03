# Heat workspace entry walkthrough

Prepared before navigation. Browser trace remains in the private proof root because authentication headers are sensitive.

## 2026-10-03T05:13:41.141Z UTC — Workspace offers Workflows

URL: http://127.0.0.1:5244/workspace/083-heat-repeat-013
Action: Open Heat-spreader comparison proof workspace.
Controls: Workflows
Expected: The workspace loads and offers Workflows.
Actual: Normal workspace and Workflows control visible.
Status: pass
Screenshots: screenshots/raw/S01.png; screenshots/annotated/S01.png

## 2026-10-03T05:14:26.446Z UTC — Entry stopped

URL: http://127.0.0.1:5244/workspace/083-heat-repeat-013
Action: Stop at the unexpected entry state.
Controls: Workflows
Expected: Workspace and established editor available.
Actual: expect(locator).toBeVisible() failed

Locator: getByTestId('workflow-file-menu')
Expected: visible
Timeout: 45000ms
Error: element(s) not found

Call log:
  - Expect "to.be.visible" with timeout 45000ms
  - waiting for getByTestId('workflow-file-menu')

Status: blocked
Screenshots: screenshots/raw/STOP.png; screenshots/annotated/STOP.png
