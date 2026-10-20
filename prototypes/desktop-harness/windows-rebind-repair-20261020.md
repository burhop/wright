# Windows rebind repair and separate desktop UI continuation

## Journey and ownership

An engineer selects a workspace and its tools, then continues authoring in the
same isolated Hermes session. Refreshing that binding must not install a login
service, target another profile, kill a healthy replacement on an observation
timeout, or submit the pending model request before the refresh completes.
Wright retains its existing sync lock, gateway authority, request evidence and
durable workflow owners. Hermes owns profile resolution, process replacement,
tool connections and session memory. This is not a new service manager.

The Windows agent owns actual Windows qualification and engineering acceptance.
Roadster remains held. Prior UI, checkpoint and metrology passes remain valid
within their recorded limits; they do not establish Astra/SteveCAD execution.

## Findings

- PR165 candidate `6a7617e532ec37c3d103428f562df862e1f715fd` already repairs
  reasoning and session selection. Its local pre-push gate passed. Current-head
  CI and a current full merge gate remain integration requirements.
- The Windows follow-up uses Hermes
  `3c27eb6234bf91b8ceee9e9071591b31e9b148cb`. That exact source is available
  locally for inspection; the GB10 installed runtime is a different revision.
- Wright's 30-second `subprocess.run` timeout is shorter than a valid Windows
  restart: Hermes permits 30 seconds for draining alone, followed by absence
  checks and startup. A timeout kills the controller during that handoff.
- In this revision, Windows `gateway restart` calls `start()`, which may offer
  service installation for a manually launched profile. The pilot is explicitly
  launched with `gateway run`; service installation is not its lifecycle.
- The supported `gateway run --replace` command retains Hermes's profile/PID
  ownership and supervised-process guards. A narrow, explicitly selected manual
  replacement path can reuse it without implementing those guards in Wright.
- The HTTP API has authenticated process health but no MCP reload endpoint.
  Its toolset listing omits non-configurable MCP server toolsets; it must not be
  presented as proof that the Wright MCP connection is usable.
- A healthy listener or standalone STDIO probe is not actual Hermes tool-use
  qualification. The reported startup cancellation still needs reproduction
  and a real bounded authoring/tool check on Windows.
- The real pinned-runtime probe reproduced a second integration defect:
  Hermes filters MCP child environments. The old source binding omitted the
  isolated database, so its STDIO child opened the source checkout's default
  database and rejected the workspace. The shared source binding now supplies
  the authoritative database plus the configured Wright state/secret paths and
  API endpoint. API credentials remain environment references. This is separate
  from the earlier Windows launcher's installed/source-mode mismatch.

## Tasks and evidence

- [x] Read the Windows follow-up and preserve original evidence.
- [x] Reconcile the Windows timeout receipt with the exact runtime's restart
      implementation. Actual Windows process qualification remains Windows-owned.
- [x] Implement a bounded manual-profile refresh through the existing sync
      owner. Verify selected local process identity before replacement; observe
      the replacement identity separately and retain it across readiness waits.
- [x] Test wrong profile/endpoint, busy service, failure, cancellation, slow
      startup and retry without another replacement. Regress existing modes.
- [x] Exercise an isolated actual Hermes/Wright connection; distinguish Linux
      process proof, controlled transport proof and Windows acceptance.
- [ ] Run repository gates, integrate through PR and deliver exact commits and
      a focused Windows handoff. Preserve all failed attempts and limitations.
- [ ] On a separate branch, inspect current UI evidence and show an early
      rendered revision: clear navigation, stable workflow/run context and
      understandable results, reusing the shared canvas/client/backend.

UI changes do not belong in the restart repair. The subsequent UI work preserves
source/diagram editing, saved drafts, exact result/block links and common-view
fallback. It adds no executor or approval authority. Actual Windows panel
usability remains a distinct acceptance item.

## Local runtime evidence

The isolated actual Hermes revision `3c27eb6234bf91b8ceee9e9071591b31e9b148cb`
was run on Linux ARM64 with a controlled loopback model endpoint. It used fresh
Wright databases, profiles and workspaces; no live inference or engineering
provider was invoked. The original PID was replaced, the new PID was independently
confirmed, and actual Hermes tool search/description/call returned
`workspace_id=after`, `session_id=session-after` from Wright. Four controlled
chat-completion requests occurred. This proves the actual provider/MCP path on
this host, not Windows process behavior, Astra, or engineering acceptance.

Local evidence directory: `/tmp/wright-windows-rebind-evidence-20261020`.
`runtime-1792521971/report.json` preserves the missing-child-environment failure.
`runtime-1792522122/report.json` preserves an incomplete test fixture that did
not use Hermes's deferred-tool discovery. `runtime-1792522194/report.json`
records actual tool success. Private runtime logs remain local. The focused
regression log is `focused-refresh-02.log`; portable hashes and results are
recorded beside this plan before delivery.

The first `b1254aad` pre-push attempt stopped at the plaintext-placeholder scan:
the new test canary used an unrecognized placeholder spelling. It contains no
credential. The fixture now uses the repository's existing `test-secret-*`
convention; no scanner rule or exception changed. The failed log is retained
as `dev-push.log`; the corrected candidate still needs the complete gate.
