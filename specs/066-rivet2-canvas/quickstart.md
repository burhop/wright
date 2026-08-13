# Quickstart: Verify the Modern Rivet Canvas Editor

## Preconditions

- Enable Wright workflow storage, editor, workflow operations, and live app surface flags.
- Use Node.js 20.4 or newer, Yarn 4.17.1 from the pinned upstream checkout, and Python through the repository `uv` environment.
- Use the checked-in Rivet 2 artifact and exact schema-v2 manifest.
- Start Wright in a clean test workspace.

## Reproduce the Editor Artifact

The acquisition step accepts only the reviewed repository and detached revision. The build step applies the bounded Wright canvas patch and wrapper, builds upstream from source, rejects public editor assets, replaces `dist/`, and regenerates the complete file inventory and tree digest.

```powershell
node integrations/rivet/editor/scripts/acquire-rivet2.mjs
node integrations/rivet/editor/scripts/build-rivet2.mjs
uv run pytest integrations/rivet/editor/tests/test_rivet2_editor_artifact.py -q
```

For revision `4f4a165a03f8da89c3d1cce2cb1a8c6eb6aa2053`, an unchanged rebuild must report 228 files and tree digest `3a365fb96b396947850f2452d185ac50875df7c77735c91ffd8e4d6afa0e39a5`.

## Acceptance Journey

1. Create a blank Rivet workflow from the Wright workflow toolbar.
2. Open the template chooser, confirm the four packaged choices and their requirements, and create a Basic Flow workflow.
3. Confirm the active Wright tab shows `basic-flow.rivet-project` while the canvas toolbar shows no duplicate filename, workflow selector, open-workflow action, or routine status prose.
4. Open the retained Rivet surface.
5. Confirm the surface reports ready and displays only the graph canvas and required graph-authoring overlays.
6. Confirm project tabs, file menu, graph/project sidebar, Rivet run controls, status bar, settings/help, Prompt Designer, Trivet, Chat Viewer, Data Studio, Node Library, and Web App builder are not visible.
7. Add two nodes, configure them, connect them, move them, duplicate one, and delete the duplicate.
8. Save from Wright and record the new workspace revision.
9. Close and reopen the surface; confirm the saved graph is unchanged.
10. Lint and run from Wright; confirm both operate on the saved workspace revision.
11. Open a second workspace and confirm it cannot observe the first workspace's workflow or editor state.

## Offline Journey

1. Deny network access before Wright starts.
2. Start the packaged native or Docker runtime.
3. Repeat open, edit, save, close, and reopen.
4. Assert that no editor request targets a public origin.

## Failure Journey

1. Corrupt or remove one editor artifact file.
2. Request the Rivet surface.
3. Confirm Wright reports the verified artifact unavailable and starts no editor process.
4. Confirm no legacy Rivet editor starts.

## Suggested Verification Commands

```powershell
npm --prefix apps/web test -- --run src/components/surfaces/DirectRivetSurface.spec.tsx src/services/rivet-editor.spec.ts src/services/surfaces/feature-flags.rivet.spec.ts src/store/rivet-tabs.spec.ts
npm --prefix apps/web run build
npm --prefix apps/web run lint
npx playwright test tests/ui-integration/workspace-surfaces/rivet2-canvas.spec.ts --project=chromium
uv run pytest integrations/rivet/editor/tests/test_rivet2_editor_artifact.py packages/workspace_service/tests/test_rivet_editor_host.py packages/workspace_service/tests/test_workflow_editor.py apps/api/tests/test_surfaces_api_contract.py tests/native_runtime/test_server.py -q
uv run pytest packages/workspace_service/tests/test_workflow_templates.py apps/api/tests/test_workflow_templates_api.py -q
npm --prefix integrations/rivet/spike test
```

The web lint command may report the repository's existing React-hook warnings; it must report zero errors. Run `scripts/check-dev-merge.sh` before merging this feature to `dev`. If an unrelated local process occupies a gate-reserved port, preserve that process and record the exact host limitation rather than terminating out-of-scope work.

## 2026-08-05 Verification Record

- An identical second upstream build reproduced all 228 files and the exact tree digest above.
- The four focused web suites passed (9 tests); the mocked retained-canvas Playwright journey passed; the production web build passed; ESLint reported 0 errors and 4 pre-existing hook warnings.
- Editor artifact, static-host, asset-catalog, API-contract, and native-runtime suites passed (26 tests, with 1 platform-dependent symlink test skipped).
- The retained Rivet compatibility suite passed (5 tests).
- Shipped-path scans found no public editor asset and no executable Rivet 1.25 marker.
- A live Wright workspace loaded `rivet.rivet-project` on the embedded Rivet 2 canvas and produced the requested screenshot.
- `scripts/check-dev-merge.sh` passed `git diff --check` and Ruff lint. The full gate remains locally limited by seven unrelated dirty-worktree files that fail the repository-wide Ruff format check. The live Playwright section was explicitly skipped because an unrelated BREP Vite process owns the gate-reserved port 5173; that process was preserved.
