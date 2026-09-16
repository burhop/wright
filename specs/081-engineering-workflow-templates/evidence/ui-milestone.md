# UI Milestone Evidence

## Served workspace path

The browser test starts Wright's Vite-served web application, enters `/workspace/ws-recovery`, and opens the normal activity-bar **Workflows** control. It then uses the existing workflow file menu and **Start from template** action. This exercises the same `WorkspacePanel` → `WorkflowRecoveryPage` → `WorkflowRecoveryConcept` entry described in `docs/contributing/workflow-ui-integration.md`.

Command:

```powershell
$env:WRIGHT_PLAYWRIGHT_PORT='5193'
$env:WRIGHT_PLAYWRIGHT_OUTPUT_DIR='test-results/playwright-081'
npx playwright test tests/ui-integration/engineering-workflow-templates.spec.ts --project=chromium
```

Initial corrected run: `2 passed (5.4s)`. Final focus-aware regression on the completed local candidate: `2 passed (5.5s)`.

The first journey checks all ten options, setup readiness, the packaged preview image, cancellation, and return to the existing canvas. The second creates a fresh named instance, observes the workspace URL change to the new canonical workflow path, and checks that the established diagram, Save, and Source controls remain visible. The complete two-journey run is well inside the 60-second interaction bound.

## Supporting UI checks

```powershell
npm run test --workspace apps/web -- --run src/services/workspace-service.spec.ts src/prototypes/workflow-recovery/EngineeringTemplateDialog.spec.tsx src/prototypes/workflow-recovery/EngineeringTemplateSources.spec.ts src/components/pages/WorkflowRecoveryPage.spec.tsx
```

Final result after approval and capture integration: `4 files passed`, `100 tests passed`.

```powershell
npm run build --workspace apps/web
```

Result: production TypeScript and Vite build completed. Vite reported only the existing config-loader and large-chunk warnings.

The browser calls are mocked at the HTTP boundary so the tests create no printer, supplier, credential, or external network state. Backend contract tests separately exercise the real packaged catalog and atomic workspace storage.
