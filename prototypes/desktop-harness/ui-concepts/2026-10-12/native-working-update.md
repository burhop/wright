# Named 0.4.0 working-view update — approved and installed

The user approved the named update on 13 October 2026. Version 0.4.0 is now
selected on GB10; actual Windows acceptance remains pending. See
[quick-walkthrough.md](quick-walkthrough.md) and
[installation evidence](working-view-evidence/native-installation-0.4.0.json).

The candidate adds run/results to the already-approved shared manual editor.
Use the OpenAI desktop conversation as the only chat. Wright owns accepted source,
durable runs, validation, permitted actions, evidence and recovery.

## Exact selection and preserved state

Same marketplace/plugin `wright-desktop-gb10-prototype`, server
`wright-desktop-gb10`, version **0.4.0**. Source worktree:
`/tmp/wright-host-adaptive-native-working-view`. Prepared marketplace:
`/tmp/wright-host-adaptive-native-working-view/prototypes/desktop-harness/native-working-candidate`.
It selects `/tmp/wright-native-working-target-20261012-01`, API8123, with native
editor/working-view flags. The exact package was read-only qualified through the
official MCP client: 18 tools and the immutable 2,184,542-byte resource
`ui://wright/workflow/ed299bbd410908eb61e63d6314b97a616f8601a714b720a46aeca427b958ba60.html`.
See working-view-evidence/candidate-0.4.0.json and candidate-protocol-0.4.0.json.

Adds a read-only primary opener `wright_process_view` and two closed UI-only
ports: snapshot/handoff/text reads, and inputs/readiness/start/declared-input/
cancellation. UI visibility is metadata, never permission. All existing tools
remain. Review decisions, external actions, uploads/navigation, binary/derived
previews and generated process-UI authoring remain unavailable. The default
candidate does not enable the separate confined-file gateway profile.

Installed 0.3.0, its clean source `72c4f86f`, API8122, package and state remain
preserved. Old workspaces/runs are not transferred or redirected. A new selected
connection cannot access their IDs; use the preserved connection or scoped rollback.
No other setting, authentication/model choice, desktop restart or all-chat reload.

## Qualification and limits

Editor/common-client regressions, real source CAS/conflicts, primary source-drift
rejection, retained Undo/Redo, digital same-run checkpoint, exact output bytes,
duplicate-start receipt, cancellation/late-answer denial, lost-ack manual
reconciliation and abrupt-restart/no-replay observation passed locally. Tests and
captures are explicitly GB10 protocol/browser evidence. A scripted input is not
user or engineering approval. Automatic reasoning restart and background chat
wakeup are unsupported. The interrupted test run remains safely retained.

Actual Windows rendering/save/reopen, tool permission prompts, storage/close
behaviour, theme/resize/zoom and usability remain pending. Save before closing.
The previously user-confirmed 0.2.0 read-only panel does not prove those behaviours.
Native historical-run opening after changing the source head is unavailable:
stale digests are rejected, and retained evidence stays intact. Edit fresh copies
for the user walkthrough. Existing browser/recorder behaviour is not claimed native.

## Commands used for the approved named update

The following was the approved procedure, not a request to run it again.
Privately back up the selected 0.3.0 package and current config; check its exact
target for pending/live work and preserve that work. Verify package/runtime hashes.
The tested CLI0.159.2 requires scoped marketplace replacement:

```sh
codex plugin marketplace remove wright-desktop-gb10-prototype --json
codex plugin marketplace add /tmp/wright-host-adaptive-native-working-view/prototypes/desktop-harness/native-working-candidate --json
codex plugin add wright-desktop-gb10-prototype@wright-desktop-gb10-prototype --json
```

Compare semantic configuration before/after: only this named marketplace source
may change; the same plugin remains enabled. Verify installed package version,
files, tools and resource. Use a fresh GB10-hosted chat when old inventory persists.
Do not reload all chats or restart the desktop. These are GB10 execution-host
paths; they are not Windows-native installation commands.

## Scoped rollback

```sh
codex plugin marketplace remove wright-desktop-gb10-prototype --json
codex plugin marketplace add /tmp/wright-host-adaptive-native-editor/prototypes/desktop-harness/native-editor-candidate --json
codex plugin add wright-desktop-gb10-prototype@wright-desktop-gb10-prototype --json
```

Restore only the named selection/package if its source is unavailable, never the
whole old configuration. Keep all newly saved source, runs, answers and evidence.
Follow [quick-walkthrough.md](quick-walkthrough.md) for Windows acceptance;
do not manufacture native acceptance from passing local checks.
