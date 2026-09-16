# Candidate Validation

## Backend and storage

```powershell
uv run pytest packages/workspace_service/tests/test_engineering_workflow_templates.py packages/workspace_service/tests/test_engineering_workflow_template_instances.py packages/workspace_service/tests/test_workflow_engineering_assertions.py packages/workspace_service/tests/test_workflow_approval_resume.py packages/data_vault/tests/test_workflow_continuation_repository.py packages/data_vault/tests/test_migrations.py packages/data_vault/tests/test_migration_failures.py apps/api/tests/test_engineering_workflow_template_api.py apps/api/tests/test_workflow_approval_resume_api.py -q
```

Final result: `61 passed` in 6.34 seconds with one existing Starlette test-client deprecation warning.

The final API-only template/approval/capture slice passed `7` tests. The final shared catalog/instance/execution/approval/assertion/capture/storage slice passed `58` tests, and the source-execution/run-record regression slice passed `40` tests.

Ruff check passed for every feature-owned Python source and test. `git diff --check` passed.

## Web client and served UI

```powershell
npm run test --workspace apps/web -- --run src/services/workspace-service.spec.ts src/prototypes/workflow-recovery/EngineeringTemplateDialog.spec.tsx src/prototypes/workflow-recovery/EngineeringTemplateSources.spec.ts src/components/pages/WorkflowRecoveryPage.spec.tsx
```

Final result after adding exact approval, server-scoped resume, readiness, and capture coverage: `4 files passed`, `100 tests passed`.

Targeted ESLint and Prettier checks passed. `npm run build --workspace apps/web` completed the production TypeScript and Vite build; only the pre-existing Vite config-loader and chunk-size warnings remain.

```powershell
$env:WRIGHT_PLAYWRIGHT_PORT='5194'
$env:WRIGHT_PLAYWRIGHT_OUTPUT_DIR='test-results/playwright-081-final'
npx playwright test tests/ui-integration/engineering-workflow-templates.spec.ts --project=chromium
```

Final focus-aware result on the current implementation: `2 passed (5.5s)`. The test entered through the workspace Workflows control, returned keyboard focus after cancellation, and retained the established Diagram, Save, and Source controls after template creation.

The production TypeScript/Vite build passed after the final session-scoped approval and capture client changes. ESLint reported zero errors and the same nine pre-existing React hook warnings elsewhere in the editor application.

## Packaging and offline behavior

```powershell
uv build --offline --package wright-workspace-service --out-dir .tmp-081-dist-final
```

Result: the workspace service wheel built successfully with the existing isolated environment. Wheel inspection found 39 files under `workspace_service/engineering_workflow_templates/`, including the catalog, ten definitions, ten layouts, ten previews, and the three flagship fixture directories.

Template listing, preview, instantiation, source parsing, and packaged-resource tests use no network. Native-device and Docker engineering-chain qualification were not run because this candidate deliberately leaves the unqualified image/slicer/P1S, AgentCAD/CFD, and supplier-browser integrations in `setup_required`; running a container cannot supply the licensed hosts, accounts, or physical printer needed to promote them. No base image was modified.

## External effects

No printer transfer, supplier upload, cart mutation, purchase, payment, social publishing, authentication, or device operation was attempted. Approval resume tests stop at a durable `not_dispatched` record, and ambiguous reconciliation remains `outcome_unknown`.
