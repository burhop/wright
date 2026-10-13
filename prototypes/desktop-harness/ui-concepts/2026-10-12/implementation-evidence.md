# Host-adaptive UI prototype evidence

12 October 2026. Implementation in progress, **not completed native acceptance**.
Local branch `codex/host-adaptive-ui-prototype`; native-panel milestone commit
`f8cace61` and shared-UI commit `9fc6ce9a` follow preserved-baseline commit `2d1e6c02`. Source is the isolated feature
worktree, never the installed Wright command. Original worktrees, old targets,
configurations and runs are preserved. No push, merge, release or physical run.

## Versions and observed capabilities

| Subject | Exact tested version / environment | Evidence and limits |
| --- | --- | --- |
| GB10 host | Linux aarch64; Python 3.13.12; Node 22.22.0 | Actual local processes; Windows GUI is a separate subject |
| Dependency subject | Existing frozen uv/npm locks; Python MCP 1.28.1; JS MCP SDK 1.30.0; ext-apps 1.7.5 | Installed only in feature worktree; no lock/global upgrades. npm warned about jsdom's Node patch minimum; focused tests passed |
| Desktop host runtime | GB10 Codex CLI/daemon 0.159.2 | Existing runtime, not an independent model worker. Actual Windows app build still unreported |
| Wright native prototype | `wright-desktop-gb10-prototype` 0.2.0; same named MCP server | Approved installed update; only marketplace source changed. Old 0.1.1 package/private settings backed up. Original chat still reports initialize-handshake failure; the fresh user-tested chat is connected with 13 tools and one resource |
| Read-only MCP panel | MCP Apps resource, thread entry, protocol 2026-01-26 | Official documented pattern; actual SDK discovers 13 tools and reads scoped resource. Browser simulated-host checks pass. Fresh native call passed and the user reports the panel visible/working. Independent desktop capture, app build, theme/resize observations, tabs and lifecycle remain unverified |
| Shared editor | Same command/model/source/layout owners | Neutral canvas once across hosts, Add step toolbar, panel-sized bottom/right inspector. Actual browser Workflows authoring verified; no claim of native editing |
| Common working view | Existing process client, reviews/actions/recovery retained | Exact-run chat wait is read-only; closing aborts its status read, never cancels or replays a run. Mock component qualification, not an actual new-target desktop workflow completion |
| Hermes / prior chat pilot | Existing source/adapters retained | Focused regressions; no live Hermes or independent model substituted. Prior Codex-inside-Wright worktree untouched |
| OpenClaw / Pi / future Claude | Existing stub/unavailable contracts retained | No new adapter; future native surfaces unqualified |

Official UI sources: [extension entries](https://developers.openai.com/plugins/build/extensions),
[MCP UI metadata](https://developers.openai.com/plugins/build/chatgpt-ui),
[initialization/events](https://developers.openai.com/plugins/build/app-quickstart),
[UI guidance](https://developers.openai.com/plugins/concepts/ui-guidelines).
Documented ChatGPT examples do not attest every Codex Windows build. A UI message
capability does not prove background wakeup or automatic workflow continuation.

## Evidence index

| Evidence | Boundary |
| --- | --- |
| `baseline.json`; private `/tmp/wright-host-ui-baseline-20261012-01` | Original HEAD, 22 dirty files and exact inherited byte hashes; isolated commit 2d1e6c02 |
| [research-findings.md](research-findings.md) | R0 source research; vendor claims/customer report/hypotheses separated; no customer interviews or fabricated adoption metrics |
| [panel-protocol-evidence.json](panel-protocol-evidence.json), [panel.html](panel.html) | Real SDK calls/read resource and recorded scoped data; not native desktop |
| [panel-browser-evidence/report.json](panel-browser-evidence/report.json) | Six browser simulated-host checks; screenshots visibly labelled as fixture |
| [panel-candidate-evidence.json](panel-candidate-evidence.json), [native-install-evidence.json](native-install-evidence.json) | Prepared/installed package hashes and scoped configuration comparison |
| [native-panel-update.md](native-panel-update.md), [native-panel-user-observation.json](native-panel-user-observation.json) | Approved update; actual fresh native tool call and user-reported visible/working panel; specific UI checks still open |
| `/tmp/wright-host-ui-authoring-20261012-04` | 11 actual browser Workflows checks after toolbar/inspector change; source inventory includes added presentation modules/CSS |
| `/tmp/wright-host-ui-authoring-20261012-05` | 11 structural checks plus bottom inspector/light theme; visual review subsequently found clipped compact actions |
| `/tmp/wright-host-ui-authoring-20261012-06` | Intermediate wrapping repair; still visibly clipped. Superseded; do not use as proof of compact completion |
| `/tmp/wright-host-ui-authoring-20261012-07` / `08` | Action visibility and bottom/sheet checks passed; later refined field layout |
| `/tmp/wright-host-ui-authoring-20261012-09` | Retained failed run: captured a calculating layout digest prematurely; exact hash readiness assertion repaired |
| `/tmp/wright-host-ui-authoring-20261012-10` | All 11 final served Workflows checks passed, exact source/layout reload, full action visibility and visible bottom-inspector fields |
| [progress-images/README.md](progress-images/README.md) | Three exact actual-browser captures and honest social caption; no external posting |
| [original-example-ui-evidence/README.md](original-example-ui-evidence/README.md) | Fresh template/data/binding hashes; compiled Workflows entry, exact source/reopen and asset hashes; five/three declared graph blocks; no engineering/model/gateway/run call |

Raw browser subjects are working-tree snapshots, with served-module hashes;
they do not establish committed or native acceptance. Tokens are supplied via
private files/normal Unlock; token-bearing traces are omitted. Do not distribute
private configuration backups, auth files or raw daemon metadata.

## Focused validation

- Final focused frontend set: **196 passed in seven files**, including shared
  authoring, session preferences, common-view/recovery, exact handoff identity and
  observer cancellation. Earlier focused runs are retained below.
- 58 shared-editor component checks passed after Add step relocation.
- 124 common-view/process-tab/session checks passed after adding the exact-run
  reader; later shell-default changes have their own targeted session check.
- 49 workspace-session checks passed after the intended chat-default update;
  both saved collapse preferences are explicitly retained. The test now waits
  for the actual canonical route transition before collapsing that chat.
- 68 Python boundary/lease/desktop-execution/registry/Hermes/OpenClaw checks passed.
- 24 mocked adapter/transport regressions passed in the untouched prior chat
  pilot's existing environment. Its separate source/dirty notes were preserved.
- Production frontend TypeScript/build passed. The existing large-chunk warning
  remains; no unrelated splitting project added.
- Targeted Python Ruff and changed-component ESLint passed.
- Browser authoring covers input/document configuration, exact typed edges and
  rejection, drag/pan/zoom, Undo/Redo, Source containment, accepted save/layout
  reload and stale CAS conflict. Compact checks require fully visible actions,
  usable bottom inspector and both luminance themes.

## Failures retained and reconciled

Initial SDK fixture creation succeeded but the probe misread a legacy text
result as structured content. Its exact workspace was recovered read-only; it
was never created again. Failed harness invocations 01/02 are retained; the
explicit run-scope guard blocked before any run was started. A JSX edit failed
parsing, was repaired, then all editor tests passed. Old chat discovery remains
failed; it was not hidden behind SDK success or an unapproved desktop restart.

The first readiness-copy probe and Python test process stalled under the
restricted sandbox. Only their identified processes were stopped. The partial
copy was resumed using its existing template request identity; immutable source,
seed and scenario bytes were verified. The same checks completed outside the
sandbox with deadlines. This suggests a sandbox event-loop wakeup limitation;
its cause was not conclusively proven, and no storage/executor contract changed.

Visual review caught compact action clipping even while structural checks
passed. Full viewport visibility assertions were added rather than weakening
checks. Theme capture now waits for the activity-bar color transition to finish. A later
Save/reopen check captured `sha256:calculating` before hashing completed; the
harness now requires a real 64-hex layout digest before checking exact identity.
All 11 final checks passed. Original-example counter reports are retained and reconciled: broad test-id
counts were replaced by actual graph-block counts compared with accepted source
declarations. The temporary source-only server was stopped after the checks.
All 22 original inherited dirty files still match
their initial byte hashes; original checkout and pilot notes are preserved.

## Remaining work / next decisions

The fresh chat `Verify GB10 native panel rendering` successfully called the
native tool for the exact workspace. The user confirmed the native panel
appeared and subsequently said it seemed to work fine. This supports the next
prototype editing spike; it is not formal qualification of app build, resize,
theme, close/reopen or document hooks. See `native-panel-user-observation.json`.
Native scoped editing transport and outer-chrome rearrangement depend on that
result. Keep single-panel/browser fallbacks explicitly labelled; never draw
counterfeit native tabs. No automatic background chat wakeup is qualified.

Next demonstrate a fresh permitted digital run with **actual desktop conversation**
reasoning, gateway evidence and a declared checkpoint, using the same durable
run after returning to the view. No SDK worker or Hermes substitution. Native
UI authoring gates, uncertain-action reconciliation and frozen configuration
continue to apply. The original starter definitions now display/reopen byte-exactly through
Workflows in the compiled browser. Scenario input/binding bytes were preserved
but not applied to those starters; full original engineering assignments remain
unavailable until their providers qualify. No toy replacement is proof.

Actual desktop 200% zoom and an uncoached usability walkthrough remain open.
Browser width/height checks are not Windows zoom acceptance. Record first useful
result, extra steps, help requests and confidence without inventing measurements.

## Reproduce the shared browser slice

From `/tmp/wright-host-adaptive-ui-prototype`, use the locked local environment.
Owned API 8120 and Vite 5220 currently serve `/tmp/wright-host-ui-target-20261012-01`.
Do not start another service on those ports. The native walkthrough above uses
an existing scoped workspace; the authoring harness creates a separate blank
workflow via the ordinary Workflows control and never starts an engineering run.

```sh
node scripts/recovery/capture_image_redesign.mjs \
  --url='http://127.0.0.1:5220/workspace/aec8d7db-e77b-4c48-a8cb-f4b3b7e87ad9?host=openai-desktop' \
  --hosted-desktop=true --mode=desktop-authoring \
  --only=desktop-entry,desktop-text,desktop-document,desktop-connect,desktop-mismatch,desktop-drag,desktop-undo,desktop-save,desktop-invalid-source,desktop-cas,desktop-compact \
  --auth-token-file=/tmp/wright-host-ui-target-20261012-01/.preview-api-token \
  --evidence-root=/tmp/wright-host-ui-authoring-new --label=shared-ui
```

Choose a fresh evidence directory. Use `--key=value` syntax; `--only` is the
filter. Do not remove explicit run guards or expose the token in command text.
Use the native walkthrough for native qualification rather than this command.

## Proposed integration description (after remaining qualification)

**Title:** Prototype shared workflow controls and a scoped desktop workspace panel

Wright's workflow editor now uses one neutral graph palette and compact creation
controls across hosts, with inspectors that adapt to the actual panel. Its own
shell retains chat/session capabilities and saved layout preferences; the common
run view explains desktop reasoning waits without executing or retrying actions.

The experimental named desktop plugin adds one scoped read-only MCP App panel.
SDK and served-browser boundaries are qualified; actual Windows native rendering
and full native workflow continuation remain open and must not be implied by the
PR title or description. Existing workflow/provider/authoring gates are retained.
Validation and reproducible evidence are indexed above. No push is authorized.

## Native shared editor candidate, 12 October — not installed

User confirmation now explicitly identifies the actual read-only native Wright
panel with Refresh status. The next editor slice is isolated on
`codex/host-adaptive-native-editor`, based at `814a763d`, in
`/tmp/wright-host-adaptive-native-editor`. The working live 0.2.0 source is clean
and unchanged. API 8122 and fresh target `wright-native-editor-target-20261012-02`
serve candidate source state only; no engineering run started.

The existing editor/UI kit is bundled as one 1,325,752-byte HTML resource using
existing Vite/React and official MCP Apps SDK 1.7.5 (JS MCP SDK 1.30.0; Python MCP
1.28.1). No new dependency, executor, generic proxy, native tabs or second chat.
An opt-in open tool and narrow UI save adapter reuse Wright's source/layout CAS;
source conflicts and known denials stay distinct from unknown outcomes. Reads
never silently rebase a retained draft. Bundle/helper/runtime hashes and the
native-editor flag are frozen and checked on connection. Run and generated UI
capabilities gain no authority from this UI.

41 focused Python checks, 7 source-client checks, TypeScript, targeted ESLint and
Ruff pass. Five browser fixture checks pass using the packaged resource and real
isolated Wright storage. Official MCP source save/stale/scope/reconnect checks
passed after read-only reconciliation of a result-decoding assertion. Preserved
failed reports and final captures are in [native-editor-evidence](native-editor-evidence/candidate.json).
The first sandbox attempt stalled before MCP operations; only owned processes
were stopped. Two browser selector failures were repaired without changing the
editor. The receipt comparison accepts Wright-assigned layout revisions while
checking the requested positions/viewport and source.

Native editor rendering/save/host permission behavior remains **unverified**;
native read-only rendering is **user confirmed**. Theme/narrow/reload above are
**locally verified in a simulated browser host**, not Windows acceptance. Saved
source restoration is verified; unsaved close restoration and native tabs are
unverified. Single-panel fallback is explicit. No automatic chat wakeup claim.

Prepared exact [0.3.0 update and rollback](native-editor-update.md) and
[actual desktop walkthrough](native-editor-walkthrough.md). Specific approval is
required by the submitted goal before this live change adds a write tool and
selects the new source state. Old target/workspaces/runs and other settings remain.
Suggested caption for the labelled browser image: “Wright’s shared workflow
canvas now edits, saves and restores in our GB10 panel test. Windows desktop
editor testing is next.” Do not present it as an actual Windows capture.

Final packaging also rejects external emitted assets/module imports. The resource
was retrieved with its exact new hash through the official MCP client (15 tools),
and the five affected browser checks passed again on that final bundle. The
working 0.2.0 and candidate targets both have zero reasoning requests/responses;
no pending desktop reasoning is redirected by the prepared update.

The final bridge also rejects an installed Python MCP SDK version that differs
from its frozen manifest. The 14 affected bridge checks pass after that guard
(including the additional drift case); the final official MCP resource read
passes with SDK 1.28.1. This original desktop conversation now exposes the live
0.2.0 Wright tools: its actual `wright_connection_status` returned connected,
with model/app identity still unreported. No candidate write tool was enabled.

The first editor milestone commit (`5a207b7e`) retained four whitespace-only
lines inside generated Zod function strings, and its staged whitespace check
reported them. Packaging now removes those generated blank-line spaces rather
than disabling the gate. The resource's final hash is
`ad4223e1c8e6d7039574c975925f33f327ca5c5dc92546c729142c92402d581e`;
the read-only MCP resource check and all five affected browser checks pass on
these final bytes. Prior resource manifests/captures remain preserved.

Proposed PR title: **Prototype Wright's shared canvas and native desktop editor**.
Description: Wright previously exposed a read-only desktop panel and a separate
browser editor. This experimental candidate places the existing shared editor
in one MCP App panel, with exact source/layout saves through Wright's existing
revision checks, while adapting surrounding controls for Wright and desktop
hosts. No second chat, workflow executor or generic proxy is added. Native
read-only rendering is user-confirmed; editor save/reopen, theme and conflicts
are locally qualified in a simulated host against real isolated storage. Actual
Windows editor acceptance remains pending the scoped 0.3.0 installation.
Validation: 41-check backend batch; 14 affected bridge checks after the SDK guard;
7 source-client checks; TypeScript/targeted ESLint/Ruff; final five-check packaged
editor walkthrough; earlier served Workflows and existing-platform regression
evidence retains its stated scope. No push, merge or release performed.

## Offline working view and actual desktop-conversation run

Next-slice work is isolated in `/tmp/wright-host-adaptive-native-working-view`,
branch `codex/host-adaptive-native-working-view`, based at `72c4f86f`. The prepared
0.3.0 candidate/worktree stays clean and unchanged. The user subsequently approved
and installed that exact candidate; see native-editor-evidence/native-installation-0.3.0.json.
No new process tool or working-view resource is registered in the installed candidate.

The common working view and existing public ProcessClient are reused. Two
closed MCP ports separate reads from user-requested inputs/readiness/start/
declared-response/cancellation. API request models are inherited, not another
execution/validation implementation. No arbitrary URL/method, model call,
executor, database or gateway changes. URI subjects are validated and encoded;
scalar declared inputs work; automatic response attribution and review fields
are rejected. Known denial remains distinct from uncertain effects, with stable
request identities and no automatic write retry. Snapshot polling is explicitly
separate from SSE/LLM streaming; event cursors are unavailable instead of ignored.

Text representations up to 1 MiB reuse the existing owning reader, exact run/
artifact references, nosniff/size/hash headers and actual byte hashing. Other
media and derived previews remain explicit unavailable capabilities. Native
review/external-action/navigation/upload ports are not exposed; no fake provider
fallback. Generated process-UI authoring remains gated. The component/transport
code is offline, **not a native working-view completion claim**.

15 new Python boundary checks and 14 native client/component checks pass, plus
TypeScript, targeted ESLint and Ruff. The 83-check combined common/status run
included 72 existing checks and the then-11 native checks; the new file-reading
cases and component were rechecked in the final 14-check batch. 78 existing
public ProcessClient checks also passed. An initial DOM hook run used the wrong
Node test environment; rerunning with the existing web config passed. The
synthetic declared-input component proof is labelled synthetic and does not
claim an actual human checkpoint was answered.

Separately, the **actual installed 0.2.0 native tools in this desktop conversation**
created a fresh workspace, accepted a versioned text-only workflow, prepared
inputs, started one durable run, queued its bounded task and accepted this
conversation's Markdown reply. Wright completed the same run and saved its
1098-byte inspection brief. No SDK model worker, engineering tool, physical
measurement/action or manufacturing release was involved. The source retains
`reviewed_ai_suggestions: false`; no engineering approval is invented. Model and
app identity remain unreported; task tools were empty but global native-tool
isolation remains unverified.

The owning representation API returned bytes matching the recorded SHA-256.
The existing served browser capture harness entered through **Workflows**, opened
the same completed run, displayed its actual saved file, reloaded and closed its
common view. These are browser captures, **not Windows/native editor captures**.
The old installed target now has one request/response/terminal receipt and zero
pending tasks; earlier zero-count records remain historical evidence. No other
workspace, run or configuration was removed or redirected.

[Evidence index, source, task/receipt/snapshot, verified artifact and captures](working-view-evidence/evidence-index.json).
The real checkpoint/gateway/native-panel journey remains a later qualification;
the original manufacturing/Robot workflows' provider gates remain unchanged.

Expert UX observation: the current browser working view spends much of its first
viewport on progress metadata and a disabled cancellation control. In the native
composition, prioritize the result or pending response and compact the surrounding
status disclosure. This is an expert observation, not customer research, and
requires no new docking or design system.

Social caption: “From desktop conversation to a saved Wright workflow result.
This text-only prototype proof shows the GB10 browser working view; native editor
testing is next.” Suggested image: `working-view-evidence/browser-native-run-2/03b-owned-inspection-brief.png`.

### Packaged editor/common-view composition, local only

The next candidate now composes the preserved editor and common controller in
one real MCP App resource. Save, then use **Run and results**; **Open workflow**
returns to the still-mounted editor with its Undo state. Unsaved inputs, busy or
uncertain mutations block switching. A changed accepted source blocks preparation;
an explicitly saved revision creates a new process binding rather than redirecting
an old run. There is no second chat, fake tab strip or executor. Host theme/font
values apply to both frames; native working controls reuse the neutral palette.

An explicit `--native-working-view` capability requires `--native-editor`, freezes
the tool-file/resource hashes, and exposes one read-only primary-document opener
plus two closed UI ports. The installed 0.3.0 tree/package remain untouched. New
qualification state is `/tmp/wright-native-working-target-20261012-01` on API8123,
Vite5223. No workflow was started there. Official MCP reads verified 18 tools,
the exact immutable resource, wrong-workspace rejection and source-drift rejection.
The current resource is about 2.18 MB with no external assets; binary/derived
representation support remains explicitly unavailable.

87 focused frontend checks and 59 backend/transport checks passed; the final
bridge guard was rechecked in its 16-check subset. TypeScript, targeted ESLint,
Ruff and `git diff --check` passed. Eight final packaged-panel browser checks exercised
real source storage, Source/apply/save/layout/reload, neutral theme/narrow controls,
common input preparation, dirty-input protection, return/reopen without replay,
and retained stale drafts. The primary opener accepts a real preparation context
with `run_id: null`; after an edit, a cached old digest is rejected and an explicit
new-revision context reopens. Actual Undo/Redo after returning from the working
view was also exercised. Its first stale continuation failure is retained; the
scope guard was preserved. The fixture forwards preparation only, never runs,
reviews or external actions. A separate sequential served-build capture entered
through **Workflows**, read the exact saved process in the common view and closed
its actual workspace tab. These are GB10 browser checks, not Windows acceptance.

Failures are retained in the existing evidence index: a backend command omitted
the repository PYTHONPATH, the first served Vite launch omitted the existing
editor opt-in flags, and bundled shader whitespace failed the Git whitespace
gate. The commands/build were corrected and affected checks passed; no gate or
authority contract was weakened.

Reproduce on the retained isolated service/state:

```sh
.venv/bin/python prototypes/desktop-harness/native_editor_probe.py --state-dir /tmp/wright-native-working-target-20261012-01 --phase resource --native-working-view
node prototypes/desktop-harness/native_editor_acceptance.mjs /tmp/wright-native-working-target-20261012-01 --working --open-working
node prototypes/desktop-harness/capture-preview.mjs /tmp/wright-native-working-target-20261012-01 /tmp/wright-working-readback-new preparation
```

The browser acceptance command deliberately changes only this isolated test
source/inputs. Run it sequentially before the read-only served capture. Vite needs
`VITE_WRIGHT_WORKFLOW_RECOVERY=true VITE_WRIGHT_WORKFLOW_COMPOSER=true` and its
API proxy target `http://127.0.0.1:8123`. The evidence index records current hashes,
versions, reports, screenshots and remaining gaps. Actual Windows edit/save/reopen
and the complete native run/checkpoint/recovery journey remain unproven. The next
working-view live update will need separate specific approval after qualification.

Suggested caption: “One canvas for authoring, one working view for preparing the
job. Wright’s neutral controls now fit the desktop-harness prototype.” Image:
`working-view-evidence/browser-working-primary-final/native-working-preparation-fixture.png`.
Label it **GB10 browser protocol prototype**, not a Windows desktop screenshot.
