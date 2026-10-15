# Named experimental 0.6.0 desktop home update

Authorized by the submitted demo-readiness goal. Prepared candidate:
`/tmp/wright-desktop-engineering-demos/prototypes/desktop-harness/native-home-candidate`.
It selects only the named `wright-desktop-gb10-prototype`, API8133 with isolated
`/tmp/wright-desktop-combined-proof-20261014-01` state. Existing source/runs are not
migrated or rebound. This candidate adds home/workspace discovery, Connections,
saved setup recovery, explicit operator setup/validation/enable controls. Native
Windows acceptance and remote OAuth callback routing remain unverified. Do not
start SteveCAD authentication until its callback route is qualified.

Qualification: combined actual-MCP browser walkthrough and package protocol receipt
in the selected state directory. Exact package reports 29 tools; editor resource
SHA-256 `2379eea9dc1d828e96eefcfa616ae05bd1531b73a9484aca536b203901934be2`,
2,202,836 bytes. Current tested CLI: 0.159.2. Official plugin packaging guidance:
https://developers.openai.com/plugins/build/plugins

Before update, privately back up config and both existing named cache versions;
check old target for pending work. Keep old services, workspaces and cached bytes.
Apply only this selection using the installed CLI's tested commands:

```sh
codex plugin marketplace remove wright-desktop-gb10-prototype --json
codex plugin marketplace add /tmp/wright-desktop-engineering-demos/prototypes/desktop-harness/native-home-candidate --json
codex plugin add wright-desktop-gb10-prototype@wright-desktop-gb10-prototype --json
```

Verify semantic config differs only in the named marketplace source. Restore any
old cache directories evicted by the CLI byte-exactly, without changing the new
selection. Verify selected package files, MCP tools and resource again. Do not
restart the desktop or reload unrelated chats. Use a fresh GB10-hosted conversation
if the current chat retains old tools. Keep the served runtime unchanged while
this candidate is selected; subsequent runtime edits require a qualified new
candidate/service or deliberate reconciliation, not silent continuation.

Scoped rollback:

```sh
codex plugin marketplace remove wright-desktop-gb10-prototype --json
codex plugin marketplace add /tmp/wright-host-adaptive-native-working-view/prototypes/desktop-harness/native-working-candidate --json
codex plugin add wright-desktop-gb10-prototype@wright-desktop-gb10-prototype --json
```

Never restore the entire old configuration or delete new state/evidence. Preserve
old cache versions even when rolling back. Installation status and exact private
backup/verification receipt are recorded separately after the operation.
