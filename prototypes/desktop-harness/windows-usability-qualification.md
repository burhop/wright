# Windows desktop-panel qualification

Run in a Windows-local isolated checkout and test state. Do not use a share,
GB10 service or SSH. Preserve the independent engineering pilot. No engineering
start/resume/retry, account, credential or permission changes are part of this
walkthrough. Use disposable workflow/import/upload assets for writes.

The existing `native_navigation_acceptance.mjs` and promoted
`native_usability_acceptance.mjs` use the actual built `native-editor.html`, MCP
bridge and owning services. Their host is simulated. They must not be reported
as native OpenAI desktop acceptance.

1. Record the local source commit and applied source patch, Node/Python/client
   versions, local service/state identity and built resource SHA-256. Use the
   lockfiles and isolated dependencies. Do not silently use another checkout.
2. Build the native resource with `node apps/web/build-native-panel.mjs`.
3. Supply a navigation JSON with `scope: {workspace_id, session_id, path}`.
   For read-only history, add the exact `run_id`. For an existing PNG, add
   `preview_filename` and its recorded `preview_sha256`. Use
   `assert_usability: true` and optionally `device_scale_factor: 1.5`.
   Never combine `edit_copy: true` with a retained engineering run.
4. Run the existing journey through the Windows wrapper:

   ```powershell
   ./prototypes/desktop-harness/qualify-windows-panel.ps1 `
     -StateDir '<absolute local test-state directory>' `
     -Python '<absolute isolated Python executable>' `
     -NavigationInput '<absolute navigation JSON>' `
     -OutputDir '<new absolute evidence directory>'
   ```

5. For the full supplemental journey, pass `-UsabilityInput` with the same
   scope and explicit `phases`. Available phases are `friendly-search`,
   `connections`, `narrow-file-preview`, `create-edit-undo-redo-save-reopen`,
   `export-import-disposable`, and `files-preview-upload-download`.
   The final two editing/transfer phases depend on successful disposable
   creation; file delivery requires the exact retained PNG hash. Connections
   currently expects an existing completed SteveCAD setup and a visible
   inspection.json; omit unavailable scenarios and report them UNVERIFIED.
6. Keep screenshots, download hashes, call identities and failures. Assert
   selected-run Results 1/1, visible producing-step files, no false mismatch,
   viewport intersection/focus for previews, and normal/narrow usability.
   Robot Tracking Diagnosis's existing observer tests cover genuine mismatch,
   missing context and Undo without engineering execution.

`device_scale_factor` tests pixel density; it is not proof of actual Windows
display scaling or browser zoom. Add direct Windows scaling evidence separately.

OpenAI's Computer Use documentation excludes automating the OpenAI application
itself. Do not work around that restriction through another tool or private
debugging interface. Without a documented permitted host test interface, the
short remaining human check is: open the installed Wright panel, download/open
the retained file, switch conversation and return. Record those outcomes as
UNVERIFIED until directly observed. An MCP open receipt alone does not pass them.

Sources: [Computer Use](https://learn.chatgpt.com/docs/computer-use) and
[plugin UI bridge](https://developers.openai.com/plugins/build/chatgpt-ui).
