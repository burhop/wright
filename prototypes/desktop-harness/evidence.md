# Evidence index

## Live-owner admission patch qualified in an isolated candidate

`recovery-admission.patch` adds a four-line deterministic admission check using
the existing `service.process_interfaces.runs.is_live(task.run_id)` authority.
No new executor, recovery loop, model service or mutable request store is added.
The patch is not applied to the prepared Windows target: its four pinned files,
configuration and existing failure evidence remain intact.

Temporary candidate `/tmp/wright-desktop-recovery-candidate-20261011-01` contains
copies of the three prototype runtime files and two probe helpers. Only the
backend differs. `prepare_recovery_candidate.py` applies the reviewable patch to
a fresh private directory with `git apply --check` first. It reproduced all five
files byte-identically in candidate 02. This is an isolated fixture, not a second
maintained runtime. Shared packages come from the locked feature environment;
the profile does not attest every dependency, GUI build or upstream model.

Candidate profile:
`wright-desktop-prototype:0449d2a3f8acb3fdf09d3e2717e9750a30ba67522bf49c6585efd360a4bc3856`.
The real MCP positive control at
`/tmp/wright-desktop-recovery-positive-20261011-01` accepted this actual desktop
conversation's answer. Canonical run `cf3a7242cfb0411dbb54e5f5c9036c33` completed
with one request, one response and one consumed receipt. No separate model worker
supplied the answer.

The separate negative control at
`/tmp/wright-desktop-recovery-negative-20261011-01` reached one pending request,
then its exact owned API was killed with SIGKILL (terminal exit 137). The waiting
controller was stopped and the same API/profile reopened. Real MCP read the same
run `f989a912113549f38ee7d326a174051a` as reconciliation_required; an exact stable
start request returned the original receipt. A deliberate actual desktop late
answer was denied with HTTP 409. The original request/digest remains pending;
zero responses/terminal receipts, one byte-identical run log and no output
creation prove no consumption, replacement run or task replay. The probe exited 0.

This qualifies the narrow fix for response tasks; automatic interrupted-reasoning
continuation stays unsupported. The candidate action-task positive control,
abrupt MCP lease and uncertain-effect recovery are separate outstanding cases.
Reduced evidence: recovery-candidate-evidence.json. `git apply --check` confirms
the patch can still apply to the main feature files, but it must be deliberately
promoted/requalified after preserving the Windows candidate's stable baseline.

The two temporary candidate API handles were stopped and observed terminal
(exit 143); their private states and all raw evidence remain retained. The latest
checkpoint checks passed 79 tests in 1.85 seconds across prototype MCP/boundary,
Data Vault handoffs, desktop source execution, routing and recorded-run reads.
Known private proof tokens are absent from the prototype files. Diff whitespace,
the candidate preparation helper's Ruff check, Node syntax and patch applicability
checks pass. This is a local experimental checkpoint, not full repository gates;
the three previously reported format changes and broader installed/candidate
qualification remain outstanding.

## Current hosted authoring and original-example readiness

The established `scripts/recovery/capture_image_redesign.mjs` reporting,
screenshots, served-source checks and diagnostics now support opt-in private
auth/hosted mode and the prototype's current authoring case registration. Default
legacy acceptance remains separate. Authenticated captures omit the full trace
to exclude credential headers/unlock values; reports and screenshots are private
until their clean export is inspected. No route mocks or model worker were used.

Eleven focused cases are proved across retained stages 05 and 08 under
`/tmp/wright-desktop-editor-acceptance-20261011-*`. Stage 05 passes entry,
direct text/instruction editing, exact keyboard connection, typed rejection,
live drag/pan/zoom and Undo/Redo. Its save succeeded but the old visible-label
assertion failed. Continuation 08 reads that exact stored source and passes
save/layout reopen, managed-field draft rejection, real second-tab CAS conflict,
explicit comparison/reload and compact layout. All 56 observed frontend module
source snapshots match the working tree, with no missing/mismatched sources.
Its 69 API requests include no agent/inference or run request. This is focused
browser qualification, not a full legacy pass, clean commit, installed desktop,
right-panel proof, process execution or user acceptance.

The corrected current registration then passed **all 11 cases together** in
`/tmp/wright-desktop-editor-acceptance-20261011-09`. This final single walkthrough
is the current qualification record; earlier staged reports and failures remain
intact. Its exact module/source observations and request counts are recorded in
qualified-authoring-evidence.json. No scope was promoted to full legacy editor
acceptance or installed desktop qualification.

Every failed stage remains intact. The legacy harness expected seven Create
groups/prefilled input; current dev has four groups/empty new workflows. Further
helper mismatches concerned current direct editing/rename controls, keyboard
feedback location, Fit already at maximum zoom, abbreviated save text with full
accessible label, a hidden raw source path, and an unanchored test regex matching
`workflow` inside a source comment. No production editor contract was changed to
obtain a pass. Exact failure dispositions are in qualified-authoring-evidence.json.
Best clean image: gallery/07-hosted-editor-saved.png.

`existing_examples_probe.py` uses the existing template/source owners to create
fresh 1.0.0 Printed Replacement Part and Robot Tracking Diagnosis instances and
copy their original first scenarios/bindings. State:
`/tmp/wright-desktop-existing-examples-20261011-01`. All original and copied
scenario hashes remain intact; no campaign record, credential, run or review
authority was imported. The scenario requirements remain separately preserved,
not substituted for template seed defaults. Both catalog drafts explicitly fail
`WORKFLOW_NOT_READY` for their unbound first execution type. Manufacturing needs
qualified image/mesh/slicing/transfer bindings; Robot needs qualified bag retrieval,
alignment and metrics. Full original tasks, validations and reviews remain required;
no engineering run was started or claimed. Twenty existing template instantiation,
catalog and promotion tests passed in 0.98 seconds. Reduced readiness evidence:
qualified-existing-examples-evidence.json.

The Windows handoff target and all four pinned runtime files remain unchanged.
The additional editor/readiness state is separate from that served target and
from independent MCP testing. Live user configuration remains untouched.
The extra API 8104 and web 5204 processes were identified and stopped after the
walkthrough; both handles returned terminal exit 143. Their state/evidence is
retained. This records process termination, not a claim about graceful callbacks.

## Abrupt API stop during pending reasoning — retained qualification failure

Private probe `/tmp/wright-desktop-mcp-restart-proof-20261011-01` created a fresh
no-tools workflow through the same MCP/source/preparation/supervisor owners.
Run `a3367c9c3c92404f899a313ba684d5cd` published one immutable desktop request.
The exact owned API PID was inspected and killed with SIGKILL; its terminal
exit was 137. The waiting protocol controller was then stopped without an answer.
A new API reused the same database and exact recorded profile.

The real MCP client read `reconciliation_required` and the original pending
request/digest. Repeating the exact stable start request returned its original
receipt; it did not allocate a run, call a model or execute the task. The one run
log remained byte-identical, with no deliverable created. This is attachment and
reconciliation evidence, not successful continuation of pending reasoning.

**Failed qualification:** the bridge accepted one deliberate actual desktop late
answer (HTTP 200, accepted=true) despite the missing live run consumer. It remains
unconsumed in append-only evidence: one request, one response, zero terminal
receipts. The canonical run correctly still reports reconciliation_required.
`restart_reconcile_probe.py` exited 2 and retained the failure. Do not turn this
into a pass because no effect replayed. Pending-reasoning automatic restart and
late-answer admission after API loss require a fix/requalification. No substitute
provider, replacement run or recovery executor was introduced.

Raw fault/snapshot evidence: restart-fault.json, protocol-probe.json and
restart-reconciliation.json in that private state. Reduced data is in
qualified-restart-evidence.json. The existing Windows target and its four pinned
runtime files remain unchanged. No live desktop setting was changed.

110 focused existing tests passed in 12.25 seconds across the run supervisor,
API run lifecycle, recorded-run reads, input supervision and action supervision.
These establish existing reconciliation/no-replay regressions; they do not erase
the live bridge admission failure or qualify arbitrary uncertain tool effects.

Windows handoff snapshot 04 includes the reduced fault evidence and precise
stop/reconcile instruction. ZIP integrity, one-root/14-file layout, updated
documentation content and exclusion of all nine known private proof tokens
passed. Archive: `/tmp/wright-desktop-windows-handoff-20261011-04.zip`, SHA-256
`35875210da76d928324bbeb5148c146d610e3e20cb14f4a16f61cac74da36a02`.
An intermediate archive 03 placed updated docs outside the original package root;
it is retained as an invalid packaging attempt and must not be used. Archive 02
also remains retained. The target API 8102 and web 5202 were re-read successfully;
recorded binding matched and all four pinned files were byte-identical. The
runtime is disconnected until the Windows connection experiment. This is
readiness evidence, not Windows-installed plugin or panel qualification.


## Confined gateway and typed MCP decisions — 11 October 2026

The real local gateway proof at `/tmp/wright-desktop-gateway-proof-20261011-02`
completed run `6dc9a0b076f84a85bcc07cae3983f56b` using this desktop's proposal
and final answer. The existing gateway denied file observation without its exact
permit (`policy_denied`) and rejected a mismatched workspace binding. The input
was unchanged. Earlier proof 01 stopped because the helper expected an error
result rather than the actual raised GatewayError; the denial was preserved,
not weakened.

The full authenticated MCP proof is retained at
`/tmp/wright-desktop-mcp-proof-20261011-05`. Its 12-tool profile is
`wright-desktop-prototype:9c72a8e7389a3c04245fc1af4d89ceef115a943dcf31923dcd9fb9f19e0c0c1f`.
Without an enrolled grant, start was rejected (403). Local setup enrolled only
the exact existing source/input/tool-schema/output scope with manual approval
mode. MCP exposes neither enrollment nor a generic gateway-call capability.

Run `5a9f0dedc8b84aba931ad251e27ebf00` completed with one successful
`wright-workspace-files__inspect_file` dispatch and input SHA-256
`0a232d5575829b90463ecc78396036894128fdd9f2ed06477a0c7ece8b360fea`
unchanged. Saved inspection note SHA-256:
`1f6cad04d08ca5c8d75a5e00fdb51e2f0dacebacbd3aedd22ad2f31c3c570b38`.

The first controller disconnected after accepting proposal 1 because its polling
helper saw the previous not-yet-consumed request. The helper now waits for the
exact run/ordinal. Reconciliation read the same live run and retained successful
tool result, submitted only decision 2, and completed without replaying proposal 1.
This proves normal controller reconnect after a read, not arbitrary lost-write
acknowledgements or an API restart during an uncertain effect.

Proof 04's helper-construction failures are retained: initial argument-name
collision occurred before workspace dispatch (empty repository verified), then
a missing explicit secret-provider dependency stopped after source save but
before run start. Proof 05 used a fresh workspace; no failed source was overwritten.

114 focused tests passed in 2.26 seconds across MCP transport, private boundary,
durable handoffs, bounded decision loop, integration restriction/policy and model
routing. Ruff and diff whitespace checks passed for the current prototype edits.
Earlier broader regressions remain separately indexed; full gates are outstanding.

Served capture `/tmp/wright-desktop-mcp-gateway-gallery-20261011-01` passed through
the normal Workflows control and exact result viewer, with no standalone
agent/inference calls. An earlier private frontend lacked the existing workflow
feature flag; that failed capture is retained and the startup README corrected.
Best images are gallery/05-gateway-workflow.png and gallery/06-gateway-result.png.
Reduced checked data: [qualified-gateway-evidence.json](qualified-gateway-evidence.json).

## Windows host confirmed; handoff prepared

The user selected "Desktop is on Windows; prepare a handoff." No GB10 desktop
registration or Windows live installation is authorized by that choice. The
GB10 config file's observed SHA-256 still matches the initial value
`695791b28bbf618adb8d4dd7e7926fa7b5fd71a843b123b446456537310d75fb`.

Prepared windows-candidate/, windows-handoff.md and windows-relay-prompt.txt.
The executable and already-authorized SSH alias remain deliberately unresolved;
Windows app build, execution host, stdio loading and panel rendering must be
observed by the Windows agent. Official packaging/MCP/browser pages were searched
and opened again. The SSH wrapper is a proposal using documented stdio support,
not a claimed upstream Wright integration. No credential enters the handoff ZIP.

Archive `/tmp/wright-desktop-windows-handoff-20261011-01.zip` contains 12
whitelisted files, including the candidate marketplace/plugin, skill, relay
prompt, instructions, reduced qualification evidence and two actual screenshots.
ZIP integrity passed; all known private proof tokens were checked absent.
SHA-256 `8908e38114ab928ed66fa33f5fb0e5f97e50618997cbb8be591f64bf84fc18c2`.
The exact private API/web target was re-read and reachable, with the recorded
profile matching and MCP disconnected until the Windows experiment. Package
inventory: windows-handoff-package.json. Later changed files require a new
versioned archive; do not overwrite this retained handoff snapshot.

Current handoff snapshot 02 adds a canonical no-tools workflow-source example
and the latest Windows capability classification. Archive 01 remains retained.
`/tmp/wright-desktop-windows-handoff-20261011-02.zip` has 13 whitelisted files;
ZIP integrity and known-private-token exclusion passed. SHA-256:
`7b914cf1db6323f7254d3a453bc914b9126f734babaca30e89b2423ad03c189a`.

| Requirement | Evidence | Status |
|---|---|---|
| Isolated current-dev baseline | worktree and git inspection; plan baseline | verified |
| Locked isolated dependencies | successful uv sync, 79 packages | verified |
| Plugin packaging | https://developers.openai.com/plugins/build/plugins | documented, local connection unverified |
| Local app in desktop browser | https://learn.chatgpt.com/docs/browser | documented, actual Wright hosting unverified |
| Actual desktop reasoning callback | live source-runtime proof `23d7fdfb-6d00-48da-bba7-c015dd5db66f`, /tmp/wright-desktop-reasoning-proof-20261011-03 | verified via local-tool transport, MCP not yet connected |
| Frozen observable configuration | live proof `e1ec47e6-013e-43f4-9586-19091cb59a73`, /tmp/wright-desktop-reasoning-proof-20261011-04 | verified connection/instruction identity; model and app build unreported |
| MCP creation/source/start/desktop reply/result | protocol proof 03, `/tmp/wright-desktop-mcp-proof-20261011-03/protocol-probe.json` | completed through pinned SDK protocol client; installed plugin unverified |
| Workspace editor and results in hosted mode | served gallery 06 and request trace; `gallery/` | browser verified; desktop right panel unverified |
| Declared checkpoint continuation | proof 03 `checkpoint-probe.json` and `checkpoint-restart.json` | same run completed after MCP disconnect and controlled API restart; synthetic test input, installed plugin unverified |
| Handoff persistence, scope, cancellation, duplicates and drift | 26 focused tests passed; includes existing Hermes routing | callback/repository verified; complete run restart/reconnect not qualified |
| Existing source executor, gateway loop and instructions | 78 regression tests passed | verified fixture coverage, not live engineering tool qualification |
| Hosted workspace skips agent activation | component tests and served gallery 06 trace | browser verified without agent/inference API calls |
| Manufacturing and Robot Tracking proofs | fresh copies not yet started | unverified |
| Preserved platforms | pending focused regressions | unverified |

## Gallery

Actual hosted-browser screenshots and captions are in [gallery/README.md](gallery/README.md).
They show the completed reasoning task and saved result viewer. They do not
establish installed-plugin loading or desktop chrome/right-panel rendering.

## MCP lifecycle qualification

- Protocol proof 03 initialized MCP `2025-11-25` with locked Python SDK `1.28.1`,
  listed 11 tools, and reused normal workspace, source, input, supervisor and
  recorder owners. The actual desktop conversation supplied the reasoning reply.
  Run `ef1ba07937a74281a7fe165af18ef250` completed; output SHA-256
  `3e9a74e02ce0446e3e35ff116087ab2059b2df4b3c30202be291a0bd60d10500`.
- Proof 01 retained an HTTP-200 frontend fallback instead of the new scoped read
  route. No workflow or run was created. Routes now precede that fallback and
  the MCP client rejects non-JSON responses without retrying writes.
- Proof 02 retained an SDK conversion of a JSON string into an object for a
  union-typed tool argument. Wright rejected the invalid response. The public
  reasoning-answer argument is now text; core schema validation is unchanged.
  Normal MCP disconnect preserved the pending run. A separate client reconnected,
  cancelled it through Wright, and a deliberate late reply was rejected with
  HTTP 409. Evidence: proof 02 `cancellation-proof.json` (decoded snapshots).
- Abrupt MCP death, lease expiry, full Wright restart and installed-package
  loading remain unqualified. Restart at a durable declared input checkpoint is
  now verified separately below; restart during pending reasoning or an uncertain
  gateway operation remains unqualified. The current client set is not a liveness guarantee.
- Runtime profile hashes the adapter, dispatch, backend and MCP transport plus
  the installed MCP version. It does not attest the desktop model/app build or
  every Wright dependency. Those limits must remain explicit.

## Current focused checks

The latest focused backend suite passed 140 tests covering the prototype MCP
checks, desktop repository/execution, source runtime, gateway loop, routing,
workspace sessions, canonical input continuation, Hermes gateway and OpenClaw
stub. Invoke it with `.venv/bin/python -m pytest` from the worktree root: the
console-script invocation failed collection because existing cross-package tests
could not import `packages`. No production contract was changed for that failure.

Frontend build passed. The latest hosted workspace, health, process tabs and
process-tab routing suites passed 123 tests across five files; ChatSessions
passed 13 tests including a new retained-cache/no-Hermes-restore check. An earlier
relative-URL test-fixture mismatch is retained; the corrected tests are included
in these clean results. These are focused checks, not full repository gates or
full editor acceptance. Ruff check passes on the new modules; format-check still
requires three files to be formatted before a coherent gate-ready commit.

## Declared input and controlled restart

`checkpoint_probe.py` uses the existing Feature 083 declared-human-input fixture
unchanged (the normal source owner embeds versioned instruction defaults at
creation). Both AI replies were authored by this desktop conversation. The
selection `a` is explicit synthetic test data; no engineering approval is claimed.

- Run `6f7baf8d464b4241b6fe265acb85307b` reached declared checkpoint
  `checkpoint-691a6465417cfd87a6fa4b9e`, then the MCP client disconnected.
- The served diagram showed the wait. Its existing Answer in working view
  control opened the exact run, and browser reload retained it. With the MCP
  client absent, the common view correctly disabled continuation because the
  model/adapter route could not be revalidated. Screenshot evidence is retained
  in `/tmp/wright-desktop-checkpoint-gallery-20261011-01`; this is a disconnected
  recovery view, not proof of a usable connected Submit button.
- The exact isolated API PID was inspected, sent SIGTERM and observed terminal
  (exit 143). A new API process reused the same database and configuration.
  Recorded binding/runtime profile hashes remained identical.
- A new MCP client read the same waiting run and unchanged first output. The
  invalid selection `c` was rejected with HTTP 422. The valid synthetic selection
  `a` started the existing canonical continuation, with reasoning ordinal 2.
- The same run completed. First output SHA-256 stayed
  `0b4a329a6925cbafe73113ed0d6f3b9613c7665824809a153f460ff07bedfd7e`;
  second output SHA-256 is
  `2d2363341ee3c54bc9bbbefc0f7190daa3a259246d186913551c09cbb740917b`.
- This qualifies a restart at a completed segment's declared input wait. It does
  not qualify killing an in-flight task or replaying any uncertain effect.

## Live boundary rejection proof

Proof 03 `boundary-probe.json` records wrong workspace/session denial (403),
unauthenticated read denial (401), stale and already-consumed reply denial (409),
and frozen connection-profile drift denial (409). Both completed runs retained
their exact output records. Normal client disconnect left the connection false.
Consumed reply duplicates currently return an explicit conflict, not an
idempotent acknowledgement; uncertain transport writes require reconciliation.

## Live proof details

Proof 03 created and saved canonical source through the production WorkspaceService
and source owner, then used the existing source executor and durable recorder.
This desktop conversation inspected the retained task and authored the structured
inspection brief. No model HTTP client, Hermes response or separate SDK worker
participated. It proves local-tool-mediated reasoning, not MCP installation.

Proof 04 additionally invokes the existing routing-freeze owner. Its recorder
retains `openai-desktop-harness` configuration digest
`8ac5277077b0a9d2d1a2b5a932e6f7d285e67716f8a351776b0ea54f314e3dce`.
The desktop reused its previously authored brief for the identical engineering
prompt. Output SHA-256 in both proofs:
`029c019ffcf3e9ad2157fc723b171e2f396c086b619511f88b7b7805ef1aa48a`.
No measurement, physical action or manufacturing release is claimed.

Earlier fresh attempts 01 and 02 failed source path/authoring-field validation
before model requests. They are retained rather than weakening source validation.

## Host observations and fixes

- Network-restricted sandbox pytest stalled at asyncio thread wakeups after the
  SQLite consumer completed. Unrestricted execution of the same tests completed
  in 0.42 seconds and exposed a real cancellation-before-insert-return race.
  The adapter now observes the started write before acknowledging interruption;
  the corrected tests passed in 0.35 seconds. Owned stalled diagnostics stopped;
  unrelated processes preserved.
- npm sandbox installation failed DNS resolution. The authorized locked install
  outside that sandbox succeeded with 490 packages. Node 22.22.0 is below jsdom's
  declared minimum 22.22.2; build and focused tests work, so compatibility is
  observed only for these checks, not certified for the whole frontend toolchain.
- Frontend build passes. First focused UI suite had 73 passes and one failure
  caused by a newly written test using a nonexistent Files test ID. Correcting it
  to the existing Explorer control yielded 48/48 panel tests; the other 26 tests
  had already passed. No production control was changed to satisfy the test.
- First two served captures stopped at the browser unlock screen because the
  capture script checked it before asynchronous rendering. The script now waits
  for unlock or workspace and uses normal browser authentication. Failed captures
  remain under /tmp/wright-desktop-preview-gallery-20261011-01 and -02.
