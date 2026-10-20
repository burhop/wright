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

## Completed CI reconciliation for the published model-routing candidate

All checks for `6a7617e5` are terminal. Two failed:

- Windows backend: the existing deadline/artifact test inspected disk 600 ms
  after timeout, before the late worker had finished cleanup. A controlled
  800 ms cleanup delay reproduced the failure on Linux; after the worker
  completed, no file remained. The corrected test holds promotion until the
  real timeout, then observes worker completion and checks both the artifact
  index and disk. The delayed case passes and deliberately disabled cleanup
  fails. Production cleanup is unchanged. Both gates now run this interleaving
  early; the contributor runbook records it.
- Engineering amd64 image: all bounded retries of the 782 MiB upstream FreeCAD
  download ended with TLS EOF / curl 56 at partial transfer. Classified as an
  upstream/download infrastructure failure, not a qualified image. No provider
  was removed or installer/security check weakened. The next consolidated
  candidate must still pass its actual amd64 build and smoke checks.

Exact logs: `ci-6a-windows-failed.log`, `ci-6a-amd64-failed.log`,
`ci-6a-terminal.json`, `deadline-before-controlled.log`,
`deadline-after-controlled.log`, and `deadline-negative-control.log` in the
local evidence directory. This is a new Windows pilot finding plus one complete
CI correction set; no serial one-error CI pushes were made. The repair remains
local until the repository gate passes.

## Windows acceptance and subsequent security follow-up

The Windows pilot subsequently qualified `d6eda2b4`: 70 focused tests; actual
Astra/high requests and frozen reasoning drift rejection; session-specific
selection; private Hermes replacement (47380 to 69280, shared 29792 unchanged);
Hermes-native workspace-status and SteveCAD reference calls; and durable resume
across API restart without another replacement. Original Windows receipts remain
in `D:/repos/wright/.local-run/windows-engineering-pilot/state/readiness/20261020-repair-d6eda2b/`.
The adjacent JSON distinguishes those actual Windows observations from the
controlled Linux probe and includes their retained capture hash.

The exact d6 pre-push and full merge gates passed. All PR checks finished:
28 success, one intentional skip. Local full WebKit lacked
`libgstcodecparsers-1.0.so.0`; separate 23 Chromium checks and full PR browser CI
passed. A subsequently published Critical certifi advisory prevents merging the
old dependency state. Security candidate `5f6ade75` pins 2026.10.19, preserves
strict Hermes override reconciliation, and verifies the actual certificate
bundles in Wright, Hermes and pip. Its fresh exact-image smoke and repository
qualification remain required. The previous resolver and pip-resource failures
are retained; no advisory exception or live profile update was made.

The remaining engineering blocker is hosted SteveCAD `generate_model` returning
`name 'wait_s' is not defined` with supported exact-revision export arguments.
Preserve document `40b599ff-8a70-4ae5-a717-3d7cd38f8fc7`, revision 1, successful
build `8bb9f109-fe80-4136-b953-727e71396f42`, and historical failed run
`1f20129a6b254135b20cb4d406384d1c`. No hosted provider source/deployment access or
repaired version has been established. A Wright update does not repair that
server. Remaining independent helper/recovery and different-workflow checks may
proceed; exact-revision STEP delivery, its bounded correction loop and Roadster
remain held. Do not recreate the design or replay an uncertain export.
