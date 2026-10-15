# Named 0.11.0 candidate and scoped rollback

Prepared, not installed. The submitted goal authorizes this named update after
exact qualification and backup. No other plugin, service or setting changes.

Runtime: `/tmp/wright-desktop-custom-candidate`, frozen from the tested feature.
Marketplace: `prototypes/desktop-harness/native-home-011-candidate`.
Fresh state: `/tmp/wright-desktop-home-011-state-20261015-01`; API8185, web5185.
Enable desktop bridge, native editor, common working view and local reviews only.
Keep image input, confined inspection and enrolled engineering tasks disabled.

The two new UI-only tools preview a public HTTPS source and create an exact
reviewed source plan. Saved plans are discoverable across the exact workspace.
Existing owners still enforce setup review/apply, protocol validation, workspace
availability and individual action authority separately. Local-command/full-JSON
import and secret entry remain unsupported. Expected total:36 tools.

Before applying: verify the actual package command/resource and all profile flags;
exercise custom source and saved-plan recovery in the combined profile; regress
workflow/template/editor and local-review continuation. Save exact hashes and
failures. Back up only the named marketplace selection, installed manifest and
all its old cached versions; retain unrelated configuration fingerprints. Preserve
0.10 service/state and cache bytes. Record candidate commit and rollback backup.

Apply after qualification and backup:

```sh
codex plugin marketplace remove wright-desktop-gb10-prototype --json
codex plugin marketplace add /tmp/wright-desktop-custom-candidate/prototypes/desktop-harness/native-home-011-candidate --json
codex plugin add wright-desktop-gb10-prototype@wright-desktop-gb10-prototype --json
```

Scoped rollback to the preserved 0.10 runtime:

```sh
codex plugin marketplace remove wright-desktop-gb10-prototype --json
codex plugin marketplace add /tmp/wright-desktop-template-entry/prototypes/desktop-harness/native-home-010-candidate --json
codex plugin add wright-desktop-gb10-prototype@wright-desktop-gb10-prototype --json
```

Do not restore a complete configuration over unrelated changes. If CLI cache
replacement evicts older named versions, restore those exact backed-up bytes and
verify their hashes. Verify the installed manifest, tools and resource against
the tested candidate. Do not restart the desktop. Actual Windows acceptance and
engineering demonstrations remain open; installation cannot prove them.

## Candidate qualification checkpoint

Frozen runtime7afc90c4 passed actual package/resource checks:36 tools and resource
SHA25651bff22d7e8a4f9882483ba74a77ae5599cf60f348ce3b20e2f7691ef6d56fbc.
Eleven home/template/editor browser checks and four custom-source browser checks
passed in the combined profile. A synthetic review completed the same run after
reconnect and explicit Continue; a stale subject was rejected. These are private
GB10 browser/MCP checks, not Windows or engineering acceptance. See
native-home-011-evidence.json. Repository gates, named backup/update and installed
verification remain pending. The first fixture launcher and probe assertion
failures are retained; runtime guards and metadata were not weakened.
