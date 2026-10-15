# Declared input upload in the desktop panel

Status: local implementation, not installed or qualified. Branch starts at
3f7ad9b2 while PR156 CI runs; preserve that candidate and all private services.

Journey: open an accepted process through Workflows, choose a file for one declared
file input in Run and results, inspect its accepted reference, prepare inputs and
check readiness. Upload never starts work, approves a review or edits source.

Reuse CommonProcessView/InputEditor, ProcessClient.uploadInput, its ArtifactRef
validation, the closed native process transport, and the existing multipart
process-interface upload route/artifact owner. No executor, vendor protocol,
new database, arbitrary URL download or workspace-write proxy. V1–V7 apply.
Host file-library integration remains optional/unverified; this slice uses the
existing user-selected File control and must qualify actual Windows hosting.

The closed UI-only update port carries exact workspace/session/source digest,
declared input ID, simple filename and bounded base64 bytes. Preserve the current
32 MiB owning-client limit; qualify the actual MCP message boundary rather than
claiming the host accepts that size. Oversize, malformed, stale/foreign scope and
non-file declarations fail closed. The owner retains format, storage and indexing
authority. Accepted source and existing runs are unchanged. Runtime hashing binds
the modified transport; old sessions stay on their frozen implementation.

Keep uncertainty visible and never retry automatically. Losing an upload reply
may leave a private indexed artifact; it does not establish input binding or
readiness. Do not start a replacement run or infer a reference from a filename.

Tasks/evidence:
- [x] Thin typed upload operation and multipart delegation; exact-byte unit checks.
- [x] Adapt the existing client FormData and enable the existing common-view control locally.
- [ ] Test valid bytes, limits, wrong scopes/source/input, malformed encoding,
      cancellation and unknown outcome without replay; regress current operations.
- [ ] Actual isolated MCP/browser proof using declared inputs on two substantially
      different existing workflow definitions, preserving their requirements.
- [ ] Qualify served workspace/editor entry and native Windows separately; do not
      count simulated hosting or upload as complete engineering execution.
- [ ] Repository gates, reviewed evidence and scoped package update before enablement.

Download/export, arbitrary file management and actual engineering provider runs
remain separate goal obligations. Missing upload support retains the common view
and explicit error; no generated process UI or tool-confinement exception changes.

Focused checkpoint: 38 backend and 24 frontend checks pass; TypeScript, Ruff and diff checks pass. Evidence: /tmp/wright-desktop-input-upload-evidence-20261015/checkpoint.json. Actual owner, wire, browser and Windows qualification remain open. No package update or engineering-run claim.

Actual-MCP checkpoint: fresh state02 passed 59-byte and 32 MiB original-byte uploads via the existing artifact owner. Stale source, undeclared input and unsafe filename were denied without file creation. Source unchanged, no runs started. First state01 failure retained: preview route guard denied upload before owner; exact route admitted only in native working-view mode. Actual Windows message/file-picker limits, browser UI and different original workflow declarations remain unqualified. API8192 remains on session39140; see external checkpoint.json.

Browser checkpoint: existing home/editor harness passes seven checks including selected-file upload, exact owner-reference display, stored-byte verification, no run creation and unchanged source. Narrow-panel screenshot and report are retained under state02/browser-home-1792053355504. The first fixture attempt correctly hit the unsaved-draft guard before uploading; a fresh observer corrected the test without altering production draft handling. Windows acceptance, two original workflows and repository gates remain open.

Existing-declaration probe remains unqualified: the manufacturing library template has no bound mesh execution type and the existing working-view compiler rejects it before upload (READINESS_UNSUPPORTED). Preserve this readiness contract. The first filename and second duplicate-name fixture failures are retained separately; no runs started. Use a fully prepared original workflow when its genuine provider bindings are ready, not a substituted synthetic task. See external checkpoint existing_declarations.

Updated UI checkpoint: owned state02 API stopped cleanly before the rebuild;
new state03 API8192 uses session46887. Actual MCP small/32 MiB and three negative
cases pass again. Seven actual-owner browser checks pass, including details
expand/collapse with exact reference, source preservation and no process start.
The stored selected bytes were independently verified. Documents no longer
show an irrelevant bitmap warning; uncertain uploads show the existing typed
reason and remain unbound without retry. Shared UI/client tests:110 passed;
affected owner/bridge/source tests:81 passed; other frontend regressions:29
passed. TypeScript and native bundle build pass. Actual Windows acceptance,
original prepared workflow qualification and repository gates remain open.
Screenshot and exact receipts: external checkpoint current_ui_checkpoint.
