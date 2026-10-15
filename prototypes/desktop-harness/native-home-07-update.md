# Named experimental 0.7.0 update

Installed and independently protocol-verified on 14 October 2026. Receipts are
indexed in `workspace-home-progress.md`; Windows acceptance remains pending. Authorized within the saved
demo-readiness goal. Update only `wright-desktop-gb10-prototype`.

Candidate marketplace:
`/tmp/wright-desktop-engineering-demos-next/prototypes/desktop-harness/native-home-07-candidate`.
Runtime: this continuation worktree, API8137, isolated state
`/tmp/wright-desktop-create-proof-20261014-01`. Freeze its runtime sources while
selected; create a separate continuation checkout before further runtime edits.
No existing workspace/run/configuration is migrated or rebound.

Changes: explicit workspace creation, Files metadata search, Recent runs and exact
run inspection, bounded PNG/JPEG result viewing. The model-image input profile is
unavailable. Engineering provider execution, generated process UI authoring and
other unqualified capabilities retain their existing gates. File upload/download
and arbitrary file previews are still unavailable. Windows acceptance is pending.

Qualification: 127 combined Python tests and 52 panel tests; served home/editor,
creation, run navigation/source drift and files proofs in `workspace-home-progress.md`.
Package receipt: `/tmp/wright-desktop-create-proof-20261014-01/candidate-0.7.0.json`.
It verifies the exact command, 31 tools, visibility, profile and resource SHA-256
`4d8a1bafb897bf76f092f716c7466c220ec6658a0b6bcb351dbbf1ccd77433bb`
(2,208,170 bytes). Skill frontmatter validation passed.

Before applying: privately back up current config and the complete named plugin
cache; record current selection and pending run/request counts in the old state.
Preserve all prior cached versions and services. Use installed CLI 0.159.2, whose
local `plugin add` command was inspected; do not upgrade software.

```sh
codex plugin marketplace remove wright-desktop-gb10-prototype --json
codex plugin marketplace add /tmp/wright-desktop-engineering-demos-next/prototypes/desktop-harness/native-home-07-candidate --json
codex plugin add wright-desktop-gb10-prototype@wright-desktop-gb10-prototype --json
```

After applying: compare configuration semantically, allowing only the named
marketplace source/selection. Restore any evicted old cache versions byte-exactly
without replacing the new selection. Compare installed package bytes, then run
`candidate_protocol_probe.py` against the actual installed package to a new receipt.
No desktop restart, unrelated settings or other chat reloads are authorized here.
An existing chat may retain old tools; verify actual inventory in a fresh chat.

Scoped rollback to the preserved installed 0.6.0 source:

```sh
codex plugin marketplace remove wright-desktop-gb10-prototype --json
codex plugin marketplace add /tmp/wright-desktop-engineering-demos/prototypes/desktop-harness/native-home-candidate --json
codex plugin add wright-desktop-gb10-prototype@wright-desktop-gb10-prototype --json
```

Never restore the entire old config or delete new state/evidence. A rollback
changes only selection; it does not erase workspaces created during testing.

Official packaging guidance was rechecked on 14 October 2026:
https://developers.openai.com/plugins/build/plugins . It documents local
marketplaces and compatibility manifests, and recommends restarting for local
updates and testing in a new chat. This task does not authorize a desktop restart;
the installed CLI/fresh-chat path is a locally tested behavior whose next-version
result must be verified, not assumed from the documentation.
