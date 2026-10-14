# Wright 0.7.0 — quick desktop check

Open a **fresh conversation on the existing GB10 host**. Do not restart the app.

Paste:

> Open Wright home in the panel. Check the connected plugin supports New workspace,
> Files and Recent runs. Do not run workflows or start provider sign-in yet.

Try these controls:

1. **New workspace** → name it `My desktop UI test` → **Create workspace**.
   It should select the new empty workspace automatically.
2. Select **SteveCAD Files UI proof** (the prepared isolated test workspace).
3. **Workflows** → open `stevecad-native.workflow.wflow`. Inspect the canvas or
   source, then **Workspaces** to return. Save any edits before leaving.
4. **Files** → search `stevecad`. This currently lists files; upload/download and
   arbitrary file previews are not available yet.
5. **Recent runs** → select the workflow. “No recorded runs” is expected in this
   fresh SteveCAD test workspace. Opening history never starts a run.
6. **Connections** → search SteveCAD → inspect **Saved setup**. Do not approve,
   apply, enable or sign in during this UI walkthrough.

Report any confusing control, clipping, failed navigation or error. A screenshot
with annotations is useful. Actual CAD execution and the Windows→GB10 sign-in
route are still being qualified; this walkthrough does not establish either.

If the new controls are missing, report the connection/tool version you see.
Do not reinstall other plugins, copy credentials or switch execution providers.
