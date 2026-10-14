# Prepared named0.5.0 update — not approved or installed

The same `wright-desktop-gb10-prototype` package is prepared at
`/home/burhop/.codex/worktrees/wright-stevecad-rebase/wright/prototypes/desktop-harness/native-merge-candidate`.
It points to the isolated gate Python and fresh
`/tmp/wright-stevecad-candidate-20261013-01` state, API8126/UI5226. It keeps the
same18tools and digital-only scope, uses the patched SDK resource, and contains
the actual SteveCAD workflows for source/UI tests. CAD execution remains gated.

After specific named-update approval, privately back up the currently selected
configuration and cached0.4.0 package, verify candidate hashes, and run:

```sh
codex plugin marketplace remove wright-desktop-gb10-prototype --json
codex plugin marketplace add /home/burhop/.codex/worktrees/wright-stevecad-rebase/wright/prototypes/desktop-harness/native-merge-candidate --json
codex plugin add wright-desktop-gb10-prototype@wright-desktop-gb10-prototype --json
```

Verify that only the named selection changed and the installed package matches.
The CLI evicts the old cache on replacement; restore that backed-up cache
byte-exactly without redirecting the new selection. Preserve old source/state,
other settings, model/auth choices, and all saved evidence. Do not restart the
desktop or reload all chats; use a fresh chat if old inventory persists.

Scoped rollback selects the preserved original0.4.0 package:

```sh
codex plugin marketplace remove wright-desktop-gb10-prototype --json
codex plugin marketplace add /tmp/wright-host-adaptive-native-working-view/prototypes/desktop-harness/native-working-candidate --json
codex plugin add wright-desktop-gb10-prototype@wright-desktop-gb10-prototype --json
```

Never restore the entire old configuration or delete new saved source/state.
This proposal does not request permission for physical actions, broad provider
permissions or engineering reviews. Those retain their existing owners.
