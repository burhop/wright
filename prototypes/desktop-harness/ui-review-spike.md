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
- [x] Build and qualify the named experimental plugin candidate.
- [x] Deliver incremental Windows source and retrieval instructions.
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

## Installed checkpoint

Named GB10 prototype **0.23.0** is installed from source
`ccfe4d947638f13b55e2d2a4e538d706ee94af24`. Its actual package command/resource
and installed-runtime browser/report/chat-message journey pass. All 56 existing
tool contracts and all unrelated desktop settings remain unchanged. The 164
original workspace files and five original binding/configuration/credential
files match their recorded hashes. Only explicit disposable diagnostic uploads
were written; retained source/run history and engineering outputs are unchanged.

The dedicated **Wright Windows UI qualification** task has received the verified
incremental patch without a share, SSH or GitHub publication. Its original 0.22
attempt exposed a genuine bridge permission-bit portability failure; the tester
is qualifying a narrow Windows check separately and has now reached the real
Windows-local UI. This does not establish this spike's native Windows acceptance.

One direct native report remains required: open **Report UI problem**, optionally
point to an element, enter a short comment, **Save UI report**, then **Ask chat to
review**. No screenshot or pasted handoff is required. Existing conversations may
retain old resources; if the action is absent, open Wright in a fresh conversation
on the same GB10 host. A UI open receipt is not evidence of rendering.

## Mounted inspection experiment — 27 October

The installed checkpoint above is historical. The current installed preview is
0.28 (`2d133c4a`, resource `6e2c52c2…cd01`), which does not yet contain this
experiment. Preserve its frozen runtime and state while qualifying a candidate.

The candidate uses the existing pinned MCP Apps SDK's public `App.registerTool`
to offer one app-owned frontend tool, `wright_ui_inspect`. It calls the same
bounded capture function used by explicit UI reports. Its closed empty input
schema accepts no selector, text, action or script. It returns only the current
Wright iframe's build, exact navigation, dirty state, theme signals and control
geometry. It does not click controls, save reports, expose source/form values,
take screenshots, inspect the desktop shell or grant process authority. It adds
no backend endpoint, dependency or general automation framework.

This is distinct from an MCP server tool: a host must discover and route the
mounted app's public tools. Support in the pinned SDK and a simulated host does
not establish that the actual desktop exposes it to the conversation. If it
does not, record that missing capability and retain explicit UI reporting.
The official [UI quickstart](https://developers.openai.com/plugins/build/app-quickstart)
recommends the MCP Apps bridge and local inspection; it does not establish
actual desktop discovery of this frontend tool. Do not use private debugging
interfaces or Office-specific Document Control as an alternative.

The actual compiled Wright/MCP/API/storage journey exercises public tools/list
and tools/call on both mounting-bracket and Robot Tracking Diagnosis views. It
checks scope/build, a visible report entry, unchanged full Source, no saves and
rejection of arbitrary input. The first journey's existing assertions passed,
but its returned geometry exposed a real defect: the Source textarea was 1134px
wide in a 1100px frame. The follow-up fixes border-box sizing and requires the
editor's actual bounds to fit at both 480px and 1100px. No-body-overflow alone
was insufficient. Keep that first result and visual failure as evidence.

Source also defaults to unwrapped lines with an explicit Wrap lines control;
this keeps engineering declarations near the top without removing, changing or
projecting accepted instruction bodies. Wrapping is presentation only and must
not dirty or save a workflow. All native-host and Windows delivery claims remain
separate from browser qualification.

### Installed 0.29 checkpoint

The mounted-inspection candidate is now installed as named prototype 0.29.0:
app source `7888226a`, resource `b2a55309…7abd`. Linux 2072 frontend checks,
types/lint and the 14-check journey pass. Independent Windows qualification
passes 89 focused checks, types/lint and all 14 journey checks on the identical
resource; five captures were inspected and owned services closed normally.

The reusable journey now optionally takes `WRIGHT_PROBE_MCP_CONFIG`, refuses a
different command/state/runtime before connecting, and reads its HTML from the
actual connected MCP resource. The exact installed-config journey passes all
14 checks. This remains a simulated host, not native desktop acceptance. A
separate read-only installed-owner image check verifies the real retained block
PNG (800×640 and its original SHA); the generic journey's one-pixel controlled
image must not be mistaken for that engineering preview.

Earlier named packages, services/state and unrelated settings are preserved.
The intentionally live isolated 0.29 preview is on port 18157; engineering,
reasoning and review counts remain zero. Actual native general-file rendering,
frontend-tool discovery, Windows delivery and conversation restoration remain
unverified. Existing-library CAD compatibility findings remain follow-on work;
no CAD viewer, parser or security relaxation was shipped.

Current private evidence index:
`/home/burhop/repos/wright/.local-run/desktop-usability-evidence-20261026/LATEST.md`.
