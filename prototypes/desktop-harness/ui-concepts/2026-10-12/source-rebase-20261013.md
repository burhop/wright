# SteveCAD dev refresh and local prototype rebase

GitHub dev was fetched at `c1a8d00942d8a80ca6229ebed23d7b8f4153a7d9`,
including merged [SteveCAD PR #151](https://github.com/burhop/wright/pull/151).
The mapped `B:\repos\wright` checkout is now fast-forwarded to that exact dev.
Its previous `a4a31c97` commit remains on
`codex/backup-gb10-dev-before-stevecad-20261013`. All three copied UI workflow
files were verified byte-exact before and after the update.

The pending developer documentation was preserved in local commit `e3c4a4b7`.
A separate attached worktree at
`/home/burhop/.codex/worktrees/wright-stevecad-rebase/wright`, branch
`codex/stevecad-ui-rebase`, replays all 26 prototype commits over current dev.
There were no conflicts; Git range-diff shows identical patches for every
replayed commit. The only overlapping runtime file retains both upstream
SteveCAD MCP changes and the prototype's reasoning-dispatch hook.

SteveCAD sources and companion files are available in the mapped checkout:

- `examples/stevecad-demonstrations/prompt-to-reviewed-cad/`
- `examples/stevecad-demonstrations/heat-spreader/`
- `docs/demos/stevecad-check-in.md`

The CAD folder includes the current native-render and earlier reusable workflow,
prompts, native binding/renderer files and historical source versions. The heat
example has its source preparer and original waiting model-basis review; this
refresh does not approve or resume it. Retained SteveCAD CAD/results evidence is
upstream evidence, not a new GB10 or desktop-platform qualification.

Focused offline regressions passed **113**, with **5 skipped** because the
installed Hermes API source is unavailable on GB10. The tests cover desktop
reasoning dispatch/permissions/native ports, upstream MCP image contracts,
Hermes normalization through its available source mirror, unavailable platforms
and SteveCAD source preparation. Git whitespace checks passed. Exact details
and test XML are in `working-view-evidence/source-rebase-20261013*`.

The running developer preview remains on its original worktree. The installed
0.4.0 plugin source/package/configuration and target state were preserved. This
is a source rebase, not an installed-runtime upgrade. Current dev changes the
Node lock; a fresh frontend/package/native qualification remains necessary
before activating this rebased source. SteveCAD execution in the experimental
desktop profile remains unqualified. No providers/models were called, protected
runs resumed, physical actions performed, or remote changes pushed.
