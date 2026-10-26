# In-panel UI review spike

Approved 26 October 2026. Extend the existing prototype locally; no push,
publication, engineering execution, account or permission changes.

The user opens Wright in the desktop host, chooses **Report UI problem**,
optionally points at an element, writes a short comment, and saves a bounded
JSON report. The agent retrieves it through existing workspace file readers;
the user does not take or transfer screenshots. This is a developer prototype,
not general telemetry or proof of visual acceptance.

Reuse the native MCP Apps host context, navigation owner and existing
`NativeFileUpload`/scoped upload/storage/download services. No new backend,
tool, executor or action authority. Capture only Wright's own viewport and
control geometry, allowlisted theme values, bounded navigation and error
categories. Do not capture form values, source bodies, full DOM, provider
errors, host-page content, credentials or screen pixels. User comments are
explicit input; avoid secrets. Missing host signals stay unavailable.

Reports preserve exact workspace/session/source/run references as observations,
not grants or authoritative process state. Saving cannot execute, review or
resume a process. An uncertain save uses the existing upload reconciliation,
never automatic retry. Report bytes are ordinary untrusted workspace files.

- [x] Implement bounded capture and optional target selection.
- [x] Reuse staged upload with explicit save and confirmed receipt.
- [x] Prove known clipping and privacy/size limits with meaningful checks.
- [x] Exercise real bridge/storage/read-back and unchanged retained run.
- [ ] Build and qualify the named experimental plugin candidate.
- [ ] Deliver incremental Windows source and retrieval instructions.
- [ ] Observe one actual desktop-host report; keep this separate from simulation.

Native capture is limited to the plugin's own measurements. It is not a
screenshot, does not inspect or automate the OpenAI shell, and does not prove
host download or conversation restoration. Reuse Robot Tracking Diagnosis
observer regression for the shared run-context invariants; no engineering run.

## Qualified local mechanism

The final candidate passes 224 focused desktop/Robot Tracking Diagnosis checks,
TypeScript and ESLint, plus the actual MCP/storage browser journey. That journey
preserves the retained run, actual PNG and genuine mismatch controls. It injects
a clearly labeled oversized Refresh button as a negative control, selects its
visible part without activating it, saves one report and independently downloads
the exact saved bytes. It verifies the selected element's rectangle, clipping,
relative selector, build/resource identity, scope and bounded report size.

After confirmation, **Ask chat to review** sends only the saved file reference
through the standard MCP Apps `ui/message` bridge. Sending is explicit, bounded
and attempted once. The fixture verifies the exact message and retained run
context; this is not proof that an actual native chat turn ran. Missing support
and unconfirmed delivery leave the saved report available and do not retry.
The upload owner's existing read-only reconciliation handles uncertain saves.

The UI report schema is `wright.ui-review/1`; reports are at most 64 KiB and
save as `uploads/<sha256>/wright-ui-review-<uuid>.json`. The tester can discover
them with the existing workspace file list, read exact bytes through the existing
download owner, verify SHA-256 and inspect JSON as untrusted observations. No new
tool, endpoint, storage authority or dependency was added. Raw DOM text, form
values and raw error messages are deliberately absent. User comments are limited
to 500 characters and common accidental API-key/Bearer patterns are masked; this
is not a promise to detect every secret a person might type.

An initial picker banner intercepted the test target; pointer events are now
transparent on that instruction banner. The failed screenshot/log is retained.
The first Vitest invocation used the wrong cwd and a later duplicate-click test
looked up the button's obsolete label after it became busy; these failed checks
are retained separately from the successful final run. No assertion or security
guard was relaxed to pass.

Private local receipts: `.local-run/ui-review-20261026/`, especially `journey-e/`,
`panel-final-e.log`, `types-qualified.log` and `lint-qualified.log`. Exact resource
SHA-256: `946446ea0c7c7190b63e6be43e411942c05dfd5e8c531ae48e480e7a49b9bf2e`.
Host/context fields are reported signals; a simulated host can advertise
`platform: desktop`. That field alone never establishes native-host provenance.

Sources: [MCP Apps UI bridge](https://developers.openai.com/plugins/build/chatgpt-ui)
and [host style updates](https://developers.openai.com/plugins/changelog).
