# Installed workflow authoring continuation

Prepared before navigation. Browser trace remains in the private proof root because authentication headers are sensitive.

## 2026-10-02T22:33:32.406Z UTC â€” Normal workspace editor entry

URL: http://wright.localhost:8037/workspace/083-heat-live-005?workflow=canonical
Action: Click Workflows.
Controls: Workflows, Workflow files
Expected: Existing editor opens within the workspace.
Actual: Existing editor and workflow file menu are visible.
Status: pass
Screenshots: screenshots/raw/S01.png; screenshots/annotated/S01.png

## 2026-10-02T22:33:32.958Z UTC â€” Accurate new-workflow instructions

URL: http://wright.localhost:8037/workspace/083-heat-live-005?workflow=canonical
Action: Open New workflow.
Controls: Workflow name, Create workflow
Expected: Instructions describe a blank workflow.
Actual: The installed dialog describes blank-workflow creation and readiness.
Status: pass
Screenshots: screenshots/raw/S02.png; screenshots/annotated/S02.png

## 2026-10-02T22:33:33.924Z UTC â€” Editor verification stopped at Blank workflow creation

URL: http://wright.localhost:8037/workspace/083-heat-live-005?workflow=canonical&workflowPath=workflows%2Feditor-verification-083-002.workflow.wflow
Action: Blank workflow creation
Controls: Blank workflow creation
Expected: Normal editor action succeeds without guesses or workarounds.
Actual: expect(locator).toBeVisible() failed

Locator: getByTestId('workflow-recovery-concept')
Expected: visible
Error: strict mode violation: getByTestId('workflow-recovery-concept') resolved to 2 elements:
    1) <section data-revision="1" data-testid="workflow-recovery-concept" class="workflow-recovery workflow-recovery--redesign" data-layout-digest="sha256:4e53cb726a749dae59d760f8dc22951cfee979be0b86bf5ab0276b21742a9396" data-semantic-digest="sha256:15e4feb074479d5f8c91ba77d0405d36bc520457065a663332dbd8ceffa75190">…</section> aka getByLabel('Heat-spreader comparison proof workflow workflows/mounting-bracket.workflow.').getByTestId('workflow-recovery-concept')
    2) <section aria-busy="true" data-surface-state="loading" data-testid="workflow-recovery-concept" class="workflow-recovery recovery-boundary-state">…</section> aka getByText('Loading workflow editor…The')

Call log:
  - Expect "to.be.visible" with timeout 5000ms
  - waiting for getByTestId('workflow-recovery-concept')

Status: blocked
Screenshots: screenshots/raw/STOP.png; screenshots/annotated/STOP.png
