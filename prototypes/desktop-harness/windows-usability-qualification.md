# Windows desktop-panel qualification

Run in a Windows-local isolated checkout and test state. Do not use a share,
GB10 service or SSH. Preserve the independent engineering pilot. No engineering
start/resume/retry, account, credential or permission changes are part of this
walkthrough. Use disposable workflow/import/upload assets for writes.

Windows private-file qualification uses the existing locked pywin32 dependency
to inspect the credential's owner and DACL on the same read handle. Only the
current process user, Local SYSTEM, local Administrators, and OWNER RIGHTS for
one of those owners may receive effective grants. Null DACLs, unknown ACE kinds,
other principals, directories and final reparse points fail closed. The handle
does not share write/delete access. Validation never repairs existing ACLs;
Unix retains its symlink and group/other mode checks. Disposable real-Windows
positive and over-permissive read/write/ACL/ownership controls are in
`tests/test_private_api_credential.py`. No account or global-policy change is
needed. This local check is not proof of OpenAI host rendering or installation.
The Windows check also covers the API URL, binding and pin metadata before
constructing an HTTP client: writable routing could disclose a private token.
These small configuration files and the credential are bounded to 4 KiB each;
unavailable ACL inspection fails closed. The reader changes no permissions.

The 26 October Windows tester qualified this reader with 45 focused checks and
actual local MCP/browser initialization. Its fix commits were
`18aa7f178d8725d6717342100339c7dbe4c72937` and
`2461ceb27716d6daf3b88b6d7a526d71f901b145`. The nonsecret transfer patch is
16,904 bytes, SHA-256
`e79da0c31ebd3f860daa2dc1b8b1e63875e6f30135fb1278b907b2963520bbfe`.
The integration worktree applied it cleanly alongside the opt-in native file-tab
probe and passed 51 Linux checks; 10 real-Windows controls are explicitly skipped
on that host. Linux results do not replace the Windows controls. A prose transfer
was corrupted; the preserved replacement was extracted from machine output and
passed strict base64, gzip and exact patch identity checks before application.

The existing `native_navigation_acceptance.mjs` and promoted
`native_usability_acceptance.mjs` use the actual built `native-editor.html`, MCP
bridge and owning services. Their host is simulated. They must not be reported
as native OpenAI desktop acceptance.

1. Record the local source commit and applied source patch, Node/Python/client
   versions, local service/state identity and built resource SHA-256. Use the
   lockfiles and isolated dependencies. Do not silently use another checkout.
2. Build the native resource with `node apps/web/build-native-panel.mjs`.
   The bridge enforces the frozen `native_editor` hash. For a new presentation,
   prepare an isolated private client-configuration directory pointing to the
   local test API, with the same authorized binding and only the tested UI hash
   changed. Preserve the existing backend's configuration and checks. Do not
   transfer credentials between hosts or edit the independent pilot's pins.
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
   currently expects an existing completed SteveCAD setup; file-preview phases
   expect a visible inspection.json. Omit unavailable scenarios and report them
   UNVERIFIED.
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
