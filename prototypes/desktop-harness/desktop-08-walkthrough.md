# Wright 0.8.0: quick UI check

In a fresh conversation on the existing GB10 project, ask:

> Open Wright in the right panel. Show the available workspaces. Do not start any workflows or setup actions.

1. Select **stevecad-files-ui-proof** (if shown); otherwise select the existing UI-test workspace.
2. Open **Workflows**, open the SteveCAD workflow, then go **Back**. Check the canvas and source editor.
3. Open **Files**. Select `desktop-ui-check.txt`; its text should appear. Close it.
4. Select the large `.wflow` file. Files should explain its preview-size limit; the full workflow still opens in the editor.
5. Open **Connections** and inspect SteveCAD status. Account setup is confirmed, but sign-in is not yet qualified.
6. Narrow the panel and report clipped controls or confusing navigation. Screenshots with annotations are useful; exclude sign-in URLs and credentials.

No engineering run or review is required for this check. This verifies the real Windows desktop experience; the GB10 browser and installed-protocol checks already passed.
