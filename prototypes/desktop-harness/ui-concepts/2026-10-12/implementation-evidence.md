# Host-adaptive UI prototype evidence

12 October 2026. Implementation in progress, **not completed native acceptance**.
Local branch `codex/host-adaptive-ui-prototype`; native-panel milestone commit
`f8cace61` follows preserved-baseline commit `2d1e6c02`. Source is the isolated feature
worktree, never the installed Wright command. Original worktrees, old targets,
configurations and runs are preserved. No push, merge, release or physical run.

## Versions and observed capabilities

| Subject | Exact tested version / environment | Evidence and limits |
| --- | --- | --- |
| GB10 host | Linux aarch64; Python 3.13.12; Node 22.22.0 | Actual local processes; Windows GUI is a separate subject |
| Dependency subject | Existing frozen uv/npm locks; Python MCP 1.28.1; JS MCP SDK 1.30.0; ext-apps 1.7.5 | Installed only in feature worktree; no lock/global upgrades. npm warned about jsdom's Node patch minimum; focused tests passed |
| Desktop host runtime | GB10 Codex CLI/daemon 0.159.2 | Existing runtime, not an independent model worker. Actual Windows app build still unreported |
| Wright native prototype | `wright-desktop-gb10-prototype` 0.2.0; same named MCP server | Approved installed update; only marketplace source changed. Old 0.1.1 package/private settings backed up. Existing chat still reports initialize-handshake failure, zero tools/resources |
| Read-only MCP panel | MCP Apps resource, thread entry, protocol 2026-01-26 | Official documented pattern; actual SDK discovers 13 tools and reads scoped resource. Browser simulated-host checks pass. Actual Windows rendering, tabs, lifecycle and native context remain unverified |
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
| [native-panel-update.md](native-panel-update.md), [native-panel-walkthrough.md](native-panel-walkthrough.md) | User-approved exact update and rollback; pending native walkthrough |
| `/tmp/wright-host-ui-authoring-20261012-04` | 11 actual browser Workflows checks after toolbar/inspector change; source inventory includes added presentation modules/CSS |
| `/tmp/wright-host-ui-authoring-20261012-05` | 11 structural checks plus bottom inspector/light theme; visual review subsequently found clipped compact actions |
| `/tmp/wright-host-ui-authoring-20261012-06` | Intermediate wrapping repair; still visibly clipped. Superseded; do not use as proof of compact completion |
| `/tmp/wright-host-ui-authoring-20261012-07` / `08` | Action visibility and bottom/sheet checks passed; later refined field layout |
| `/tmp/wright-host-ui-authoring-20261012-09` | Retained failed run: captured a calculating layout digest prematurely; exact hash readiness assertion repaired |
| `/tmp/wright-host-ui-authoring-20261012-10` | All 11 final served Workflows checks passed, exact source/layout reload, full action visibility and visible bottom-inspector fields |
| [progress-images/README.md](progress-images/README.md) | Three exact actual-browser captures and honest social caption; no external posting |
| `/tmp/wright-host-ui-original-examples-20261012-01/existing-examples.json` | Fresh original manufacturing-preparation and Robot Tracking Diagnosis template/data/binding hashes; readiness only, no run |

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
All 11 final checks passed. All 22 original inherited dirty files still match
their initial byte hashes; original checkout and pilot notes are preserved.

## Remaining work / next decisions

Native walkthrough first: actual Windows build, rendering, resize, theme,
close/reopen and available document hooks. The user is testing a fresh GB10 chat.
Native scoped editing transport and outer-chrome rearrangement depend on that
result. Keep single-panel/browser fallbacks explicitly labelled; never draw
counterfeit native tabs. No automatic background chat wakeup is qualified.

Next demonstrate a fresh permitted digital run with **actual desktop conversation**
reasoning, gateway evidence and a declared checkpoint, using the same durable
run after returning to the view. No SDK worker or Hermes substitution. Native
UI authoring gates, uncertain-action reconciliation and frozen configuration
continue to apply. Original engineering examples remain unavailable for full
execution until their original providers qualify; no toy replacement is proof.

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
