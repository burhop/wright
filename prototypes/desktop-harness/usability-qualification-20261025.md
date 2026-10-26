# Desktop usability prototype qualification — 25 October 2026

The named experimental plugin is updated to **0.22.0**, using UI source
`78b4c3516f29134cc6c359357c8451131b7b69c2` and native resource SHA-256
`92b06b02333cc006192b99d9f6b9b06fcab48b69d3a519f4c5cd2601a1744b60`.
The existing Python backend, frozen reasoning binding, tool authority and live
workspace configuration are unchanged. This is not a product release or human
acceptance, and no engineering process was executed.

## User-visible corrections

- Workspace return explicitly says **Workspace home**, and the editor tab says
  **Edit workflow**. The editor explains whether a run is selected; results
  remain attached to the exact selected run.
- Home displays accepted job purpose with its saved title and searches purpose,
  title and normalized filename. Exact paths remain in details.
- Saved names/purposes appear together after reading, with an explicit loading
  state. A pending read no longer produces a temporary name or false empty
  search. Failed metadata reads explicitly explain the filename fallback.
- Connections uses compact cards while keeping saved status, authentication
  limits, current readiness and compatibility visible. Missing setup has a
  distinct next action. Connection availability still grants no process approval.
- Results use the host font. The shared canvas, full Source, instructions,
  Undo/Redo, source/layout persistence, inspectors and common view remain.
- PR171's selected-run evidence, title/search, preview focus/scroll and
  completed-setup corrections are included in the installed resource.

## Qualification boundaries

| Check | Result | Scope |
| --- | --- | --- |
| Create/name/edit/Undo/Redo/save/search/reopen | PASS | Actual MCP/storage; disposable source |
| Export/import; text upload/preview; PNG download | PASS | Disposable writes; downloaded retained image hash matches |
| Existing PNG → producing step → same run | PASS | Recorded run 681a949b7b2e463dabc2d5ac97ce7651; visible Results 1/1; no false mismatch |
| Real mismatch, missing context and Undo | PASS | Existing Robot Tracking Diagnosis observer regression; no engineering execution |
| Delayed metadata/search; normal/narrow and 150% pixel density | PASS | Controlled latency; actual browser rendering on Linux ARM64 |
| Installed command/resource and tool contracts | PASS | 56 unchanged input/output/annotation/metadata contracts; resource read matches built bytes |
| Frontend regression | PASS | 2,045 tests in 224 files, final patched dependencies, one worker |
| Bridge regression | PASS | 311 controlled checks; unchanged Python source/runtime |
| Type/lint/format and Node security policy | PASS | Zero high/critical findings; seven moderate findings remain |
| Existing work/configuration preservation | PASS | 164 pre-existing workspace files and original credentials/binding/version/token/preview files unchanged |
| Windows-local browser/MCP qualification | UNVERIFIED | Self-contained source patches and runner handed to busy independent Windows pilot |
| Actual Windows native panel, download/open and chat restoration | UNVERIFIED | Requires directly observed supported-host evidence |
| Human usability acceptance | NOT ASSESSED | Agent task walkthrough and regression proof are not a user study |

Browser screenshots use a simulated desktop host with actual Wright owners.
Pixel density is not actual Windows display scaling or browser zoom. The
existing [Windows runner and boundary guidance](windows-usability-qualification.md)
must preserve those distinctions. Current OpenAI Computer Use guidance excludes
automating the OpenAI application itself; no alternate-tool or private-debugging
bypass was attempted.

The initial sandboxed bridge attempt stalled and was retained; the bounded
local-network rerun passed. One full frontend attempt passed assertions but
failed Vitest RPC teardown in an unchanged chat test; its isolated check and
subsequent full serial runs passed. Neither attempt was silently classified green.

## Dependency gate and provenance

The pre-existing lockfile failed current high-severity advisories for
[body-parser](https://github.com/advisories/GHSA-27r3-jxmh-p828),
[undici](https://github.com/advisories/GHSA-xjj6-f33q-929c) and
[Zod](https://github.com/advisories/GHSA-mrhx-c7xc-m3w5).
The isolated candidate now pins body-parser 2.4.0, undici 8.12.3 and Zod 4.6.6,
with compatible content-type/qs updates. No audit exception or policy change was
introduced. CLI and Python backend installations were not upgraded.

Tested client/runtime: Node 26.0.0, Python 3.13.12, Python MCP 1.30.0,
JavaScript MCP 1.32.1 and MCP Apps 1.7.5. MCP resource protocol and the simulated
UI handshake are recorded independently in the receipts.

A changed UI correctly failed the old frozen resource pin. Qualification uses a
new private client configuration with the same binding/API and only the new
presentation hash; the original backend configuration and guard remain intact.
The CLI omitting an empty marketplace table caused one initial settings-check
failure; exact hash reconciliation confirmed that no unrelated setting changed.
Both failed probes and successful continuations are retained.

## Remaining work and evidence

Managed instruction folding is deferred: Source is a plain textarea and remains
fully inspectable/editable/portable. Native host behavior and human acceptance
stay open. Generated process-UI authoring remains gated by its existing no-tools
requirement; this presentation work grants no additional agent capabilities.
Existing container-publication metadata findings are outside this
UI task and remain unchanged.

Private local evidence is indexed in `.local-run/usability-20261025/EVIDENCE.md`,
with the task-based `BACKLOG.md`, combined `QUALIFICATION.json`, before/after
screenshots, original failures, preservation receipts, installed resource
verification and unpublished social-image options. No source or evidence was
pushed or published. Local checks do not replace the normal push/merge gates
before any future integration authorization.

Official host sources: [Computer Use](https://learn.chatgpt.com/docs/computer-use)
and [plugin UI bridge](https://developers.openai.com/plugins/build/chatgpt-ui).

## 26 October: compact workspace lists

The user's long-list complaint reproduces at 480×820: the existing workflow list
is 1,554px tall. The focused follow-up bounds file/workflow lists to 360px or
45% of the viewport, makes file entries compact rows, and moves upload controls
and preview limits into explicit disclosures. Search and exact file/source owners
remain unchanged; the full file path remains in the preview's location details.
This improves the current navigator while the user's native document-tab
direction is being qualified. It is not a replacement navigation design or a
claim that the host can render engineering formats.

The existing actual-MCP browser harness now checks list height, overflow,
keyboard access to the last entry, filtering, horizontal fit, and unchanged
accepted source/history. All 39 visible files in the retained demo are available;
the initial workflow height falls to 360px. The disposable upload/preview/exact
PNG download journey and 33 focused regressions also pass. TypeScript, focused
lint and whitespace checks pass. The built HTML SHA256 is
`05584072f3f329d3d621da996125184d156c0a9e3995d879f333801f189dcf1f`.

Evidence and before/after screenshots:
`.local-run/native-document-tabs-20261026/list-density/`. The initial stale-pin
connection rejection is preserved separately from the successful new private
test configuration. No frozen installed or historical configuration was edited.
This follow-up is not installed and has not yet been qualified on Windows or in
the native desktop. The installed 0.24 native file-handler test remains stable.

## 26 October: Connections disclosures and bounded catalog

The narrow SteveCAD entry was still 456px tall. Keep provider activity, workspace
access, authentication uncertainty and current readiness visible; move the full
description, validation evidence and explanation into Readiness details. Shared
lifecycle/availability controls stay behind Manage connection. Saved setup and
Review setup remain directly accessible with shorter visible labels and exact
provider names for assistive technology. The catalog itself scrolls in a bounded
area, including keyboard access to its last entry.

The same actual-owner read-only journey now measures a 260px entry at 480×820,
retains expired-validation/uncertain-compatibility warnings, opens management
without invoking an action, and reads the existing completed setup without
asking to reconnect or approve it. Forty focused connection/control/custom-setup
checks pass, including uncertain disable reconciliation and exact subjects.
The initial padding and ambiguous-locator failures are retained alongside the
baseline under `.local-run/native-document-tabs-20261026/connection-density/`.
TypeScript, focused lint and resource packaging pass. Compiled UI SHA256:
`2e4c5f7c48e0ccd44032a8173f9f86c1cca4bad5ad25416f96d899020af17553`.
This batch remains local/uninstalled; Windows and native checks are separate.

The independent Windows list check subsequently found a 364px list at normal
size: padding was outside its 360px limit. Linux reproduces the same failure
when the journey measures normal size as well as narrow. The list now uses
border-box sizing; the acceptance phase measures both sizes explicitly. This
does not relax the 360px bound or change file/keyboard/navigation contracts.
