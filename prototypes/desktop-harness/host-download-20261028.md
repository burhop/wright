# Native-panel download correction

On 28 October the user confirmed that the retained PNG displayed in the actual
Windows desktop panel, then reported that **Download exact file** did nothing.
Windows image display passes; Windows download delivery failed that user check.

The shared preview used a normal `blob:` download anchor. The workspace Files
control also clicked a hidden anchor. These browser paths are unsuitable for a
sandbox that does not permit downloads. The installed official MCP Apps SDK
`@modelcontextprotocol/ext-apps` **1.7.5** documents `App.downloadFile` specifically
for host-mediated delivery from sandboxed panels. This is the public
`ui/download-file` protocol, guarded by the host's `downloadFile` capability.
SDK availability does not prove that this desktop build implements it.

The candidate injects one small download port into the existing shared UI kit.
Native previews and workspace Files request delivery through this port; ordinary
browser/Hermes hosts retain their existing browser download path. The native
adapter passes the already-scoped original bytes as an embedded MCP resource,
with a basename and MIME type. The URI is a filename hint, not a server path or
network fetch. Existing workspace/path, evidence hash and byte-limit owners stay
in place. No new filesystem service, remote upload, provider call or permission
grant is added. No engineering process starts or resumes.

The button shows progress and ignores duplicate clicks. Acceptance by the host
is described as a request, never confirmed delivery. Denial, missing capability
and uncertain transport results produce visible messages; none automatically
retry or silently substitute an unqualified transport. Stale replies cannot
change a replacement preview. Limits remain 16 MiB for workspace Files, 32 MiB
for the shared viewer; the existing native representation read is further bounded.

## Evidence

Local evidence directory:
`.local-run/engineering-run-journey-20261028/host-download/`.

| Check | Status | Boundary |
|---|---|---|
| Original installed 0.33 download | FAIL | User reports no visible response on Windows |
| Shared preview and workspace Files validation | PASS | 136 focused tests including exact bytes, denial, absent capability, size/name/scope/hash rejection and stale receipts |
| Different existing Robot Tracking Diagnosis telemetry | PASS | Retained CSV through shared download control and native adapter; controlled host reply, no engineering execution |
| Exact retained PNG and report download requests | PASS | Compiled UI, actual Wright storage/owners, public SDK, simulated host; iframe deliberately omits `allow-downloads` |
| Visible cancellation, no automatic retry | PASS | Same simulated host and unit tests |
| Image display, producing step, Results 1/1, same-run return, narrow view and reopen | PASS | Same read-only browser journey |
| TypeScript and standalone native resource build | PASS | No new dependency or external asset |
| New lint findings | PASS | Zero; four unchanged existing React lint findings remain in `representations.tsx`, baseline comparison retained |
| Windows save/download/open for the correction | UNVERIFIED | Requires actual desktop observation; simulated host acknowledgement is insufficient |
| Windows chat-switch restoration | UNVERIFIED | Unchanged by this correction |

The exact subject is workspace `4bcda80f-0afe-44d7-a8ef-33b2395300b0`, workflow
`workflows/block-preview-recovery.workflow.wflow`, completed run
`91c3fe3f4e0c477e9d9ea0d0dde477b2`. PNG SHA-256 remains
`1a1f6ca6c17ef90e5e0e9d6f70eb8f4e867405a0f89669ecdaca5dda1d23698f`;
report SHA-256 remains
`5e0e02a42274e2b37f7f1f4afe6b8cf71680d2bcfa7f7c4d77ddcac710f40dd2`.

The browser runner is `run-results.py` with its adjacent `native-results.mjs`;
`candidate-034-final/report.json`, `host-download-evidence.json`,
`download-declined.png`, `image-1100.png` and `image-480.png` retain the actual
proof. Earlier attempts remain preserved. Nine protected source, run, output
and backend metadata hashes are compared before and after qualification.
Full repository/CI gates are not claimed for this focused local prototype fix.

Only the named prototype is eligible for the qualified 0.34 update. Existing
backend service, accounts, credentials, gateway permissions and unrelated plugin
settings remain unchanged. An already-open 0.33 panel still contains its old
download control; the new resource must be opened for the Windows check.
