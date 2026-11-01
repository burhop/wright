# Windows qualification: ordinary native workspace files

27 October 2026. Continue the existing usability work in its separate Windows
test checkout. Preserve the engineering pilot and every previously qualified
build. No GitHub push/merge, installed-plugin change, account/credential change,
OpenAI-app automation, engineering execution or physical action is authorized.

## Candidate and scope

The candidate adds file-centered Home navigation and native-file open requests
over existing workspace/source/draft/transfer owners. It is opt-in and remains
uninstalled. Expected independently built `native-editor.html` SHA256:

`6e2c52c2464837e817e0d2d71776f05008090527d6840e5b7c5ef249d71ccd01`

Linux's actual-owner ten-check journey passed on these bytes. This includes
two substantially different existing workflows, edit/Undo/Redo/save/reopen,
stale-context hold and explicit reconciliation, a decoded retained PNG, visible
STEP/opaque-upload fallback, creation/title search, and browser export/download
plus one inspected import opening another file view. It establishes a simulated
host with real Wright UI/MCP/API/storage; it is not native-desktop acceptance.

Use the prepared source patch only in a fresh disposable copy of the previously
qualified Windows 0.27 source. Check preimages/application first. Do not overwrite
unrelated changes or fetch a supposed GitHub candidate: these commits are local.
If the baseline differs, retain the mismatch and adapt only this test checkout;
never weaken source, permission, hash, review or uncertain-outcome contracts.

## Reuse the existing Windows setup

Use the previously qualified local Python/MCP, Node, browser and private-state
initializer. Dependencies did not change: MCP Python 1.30.0, MCP JS 1.32.1 and
MCP Apps 1.7.5 remain the tested transport versions. Record actual Python, Node,
Chromium, OS and architecture. No shares, B: paths, SSH or GB10 service may be
needed. Keep API workspace state **outside** the Wright checkout; the application
correctly refuses engineering workspaces inside protected code directories.

1. Apply and verify the patch in that disposable checkout. Build with
   `node apps/web/build-native-panel.mjs`; compare the exact HTML hash above.
   Do not force a match or modify the bundle by hand.
2. Freeze the top-level prototype `.py` and `.html` files together into an owned
   runtime directory. Create a runtime JSON with `runtime` (that directory),
   `native_html_sha256`, and `python_paths` (this checkout's `apps/api/src` and
   existing `packages/*/src`). No credentials belong in this receipt.
3. Start one owned preview API using fresh local state, unused loopback ports and
   `--enable-desktop-bridge --enable-native-editor --enable-native-working-view
   --enable-native-workspace-files`. Set source import paths before loading the
   server, as in the prior Windows qualification. Retain private-state/DACL
   checks; do not broaden permissions. The preview disables MCP autostart.
4. Set `WRIGHT_PROBE_PYTHON` to the qualified isolated Windows Python. From the
   candidate checkout, run these sequentially with new output paths:

   ```text
   node prototypes/desktop-harness/native_workspace_files_setup.mjs STATE RUNTIME.json FIXTURES.json
   node prototypes/desktop-harness/native_workspace_files_acceptance.mjs STATE FIXTURES.json RUNTIME.json OUTPUT
   ```

   The setup uses normal workspace, source, template and upload owners. It
   refuses to replay a partial/completed output; inspect its saved intent and
   reconcile through existing owners after any failure. Its default PNG is a
   valid small synthetic image, not claimed engineering output. The browser
   journey permits edits only to designated disposable sources and one named
   creation/import. Engineering/provider/review actions are outside its allowlist.
5. Run owning/affected tests, TypeScript and focused lint. In particular include
   `test_native_workspace_files.py`, `test_native_file_tab_probe.py`,
   `test_native_process_tools.py`, `test_mcp_bridge.py`, and frontend
   NativeHomePanel/NativeNewWorkflow/native-file-client/native-transfer-client.
   Qualify ordinary Windows path/byte access and denial of changed/unavailable
   files. Keep privileged symlink fixtures explicitly unverified if unavailable;
   do not change account permissions to obtain a pass.

Inspect screenshots as a user. Assert accepted workflow names are visible in the
initial narrow viewport, file rows sort naturally, previews enter the viewport,
creation resets without repeating writes, and importing a copy leaves the
original file view/source/history intact. Do not replace these checks with
control-existence assertions. Host tab labels in this simulator are test UI;
the actual OpenAI dynamic-caption capability remains unverified.

Stop only owned test processes after their clients finish. Confirm their ports
are closed and all workflow-run/review/desktop-reasoning counts remain zero.
Return a concise JSON/Markdown receipt with exact source/resource identity,
commands, terminal exit codes, screenshots, failures and ownership/cleanup proof.
The parent will read this thread; no message to another chat is necessary.

Keep actual Windows native-panel rendering, native download/open, normal file
permission prompts and real conversation restoration **UNVERIFIED** unless
directly observed through a permitted interface. No user login is needed here.
