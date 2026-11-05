# Production integration acceptance matrix

**Status:** candidate qualification in progress, 5 November 2026. Not production accepted.
Parent: [plan](../codex-production-integration-plan.md). Work: [tasks](tasks.md).

Historical proofs are regression inputs, not a blanket pass on a new candidate.
Use **PASS / FAIL / BLOCKED / NOT TESTED / OUT OF SCOPE**, with exact evidence.
Record source implementation, automated browser tests, installed runtime, native
desktop observations and human acceptance separately. Do not average them into
one success percentage. The checkpoint below records the new candidate separately
from the mandatory acceptance definitions; a partial boundary pass does not satisfy
an entire story.

## Native matrix observation — 5 November, head 15dbfef8

Actual installed desktop MCP tests now PASS on Windows x64 and Linux x64 using
the same `59d8274e...` wheel. Both retain exact viewer bytes and saved source
through restart and stop successfully. This establishes the tested backend
profile, not Windows Codex app rendering/download/chat restoration.

macOS ARM64 connected, served the exact viewer and preserved saved source through
restart, but FAILED final shutdown. CI's original receipt omitted the failing
command result; the cause is not yet established. A qualification-only correction
now retains failed CLI results/exit codes and a read-only doctor observation.
It does not change shutdown policy, retry a failed action or claim a runtime fix.
Evidence: `ci-desktop-15dbfef8/platform-summary.json` and retained macOS job log;
required current-head CI and all original engineering/UI blockers remain open.

## Native desktop profile qualification — 5 November

| Boundary | Result | Evidence / limitation |
| --- | --- | --- |
| Q06/Q08 installed package at df6ea4c4 | PASS for native Hermes lifecycle only | `current-native-platform-evidence.json`: actual Windows x64, Linux x64 and macOS ARM64 CI receipts use the exact wheel below. No Codex desktop rendering claim |
| Q08 installed desktop MCP profile | PASS on Linux ARM64 | `desktop-native-matrix-local/dist/desktop-native-Linux/receipt.json`: exact new CI step, separate installed manager/runtime, authenticated connection, exact viewer bytes, save/reopen/restart and owned shutdown; zero engineering runs |
| Q06 Windows desktop MCP profile | NOT TESTED by the new matrix yet | The candidate matrix now invokes the same desktop harness on Windows, Linux and macOS; current correction's CI evidence is required |
| Q10 product gates | PASS for recorded scope | Full gate 15 at parent `2114dd23` plus unchanged generated assets/identical wheel; normal pre-push gate 7 at `df6ea4c4`. Current correction's gate and CI remain pending |

The named 0.39.0 wrapper now serves the df6ea4c4 artifact through its owned runtime,
verified by `connections-live-update.json` and `connections-live-profile-check.json`.
Its wheel and UI hashes match the latest bounded qualification below. Historical
statements about earlier installations remain dated evidence. Windows native file
selection remains FAIL from the user's observation; GUI checks, complete engineering
journeys and human reviews are not established by backend CI.

## Latest bounded qualification — 5 November, Connections correction

These observations supersede only the matching subset claims in the older
checkpoint below; mandatory stories remain unchanged.

| Boundary | Result | Evidence / limitation |
| --- | --- | --- |
| A03 isolated installed custom MCP | PASS for setup/control subset | `installed-connections-corrected/` and `installed-connections-management-continuation-3/`: actual pinned OASiS protocol with 17 tools; explicit setup, validation, enablement, start/stop, disable, replacement draft and removal. Zero engineering tool calls; no invocation approval. OAuth/reconnect/update impact remains incomplete |
| A05/A12 preserved editor and exact run | PASS for installed exercised subset | `connections-retained-regression/`: rename/Undo/Redo/save/search/reopen/export/import and retained image → producing step → same exact run; original evidence unchanged |
| A06 references/validation/interface source | PASS for bounded transfer subset | `installed-dependency-transfer/asset-transfer-proof.json`: identical declared reference and pinned validation-profile bytes, tamper/collision rejection; explicitly inactive portable interface fixture. Does not establish saved-interface authoring/export/build acceptance |
| Q01/Q08 final artifact | PASS for installed Linux and Docker subset | Wheel `59d8274e048ddb08a72d3e746d1ce0224eab0ab571ceff2a7cf97dd3ab679abe`; UI `6a8d381b7970c5415b0640362f315038ba815c8deede41bd77b971e2a949bd74`. Final rebuild matches installed tested bytes; authenticated configuration denies anonymous reads |
| Q06 native Windows backend lifecycle | PASS on preceding b9553937 only | Actual installed CI install/start/status/doctor/stop/uninstall with Hermes adapter. This is not Windows Codex panel, viewer, file-delivery or chat-restoration acceptance |
| Q10 CI / current local correction | Prior pushed head PASS; correction pending | `pr191-third-cycle-final.json`: all 30 checks/11 workflows terminal without failures on b9553937. Later local gate failures for image revision metadata, test formatting and stale checked-in UI are retained; corrected final head still requires its own prescribed gates and CI |

The named installed wrapper remains 0.39.0 on the previously qualified runtime
until a separately recorded scoped update. The new UI's connection checks are
visible without opening credential settings. Normal entry and 480 px layout are
verified in a simulated host, not the actual desktop. No personal sign-in,
engineering review, engineering workflow run or physical operation was performed.

## Candidate checkpoint

Candidate: unpublished Wright 0.1.9, maintained branch `codex/codex-production-integration`.
The normal-build wheel with the installed migration correction is SHA-256
`faa5bf561e93529ce01ede7ab2492f465db27bfb2160fce28bcf99f3670bf277`;
UI SHA-256 `95bfbff7d17b34eabad7b7cbf23bedf9e989e5637173c01b656cd4ab2ac6992f`.
Evidence paths below are relative to private `.local-run/production-integration/`.
This is the preceding migration-correction wheel; the current named 0.39.0 runtime uses the later file-list wheel documented below. Live Windows observations still refer to prototype 0.38.1; the current chat reports its older connection.

`installed-gate-artifact/` qualifies the identical UI from the normal build
(wheel `6e356e931d0af0f9552702fbbe8436b94bf4fd86f6438657d16b147184482e77`).
`light-manager-update/` qualifies the later migration correction through the actual
dependency-light manager: install, saved source, restart, update and exact reopen.
Earlier wheel `6301fe9e...` had the correct desktop panel but stale main-app assets
and runtime-lock metadata; it is superseded for the full installed-app claim.
The normal pipeline regenerates both from current source and the frozen uv lock.

The installed authoring proof asserts the exact imported destination and source.
The earlier `installed-authoring-2` PASS lacked that assertion and is superseded.
Declared reference transfer is additionally verified below; full typed-port
interaction and validation/UI dependency transfer remain beyond these fixtures; no full portability or Windows claim is inferred.

| IDs / boundary | Status | Evidence and remaining requirement |
| --- | --- | --- |
| A01, Q01 installed Linux artifact | PASS | `installed-gate-artifact/installed-receipt.json`: installed package outside checkout, authenticated API and MCP, exact packaged editor; Windows install remains NOT TESTED |
| A02, A05 selected workspace/save/reopen/search | PASS for exercised subset | Installed receipt plus browser receipt: disposable source save/reopen and retained title/normalized-name search; rename, Undo/Redo, save/reopen and exact import are exercised; full typed-port interactions remain NOT TESTED |
| A03 tool management; A04 actual conversation authoring | NOT TESTED | Existing contracts retained; no new account/setup actions or live conversation authorship claimed |
| A06 full portable round trip | NOT TESTED | Minimal installed export/import and exact destination/source PASS; complete dependency transfer remains NOT TESTED |
| A07 automatic native file selection | FAIL on observed 0.38.1 | `native-observation.md`: all three controls opened text. Manual external control rejected missing saved context; not evidence of authorized workspace viewer failure |
| A07 explicit panel fallback | PASS in simulated host | `installed-gate-artifact/browser/receipt.json`: native acknowledgement followed by **Open workflow here**, real packaged editor and source. Windows fallback remains NOT TESTED |
| A08 readiness entry | PASS for retained read-only case | Same browser receipt; no engineering start and no claim all handle capabilities are ready |
| A09–A11 actual handle reasoning/review/correction | BLOCKED | Reviewed strength basis and usable provider bindings remain required. No fabricated reviews, material limits or solver results |
| A12 retained results navigation | PASS for exercised subset | Exact selected run, decoded hash-matched image, producing-step Results 1/1, no false mismatch, return to same run. Edited-source mismatch/Undo also passes in the later installed check; full engineering summary remains pending |
| A13 actual Windows file delivery | NOT TESTED | Verified bytes in MCP/browser do not prove Windows download or open |
| A14 changed-input full engineering rerun | BLOCKED | Requires the same real engineering basis and review as A11; historical runs preserved |
| A15 installed restart | PASS for exercised subset | `light-manager-update/receipt.json`: dependency-light CLI installs, restarts and updates with exact saved-source preservation; copied completed-run restart also passes. Broader cancellation/uncertain-effect fixtures retained; no live-engineering claim |
| A16 actual chat switching | NOT TESTED | No Windows automation available in this session; no observation requested while user away |
| A17 narrow panel | PASS in simulated host | Browser receipt and `results-narrow.png`: 480 px no body overflow. Human usability acceptance remains NOT TESTED |
| A18 generality | NOT TESTED for full new proof | Retained block regression passes; complete existing Robot workflow and Hermes qualification remain pending |
| Q02 scoped option reads | PASS | `options-boundary-tests-2.log`: 408 passed, 10 skipped across relevant boundary suite; new fixed-kind reader rejects cross-scope/arbitrary-route requests |
| Q03–Q04 complete content/configuration controls | NOT TESTED as complete acceptance | Existing contract regression retained; backend/security gates passed at `3f373cf0`; later gate 9 passes with the documented local browser-host exception; complete CI remains pending |
| Q05 copied-state migration | PASS for exercised subset | Installed receipt: original and copied workflow/history/output hashes unchanged; selected immutable input/start receipt copied without credentials, live jobs or grants |
| Q06 Windows local; Q07 Windows + GB10 | NOT TESTED on maintained candidate | Existing prototype screenshots remain historical evidence only |
| Q08 Linux ARM64 / Docker | PASS for installation / security subsets | Installed Linux receipts pass. Migration-correction image `60085b5e80b0494401cfa48959407b9cfa22a3f39d466bd94d103ba2d5b7b773` passes exact-image security, smoke and authenticated desktop opt-in checks (`docker-smoke-current.json`, `docker-desktop-check.json`). x64 remains NOT TESTED; current file-list image `635a9c835da4b760d2190d9b6be35ed40d868b0edacf4eb8b254c39595083129` also passes exact-image security/smoke/desktop opt-in checks |
| Q09 compatibility/fallback | PASS for local contracts | Content-hashed assets, versioned plugin files, scope checks and explicit fallback preserved; host selection is unresolved |
| Q10 repository gates/CI | Local gate PASS with documented host limitation / CI NOT TESTED | Gate 9 at `de0886b9` passes using the existing documented `SKIP_PLAYWRIGHT=1` option: WebKit 2370 aborts before Wright on this 64 KiB host. Separate installed Chromium journeys and isolated Firefox 19-test suite pass. This is not a full browser PASS; normal pre-push and complete current-head CI remain required. Gate 7/8 failures are retained |

## Subsequent file-list correction

Normal-build wheel `9b03e94d95ab5fe742d9f1b3b6d96013d28bc47a483b2488ca774ce7c6d4a2b8`
and UI `74aeb02f85013de9358f05523e7ab460f1bbad4171d64d2bfb4623ee661792b9`
pass `file-list-final-proof/installed-receipt.json` and its browser receipt.
Duplicate filenames have distinct visible folder captions and accessible names;
canonical run records are collapsed but searchable/openable. Ordinary engineering
JSON is not hidden by extension. File types stay on one line at 480 px. The
installed authoring and exact retained-results journeys still pass. Screenshots
are Linux Chromium with a simulated desktop; these do not establish Windows
acceptance. This later wheel now runs in the authorized owned candidate, behind the unchanged 0.39.0 wrapper. `file-list-live-update.json` and `file-list-profile-check.json` verify the normal manager update, actual MCP profile and exact hashed UI. Original services/settings and engineering files are preserved; no desktop restart or Windows observation is claimed.

`firefox-isolated/receipt.json` records 19 existing workspace-surface tests passing.
The first standalone attempt lacked an API and is retained as failed environment
evidence. `webkit-host-limitation.json` and debugger logs establish a browser
startup limitation; no browser binary, kernel, test assertion or security policy was changed. Gate 9 uses the existing documented local-host skip option, with complete CI browser coverage still required.
The related [upstream WebKit/64 KiB report](https://bugs.launchpad.net/ubuntu/+source/webkit2gtk/+bug/2156420)
supports the diagnosis; current local binary disassembly is the exact-host evidence.

## Additional installed qualification (5 November)

- `installed-first-contact/`: normal chooser → one named workspace → New workflow → exact workspace/session chat handoff, with one simulated-host message, visible next action and 480 px layout. No generated workflow or native Windows chat delivery is claimed.
- `installed-reference-transfer/asset-transfer-proof.json`: actual installed MCP owners export/import an existing declared SVG reference with identical source and asset bytes, reject collisions, preserve missing-capability readiness and start zero runs. Saved UI/validation dependency portability remains unverified.
- `installed-edited-source-proof-3/browser/receipt.json`: a genuine unaccepted source edit shows the mismatch, separates the current unproduced output from explicitly marked saved-run results, and Undo restores Results 1/1 and the matching inspector. `negative-control-audit.json` verifies every original and copied preexisting file unchanged and the sole new copied-workspace draft matches its exact observed request. The read-only helper's FAIL is retained: its no-new-file assertion intentionally does not permit this new test draft. The independent strict audit qualifies this negative control only; it does not relabel that helper run or weaken the normal preservation check.

## Mandatory stories and controls

| ID | Task / action | User-visible and authority acceptance | Required proof |
| --- | --- | --- | --- |
| A01 | Install/open Wright | Normal packaged installation gives a usable chooser or an actionable connection error, without repo/private paths or source text masquerading as the viewer | Clean Windows-local installation plus actual desktop observation; installed build identity |
| A02 | Create/select workspace | Simple name/selection; clear active destination; loaded tools selected subject to existing grants; no workflow started | Both UI and chat entry, fresh and populated workspace; scope/duplicate handling |
| A03 | Maintain tools | Add catalog/custom MCP, private sign-in, reconnect, validate, update, disable/remove; status distinguishes auth/access/compatibility/readiness; affected workflows identified | Real setup for selected providers; controlled expired, denied and incompatible cases; sensitive-data checks |
| A04 | Describe the job | Prompt/images are retained in the correct workspace; editable workflow distinguishes facts and assumptions and declares reviews; creating a design does not require its future CAD document | Actual conversation authoring and exact saved references; failed/unsupported attachment delivery visible |
| A05 | Create/name/edit/save/reopen | Accepted title survives and is searchable with normalized filename; Diagram/Source, typed connections, instructions, Undo/Redo, layout and dirty draft recovery work | Served normal entry; pointer/keyboard regression; concurrent save conflict preserves both work and authority |
| A06 | Export/import | Disposable copy retains source, instruction bodies, layout and required reference/validation/UI dependencies; capability gaps diagnosed | Byte/identity checks across different workspaces/defaults; no credentials, runs, approvals or trusted UI builds transferred |
| A07 | Open files/viewers | Workflow, image, PDF and required engineering-format viewers display content visibly with a clear return; unsupported format says so | Actual desktop workflow route plus representative files; tested license/format inventory for third-party viewers; no raw-source fallback claimed as success |
| A08 | Start readiness | Inputs are supplied/defaulted/upstream-produced/declared interactions; missing tools, unsupported semantics/context settings and authentication diagnosed before effects | Negative controls and visible link to the exact fix; saving an incomplete draft still works |
| A09 | Execute with Codex | The current conversation supplies reasoning; Wright owns sequencing and gateway actions; progress and failures understandable | Exact request/response and gateway evidence including image/helper/correction/recovery calls; no fallback model/platform |
| A10 | Review and continue | Exact specification/output/criteria visible; invalid input or stale approval rejected; valid authorized answer continues the same waiting run | Declared input and review tested separately, duplicate response control; human review remains human for live engineering |
| A11 | Check/correct engineering output | Exact model measured against design; failed check holds downstream work; configured bounded correction produces a new checked subject or clear exhausted state | Actual provider handoff plus deliberate noncompliance and missing-check controls; no AI verdict substituted for measurements |
| A12 | Read results and producing step | Engineering summary, units/plots/previews and limitations first; exact selected-run evidence travels to step and back; matching digest has no false mismatch | Retained run regression; real edited-source mismatch still detected; absent context has a distinct state |
| A13 | Upload/download | Upload enters chosen workspace without overwrite; download responds visibly and correct file arrives on Windows, with correct filename/type/bytes | Actual Windows file open/hash observation; denied, unsupported, oversized and interrupted cases; an acknowledgement alone is insufficient |
| A14 | Change/rerun | Edited input/process creates a new subject/run; affected old checks/reviews do not authorize it; old evidence unchanged; layout-only change does not invalidate engineering work | Actual full changed-input rerun, revision comparisons, source and output hashes, applicability checks |
| A15 | Cancel/disconnect/restart | Clear waiting/cancelled/failed/reconciliation states; pending requests and completed outputs survive; stale replies rejected; uncertain effects never replay | Controlled candidate service/transport loss before/after receipt; exact resumed identity; cancel acknowledgement not misrepresented as physical stop |
| A16 | Reopen/switch chat and tabs | Workspace/document/run selection remains correct; reopening reads rather than starts work; no cross-chat/workspace leakage or silent route switch | Actual host close/reopen/chat-switch observation; fixture tests separately; frozen configuration drift rejection |
| A17 | Understand the interface | No assistance needed to find next action, active view, result and return path; selected differs from disabled; narrow panel remains usable | Task-only recorded observation; screenshots at realistic widths/theme/zoom; record wrong turns, not just control existence |
| A18 | Generality/regression | Same owners handle Robot analysis and retained block results; Hermes editor/execution unchanged; OpenClaw stub and Pi unavailable behavior preserved | Appropriate existing owner tests and actual different-workflow proof; no weakened original requirements |

## Cross-cutting production checks

| ID | Qualification | Required outcome |
| --- | --- | --- |
| Q01 | Package independence | Wheel/sdist and selected plugin contain all necessary resources; installed operation works with source checkout inaccessible; no developer home paths, private flags or prototype imports |
| Q02 | Scope and security | Existing session/workspace grants apply to chat and app-only calls; unauthorized cross-workspace file reads, traversal, symlink/junction escape, changed-byte races and hostile MIME/content rejected; no privileged generic proxy |
| Q03 | Host content boundary | Restrictive CSP/image/download cases; inert untrusted HTML/Markdown, bounded uploads/media, isolated generated views; keep existing redaction and exact-output protections |
| Q04 | Configuration/evidence | Freeze observable routing/runtime/instructions/tool schemas; continuation rejects observable drift; unreported host model/build remains explicit; capture only Wright-observed boundaries |
| Q05 | Migration/update | Old drafts/source/history/results remain readable; migration rehearsal preserves original hashes; install/update/stop affect only owned candidate instance; no profile or credential takeover |
| Q06 | Windows local | Actual Windows packaged lifecycle and actual desktop UI/file checks, not WSL substitution; dependency/tool host requirements and versions recorded |
| Q07 | Windows desktop + GB10 | Actual remote UI and file delivery independent of drive mappings; current provider-supported personal sign-in; no SSH callback requirement |
| Q08 | Linux ARM64/x64 and Docker | Separate installed backend and packaged-resource checks for each advertised architecture/deployment; remote desktop attachment qualified separately; absent hosts explicitly not tested |
| Q09 | Compatibility and fallback | Pinned plugin/runtime/UI/client/kit/SDK versions; missing host capability or incompatible saved UI uses explicit supported fallback; native viewer choice is not inferred from an open receipt |
| Q10 | Repository/release | Required pre-push, merge gates and all current-head CI; full release runbook only when authorized; user acceptance and public availability reported independently |

## Engineering reference proof

Freeze the chosen existing handle assignment before execution. Preserve its
requirements and reference images. The intended strength extension requires an
explicitly reviewed analysis basis; no material or failure threshold invented to
get a pass. Actual CAD outputs must feed geometry checks and analysis; the actual
checked design must feed manufacturing preparation. Record exact producer and
consumer identities, numerical/physical applicability limitations, correction
budget and final package subjects. Stop at the declared human approval before
physical printing. A simulated submission can test the UI only when labeled.

Use fresh copies of Robot Tracking Diagnosis for applicable data-to-metrics-to-
report/review regression. Preserve original tolerances and datasets; do not call
this proof of the handle's manufacturing chain. Existing retained block runs
remain read-only regression subjects and must not be recreated or relabeled.

## Explicit exclusions and release decisions

- No physical operation, protected campaign or Roadster run in this qualification.
- No blanket claim that all engineering formats/providers/graph shapes work.
  Required missing semantics block the corresponding story; they are not removed.
- Confined AI process-UI authoring stays disabled until its actual capability
  requirement is met. Common view and compatible saved interfaces remain usable.
- No promise of reasoning while the host conversation is unavailable. Qualify
  durable waiting and explicit continuation; report autonomous-wakeup limits.
- Manual native viewer selection or a thread panel may be an approved supported
  route. Automatic selection remains its own separate evidence row.
- Actual model attestation, upstream internal prompts and host-wide native-tool
  enforcement cannot be claimed from Wright's gateway enforcement.

Required stories with FAIL/BLOCKED/NOT TESTED prevent a full-integration claim.
Optional exclusions need an explicit release-scope decision and visible product
behavior; do not relabel a requirement optional solely to finish overnight.

## Minimal native observation packet

Prepare a single known candidate and exact test workspace. Use available authorized
Windows automation first; verify it controls the actual app. If only the user can
observe, ask one short task at a time, collecting the same build's evidence:

1. Open the workspace and workflow; confirm the diagram and current document.
2. Open a retained result and download it; confirm the local file opens correctly.
3. Return to the same run, switch away/back, and confirm context survives.

These three checks cover remaining host-specific observations, not every test
above. They must not require running CAD again. A later task-only full journey
establishes usability separately; saved screenshots do not prove interactive
controls that were never exercised.
