# Shared host-adaptive UI prototype — review packet

Prefer one native Wright panel beside the host conversation, using the existing
shared editor and common working view. The neutral canvas stays shared across
hosts; controls/frames adapt through a small presentation profile and scoped
theme values. Wright/Hermes retains its own single chat and useful capabilities.
No new docking system, database, executor or speculative Claude/OpenClaw adapter.

The local prototype is reviewable; **the full goal is not complete**. The user
approved the named update and **0.4.0 is now installed on GB10**. Its exact package,
18 tools, resource, saved source and completed-run readback are verified through
the official MCP client. Actual Windows editor/working-view acceptance remains
open. Use [the short walkthrough](quick-walkthrough.md); no separate 0.3.0 test
is required. See [installation evidence](working-view-evidence/native-installation-0.4.0.json).

## Current evidence and capability matrix

| Capability | Current evidence | Status/limit |
| --- | --- | --- |
| Native side panel | User confirmed the 0.2.0 panel with Refresh status in Windows/GB10 | Supported on that observed arrangement; later editor acceptance unverified |
| Native panel protocol | Official MCP client and packaged simulated-host UI checks; 18-tool candidate/resource verified | Experimental candidate; browser evidence does not prove native Windows |
| Shared canvas/editor | Existing command/source/layout owners, neutral canvas, compact Add step/context inspector, Source/Side by side, CAS, Undo/Redo and served Workflows checks | Local supported behaviour; manual editing is separate from generated UI authoring |
| Chat supplies reasoning | This actual conversation supplied digital task replies/proposals; Wright queued/validated them and completed exact runs | Experimental manual continuation; SDK model worker not used; upstream model/build identity unreported |
| Inputs/checkpoint/results | Real owning APIs, one scripted exact-subject input, same durable run, verified saved bytes and reopen | Mechanism qualified locally; scripted test input is not actual user/engineering approval |
| Cancellation/failure | Terminal cancel, late-answer denial, lost acknowledgement retained across reload, explicit identical-request reconciliation | Locally qualified affected boundaries; no automatic uncertain retry |
| Restart | Exact interrupted receipt/request/runtime/artifacts retained; UI says reconciliation | Automatic reasoning restart unsupported; no replacement run or dead-consumer reply |
| Historical source changes | Native entry verifies the current accepted source against the requested digest and refuses stale context | Opening an old run after its source head changed is unavailable in this prototype; retained evidence is preserved. Existing Wright recorder/browser behaviour is not relabelled native |
| Gateway | Separate opt-in exact privately enrolled file read; no-grant403, one successful dispatch, immutable input | Experimental narrow profile; default 0.4.0 does not select it or grant broad tools |
| Review/external action | Existing Wright authority retained; no corresponding native write port | Unsupported in this candidate; UI/agent permission is not process approval |
| Binary/derived preview, upload/navigation | Explicit unavailable ports/read limits | Unsupported here; raw text reads <=1MiB qualified |
| Generated process UI | Existing no-executable-tools gate retained | Gated; manual trusted editor is supported separately |
| Native tabs/lifecycle/storage/zoom | No native editor/tool-permission/storage/close/zoom observation yet; document-control reported no connected sessions | Unverified; one panel, no fake tabs; save before close |
| Other platforms | Existing Hermes/pilot regressions and OpenClaw stub/Pi unavailable behaviour retained | No live Hermes acceptance or future Claude/OpenClaw adapter claimed |
| Original workflows | Fresh manufacturing-preparation and Robot Tracking Diagnosis copies preserve requirements/bindings/assets and display/reopen through Workflows | Provider readiness gates remain; digital fixtures do not qualify their engineering outputs |

Actual host: Linux ARM64 GB10, Python3.13.12, Node22.22.0, CLI/daemon0.159.2;
MCP Python1.28.1, JS SDK1.30.0, ext-apps1.7.5, existing uv/npm locks unchanged.
Model/auth/account usage and Windows app build are unreported; no provider-internal
prompt, memory, agent-management or usage receipt is invented. Windows-native,
Linux-x64 and Docker packaging are not qualified by these GB10 checks. The package
uses GB10 absolute paths; Windows is the renderer with that execution host.

Read [implementation-evidence.md](implementation-evidence.md) and the existing
[evidence index](working-view-evidence/evidence-index.json) for exact boundaries,
hashes, failed checks, repaired continuations and commands. The Windows walkthrough
is the next acceptance boundary, not another framework refactor.

## Windows walkthrough for installed 0.4.0

Use a fresh conversation on the existing GB10 host:

> Use the Wright plugin. Read connection status, then read saved workflow
> `workflows/desktop-checkpoint.workflow.wflow` in workspace
> `d8497ee5-0ef9-4cfe-8f0c-10c609ddab0b`, session
> `desktop-afee602f-a641-4173-a80b-e69e0aa99233`. Open its completed run
> `92db9047617c48ec91a85dec3a3a0a1b` with wright_process_view, using the exact
> returned storage digest and operation snapshot. This is digital UI test state.
> Do not start/restart/resume a run, call a model worker or open a browser URL.
> Report missing tools or scope/version failures explicitly.

Confirm actual panel rendering, results/read-file behaviour, host permission
prompts and current app build. Create a fresh copy for editing, open its editor,
make an innocuous name/layout edit, save, close/reopen and verify accepted state.
Keep the recorded source/run intact and never redirect it to a new revision. Resize, light/dark,
keyboard access, detailed editing and actual 200% host zoom should remain usable.
Save before close; do not assume unsaved or uncertain local state is restored.

For the full user journey, use a **fresh workspace/source** and the retained digital
checkpoint fixture. Create/open, edit/save, prepare/start once, use this conversation
for each queued task, and ask the user for the declared selection. Continue the
same durable run and inspect its files. Record that actual user input separately
from existing scripted tests. Agent tool prompts are not engineering reviews.

Measure first useful result, help/wrong turns, repeated context entry, current-state
clarity and 1–5 ease/confidence/pleasantness. Expert captures are not customer
research. No outreach or social publishing is authorized.

## Historical goal audit before the 0.4.0 installation

The audit re-read the full goal and inspected the current package/reports and
original-worktree preservation. All 22 inherited dirty files still match their
baseline hashes. Main a4a31c97, installed-source72c4f86f and shared-UI814a763d
remain clean; dirty prototype/pilot work is preserved. Package/runtime hashes
match, and live selection remains approved0.3.0. No repeated suite was necessary.

| Full requirement | Evidence now | Completion judgment |
| --- | --- | --- |
| Baseline, instructions, concepts, preservation | baseline.json, frozen files, design references, current worktree checks | Local established; existing data/configuration preserved |
| R0 six–eight journeys, separated claims, <=5 findings/<=3 experiments | research-findings.md, sources and formative script | Complete bounded pass; no fabricated interviews |
| Native panel/theme/resize/lifecycle/continuation investigation | User-confirmed0.2.0 rendering, protocol/browser reports, explicit gaps | Rendering observed; actual host theme/resize/lifecycle unproven |
| Workspace create/open; workflow create/view/edit/save | Actual native creation, packaged/served Workflows checks, source/layout receipts | Local mechanism proved; complete Windows editing journey unproven |
| Desktop reasoning, single chat, preserved pilot | Actual-native-conversation.json, checkpoint/gateway replies, shell/pilot regressions | Stated conversation/transport boundaries proved; combined native0.4.0 journey pending |
| Progress/results/evidence; declared input continuation | Same-run checkpoint, exact bytes/hashes, captures, scripted attribution | Mechanism proved; actual user response/Windows observation pending |
| Close/reopen accepted work, no replay | Source/layout reload, run readback, lost-ack reload, restart artifacts | Local proved; native storage/close/unsaved behaviour unproven |
| Neutral canvas, compact/focused authoring, Hermes shell | Shared code, served authoring reports, focus/source/inspector and preference checks | Implemented/local checked; host usability acceptance pending |
| Authority/configuration/evidence | Scope/stale/permission denial, frozen config, one gateway dispatch, late denial/no replay | Affected boundaries proved; unreported identities/unavailable capabilities explicit |
| Lifecycle/keyboard/sizes/actual zoom | Browser light/dark/size/authoring evidence, native script | Browser scope proved; actual Windows keyboard/zoom/lifecycle missing |
| Hermes/pilot and unavailable-platform regression | Backend/registry68, pilot24 mocks, shared frontend196, native/shared87 | Local regression; not live Hermes acceptance |
| Different original manufacturing and Robot workflows | Exact hashes, served reopen, five/three blocks | Shared authoring spans both; original provider gates prevent engineering execution |
| Ease/confidence/first result/clear next action | Research, expert fixes, wait/reconciliation UI, formative script | Expert evaluation; actual user measurements/feedback pending |
| Prototype/walkthrough/matrix/images/limits | This packet, evidence index, update/rollback, screenshots/captions | Local deliverables ready; no external publishing/integration/release |

The full goal is **not achieved**. The named 0.4.0 update was subsequently approved
and installed on 13 October; remaining acceptance depends on the actual
Windows/GB10 walkthrough. Local tests, scripted input, a browser fallback or
another report cannot prove those requirements. No further live-update approval
is currently needed. Further changes should follow a demonstrated gap.

## Integration and proposed PR description

Keep this isolated branch stacked on the preserved native-editor/shared-UI work.
Integrate the prior prototype base first or consolidate the stack deliberately
after reviewing its frozen baseline. Recheck current dev then; do not discard
dirty source worktrees or merge another session's gateway/catalog changes.
Changes here touch shared UI presentation/controller hooks and prototype ports/
tests/package/docs. Existing gateway/executor/validator ownership is reused.
No push, PR creation, merge or release is authorized; repository gates remain
required when integration is subsequently assigned.

Proposed title: **Prototype shared host-adaptive workflow editing and working views**

Proposed description: Wright's desktop-harness prototype now uses one shared
editor/working surface beside the host conversation, with neutral canvas controls,
source/layout conflict handling, exact process/run bindings and honest chat waits.
The existing Wright process client/runtime owns inputs, execution, permissions,
results and recovery; closing/reopening and uncertain acknowledgements do not
automatically repeat effects. The installed native plugin is experimental.

Validation: focused editor/common-client/backend/pilot regressions, served
Workflows entry, packaged resource/protocol checks, real digital same-run input/
result/cancellation/uncertainty/restart and narrow gateway evidence. Native Windows
editing/permissions/lifecycle/user walkthrough and unavailable engineering providers
are explicitly outstanding. No formal product/release or production readiness claim.

Best progress images: checkpoint-panel-scripted-input/native-test-choice-waiting-for-chat.png
and checkpoint-panel-completed/native-completed-owned-result-fixture.png under
working-view-evidence. Label **GB10 browser protocol prototype**. Suggested caption:
“One shared canvas, a clear pause for input, and the same run continuing with its evidence.”
