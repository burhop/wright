# Named 0.9.0 update and rollback

Applied and installed-package verified; Windows acceptance pending. The saved demo-readiness goal authorizes only the
named prototype update after concrete qualification and backup. No new approval
is required within that scope. Do not restart the desktop.

Candidate: `/tmp/wright-desktop-continuation-candidate`.
Marketplace: `prototypes/desktop-harness/native-home-09-candidate`.
Runtime: loopback API 8156, fresh private state
`/tmp/wright-desktop-local-review-state-20261015-01`.

Changes: workspace-preserving Refresh, same-run explicit Continue and separately
qualified local reviews. Exact manual empty-tool enrollment remains necessary;
no new automatic grants, general MCP execution or image-input support.
See local-review-candidate-final-evidence.json and local-review-runtime-evidence.json.
Actual Windows native acceptance is still pending.

Before applying, verify current CLI syntax, freeze package hashes and privately
back up current configuration plus every cached version of this named plugin.
Record semantic configuration before/after; allow only its marketplace source
and selected version to change. Preserve all old cache bytes and services.
Do not blindly restore a full configuration file during rollback.

Apply after that backup:

```sh
codex plugin marketplace remove wright-desktop-gb10-prototype --json
codex plugin marketplace add /tmp/wright-desktop-continuation-candidate/prototypes/desktop-harness/native-home-09-candidate --json
codex plugin add wright-desktop-gb10-prototype@wright-desktop-gb10-prototype --json
```

Scoped rollback to preserved 0.8.0:

```sh
codex plugin marketplace remove wright-desktop-gb10-prototype --json
codex plugin marketplace add /tmp/wright-desktop-ui-files-candidate/prototypes/desktop-harness/native-home-08-candidate --json
codex plugin add wright-desktop-gb10-prototype@wright-desktop-gb10-prototype --json
```

After applying, verify actual installed package bytes, version, 32-tool protocol
and exact resource digest. Verify older named caches are retained byte-for-byte.
Retain all new test state even on rollback. A fresh conversation may be needed to
observe new plugin tools; old chats and user evidence must remain intact.

Installation evidence: installed-09-evidence.json. Private backup and command
receipts: `/tmp/wright-desktop-plugin-update-20261015-01`. All 15 prior cache files
were restored byte-for-byte after CLI eviction. No unrelated configuration changed.
