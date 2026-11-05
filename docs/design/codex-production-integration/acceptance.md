# Production integration acceptance matrix

**Status:** planned qualification, 4 November 2026.
Parent: [plan](../codex-production-integration-plan.md). Work: [tasks](tasks.md).

Historical proofs are regression inputs, not a blanket pass on a new candidate.
Use **PASS / FAIL / BLOCKED / NOT TESTED / OUT OF SCOPE**, with exact evidence.
Record source implementation, automated browser tests, installed runtime, native
desktop observations and human acceptance separately. Do not average them into
one success percentage. Every row below is currently **NOT TESTED for the future
production candidate**; baseline evidence is described in the parent plan.

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
