# Named experimental 0.8.0 candidate

Prepared, not installed. Authorization is in the saved demo-readiness goal.
Only `wright-desktop-gb10-prototype` may change; no desktop restart.

Candidate source worktree: `/tmp/wright-desktop-ui-files-candidate`.
Marketplace: `prototypes/desktop-harness/native-home-08-candidate` under it.
State: `/tmp/wright-desktop-ui-files-state-20261014-01`, to be created from a
consistent private snapshot of preserved 0.7.0 test state. Do not attach copied
runs to execution or carry credentials. Preserve exact source/evidence; only the
copied workspace-root registration may relocate. This is a separate test copy.

Changes: UI-only bounded text-file preview; corrected recorded-review guidance
and declared exact-subject review port. Shared editor preserved. Default image
input/enrolled MCP task profiles stay unavailable. No new provider installation,
permission grant, authentication route or engineering execution qualification.

Before installation: freeze runtime source, prepare isolated dependencies and
service, test actual package command/resource with candidate_protocol_probe.py,
check the copied state through Workflows/Files, and privately back up current
configuration plus all named cache versions. Compare before/after semantic
configuration, allowing only the named marketplace source/selection. Keep old
cache bytes and services intact. Qualify installed bytes/protocol afterward.

Apply only after those checks:

```sh
codex plugin marketplace remove wright-desktop-gb10-prototype --json
codex plugin marketplace add /tmp/wright-desktop-ui-files-candidate/prototypes/desktop-harness/native-home-08-candidate --json
codex plugin add wright-desktop-gb10-prototype@wright-desktop-gb10-prototype --json
```

Scoped rollback selects the preserved 0.7.0 marketplace; do not restore an entire
old configuration or remove new work/evidence:

```sh
codex plugin marketplace remove wright-desktop-gb10-prototype --json
codex plugin marketplace add /tmp/wright-desktop-engineering-demos-next/prototypes/desktop-harness/native-home-07-candidate --json
codex plugin add wright-desktop-gb10-prototype@wright-desktop-gb10-prototype --json
```

Actual Windows panel acceptance is separate. Start a fresh GB10 conversation when
ready; old chats may retain their prior tool inventory. Do not claim rendering
from tool discovery alone.
