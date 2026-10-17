# Named 0.15.0 update — prepared, not applied

Only `wright-desktop-gb10-prototype` changes. The submitted goal already authorizes
this tested named update, private backup and scoped rollback; no further routine
approval is needed. No desktop restart, unrelated settings or production change.

## Concrete candidate and evidence

- Marketplace: `/tmp/wright-desktop-completion-015-marketplace-20261017`.
- Frozen runtime: `/tmp/wright-desktop-completion-2d4f589e-runtime-20261017`.
- Python: `/tmp/wright-desktop-completion-015-env-20261017/bin/python`.
- **Retained installed state:** `/tmp/wright-desktop-home-014-mcp130-state-20261016-01`.
- Retained API/web ports: 8198/5198. Native UI has no external asset requirement.
- Preserve engineering-image inputs and local reviews; add normal workspace MCP
  tasks. Private enrollment off; generated UI authoring remains gated.
- Qualification copy differs only by fresh state path; real combined-profile
  tool/image/review checks and 51-tool resource verification passed.
- Exact receipts: `/tmp/wright-desktop-completion-qualification-20261017/`.

The required repository gate is currently red on upstream DB freshness, and
consolidated regression checks are running. Do not describe this candidate as
integrated or installed. Finish/reconcile qualification before applying it.

## Backup and service transition

Existing private backup (0700 directory, 0600 files):
`/tmp/wright-desktop-completion-qualification-20261017/named-014-private-backup`.
`named-014-backup-receipt.json` records its hashes and SQLite online backup.
This includes only the exact configuration backup, named plugin cache and owned
prototype state. It does not authorize copying unrelated credentials.

Immediately before applying, recheck current source/version, configuration hash,
workspaces, active runs, reasoning requests and provider processes. Reconcile any
new activity and refresh the backup. The last read found two owned workspaces,
zero run records/start receipts/reasoning requests. That observation alone is not
a promise that the service remains quiescent.

Stop only the exact owned API after quiescence and retain its exit/log. Start the
new frozen service against the **same state and paths**, using:

```bash
/tmp/wright-desktop-completion-015-env-20261017/bin/python \
  /tmp/wright-desktop-completion-2d4f589e-runtime-20261017/prototypes/desktop-harness/preview_server.py \
  --state-dir /tmp/wright-desktop-home-014-mcp130-state-20261016-01 \
  --port 8198 --web-port 5198 --enable-desktop-bridge \
  --enable-native-editor --enable-native-working-view \
  --enable-engineering-image-inputs --enable-local-reviews \
  --enable-workspace-mcp-tasks
```

Retain a process handle, health receipt and new binding/version hashes. This is a
deliberate version transition, never an automatic same-run continuation. If a
newly discovered run is bound to the previous profile, preserve it and use the
existing drift/reconciliation contract; do not rewrite its saved identity.

## Scoped plugin commands

```bash
codex plugin marketplace remove wright-desktop-gb10-prototype --json
codex plugin marketplace add /tmp/wright-desktop-completion-015-marketplace-20261017 --json
codex plugin add wright-desktop-gb10-prototype@wright-desktop-gb10-prototype --json
```

After each command, reconcile an uncertain result before another mutation. Verify
that semantic configuration changes are limited to this named marketplace/version,
and every other setting is preserved. The installer can remove older named cache
files: restore **only missing** old named files from the exact backup, verify their
hashes, and fail on a conflicting existing file. Do not overwrite the entire
configuration or delete newer evidence.

Verify the exact installed command reports 51 tools and the recorded native
resource/profile, and the two workspaces/source/files/settings remain intact.
Actual Windows panel/file delivery is a separate check in a fresh conversation.

## Scoped rollback

First reconcile requests/runs and preserve all new evidence; never automatically
roll back source or state under a live run. Stop only this candidate's owned API.
Restart the previous exact service with the same state/ports and its previous
flags (the command above using the old environment/runtime, omitting
`--enable-workspace-mcp-tasks`):

- Environment: `/tmp/wright-desktop-downloads-014-mcp130-env/bin/python`.
- Runtime: `/tmp/wright-download-83c2ca70-clean-archive-20261016`.

Then restore only the named source through the supported CLI:

```bash
codex plugin marketplace remove wright-desktop-gb10-prototype --json
codex plugin marketplace add /tmp/wright-desktop-downloads-014-mcp130-marketplace --json
codex plugin add wright-desktop-gb10-prototype@wright-desktop-gb10-prototype --json
```

Recover only missing old cache files and verify the original 41-tool command and
resource. No database restore is automatic: a rollback must preserve any new
accepted source, drafts, files, responses and runs. Keep the frozen 0.15 runtime,
package, state backup and receipts for inspection. Do not restart the desktop.
