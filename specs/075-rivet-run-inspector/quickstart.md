# Quickstart: Rivet Run Inspector

## Local prerequisites

- Use the existing Wright development environment and pinned Rivet editor artifact workflow.
- Keep normal tests offline; no OAuth, Onshape subscription, CAD host, or external MCP server is required.
- Preserve the current dirty UI-marathon changes and work only on `codex/075-rivet-run-inspector`.

## Focused implementation checks

Run backend and persistence coverage:

```powershell
uv run pytest packages/data_vault/tests/test_data_vault_workflow_runs.py packages/data_vault/tests/test_rivet_run_manifest.py packages/workspace_service/tests/test_workflow_runner.py packages/workspace_service/tests/test_workflow_operations.py packages/workspace_service/tests/test_rivet_run_evidence.py packages/workspace_service/tests/test_rivet_gateway_bridge.py apps/api/tests/test_rivet_mcp_run_api.py
```

Run frontend component coverage:

```powershell
npm --prefix apps/web run test -- --run src/components/workflows/RivetRunInspector.spec.tsx src/components/surfaces/DirectRivetSurface.spec.tsx src/services/workspace-service.spec.ts
```

Run mocked browser journeys:

```powershell
npx playwright test tests/ui-integration/workspace-surfaces/rivet-run-inspector.spec.ts
```

Run the focused local system smoke:

```powershell
uv run pytest tests/e2e/test_rivet_run_inspector.py
```

Rebuild the pinned editor only after the source bridge and maintained patch are covered:

```powershell
node integrations/rivet/editor/scripts/build-rivet2.mjs
```

## Required behavior checks

1. Open a saved workflow and use the main Run icon. Confirm it starts immediately; the adjacent options control remains the only way to open graph/input options.
2. Confirm the bottom inspector shows live elapsed time, phase, current step, and completed count within one second.
3. Complete a run with text, structured, null, link, and artifact outputs. Verify full retained values, copy/export behavior, and explicit no-output wording.
4. Fail an MCP step. Verify automatic opening, failing node/tool, plain explanation, technical details, successful upstream results, and full-rerun guidance.
5. Select a step. Verify the matching canvas node is focused and its state is understandable without color.
6. Refresh during a delayed run. Verify the same run ID reattaches and no second POST start request occurs.
7. Inspect recent runs from two workflow revisions. Verify revision identity and historical missing-node behavior.
8. Exercise oversized and secret-bearing fixtures. Verify truncation disclosure and absence of secrets in the screen, clipboard, result export, evidence export, and browser diagnostics.
9. Cancel a child call. Verify cancellation/residue truth and that unsafe partial retry is absent.
10. Collapse the inspector and verify the canvas regains its vertical area without losing the compact run summary.

## Final gates

- Run the focused tests above during iteration.
- Run the web build and lint after component work stabilizes.
- Run `scripts/check-dev-merge.sh` before any merge to `dev`, or document the exact local host limitation for a gate that cannot run.
- Do not merge, push, publish, or release as part of implementation unless separately authorized.

## Verification record — 2026-08-20

- Backend, persistence, lifecycle, API, local E2E, and pinned-editor artifact gate: 53 passed.
- Frontend component/client/hook gate: 33 passed across five focused files.
- Mocked browser journey: 12 passed across Chromium, Firefox, WebKit, and the desktop-surface profile.
- Pinned Rivet editor: rebuilt from revision `4f4a165a03f8da89c3d1cce2cb1a8c6eb6aa2053`; 228 generated files passed all six integrity checks.
- Web production build passed. ESLint passed with three pre-existing hook warnings outside Run Inspector files.
- `git diff --check` and Ruff lint passed. All feature Python files were formatted with the repository Ruff configuration.
- `scripts/check-dev-merge.sh` was attempted from PowerShell with `SKIP_PLAYWRIGHT=1` because the actively running local Wright UI occupies ports 5173/8000. The script entered WSL, passed `git diff --check`, then stopped at its first Python gate because `uv` is installed in Windows but is not on the WSL `PATH` (`scripts/check-dev-merge.sh: line 23: uv: command not found`). The equivalent focused Python, frontend, browser, build, and artifact gates above were run directly in Windows.

## Development feedback-loop verification — 2026-08-20

- Added `scripts/check-dev-push.ps1` and `scripts/check-dev-merge.ps1`; both use Git for Windows Bash, eliminating the WSL toolchain mismatch above.
- Added isolated UI/API ports and a cached, Git-ignored Python 3.13 gate environment so validation does not stop or mutate a running Wright instance.
- Process-policy tests passed: 5. Frontend tests passed: 368 across 91 files. The production web build and strict MkDocs build passed.
- The Chromium fast smoke passed 6 journeys, including direct Rivet run, failed-run diagnostics, refresh reattachment, focus mode, narrow layout, and navigation.
- The final fast gate passed end to end, and ports 18001 and 15174 were confirmed released after cleanup.
