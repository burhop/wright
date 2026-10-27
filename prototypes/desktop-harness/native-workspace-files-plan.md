# Native workspace files prototype — 27 October 2026

Status: read-only backend/MCP slice locally qualified; UI integration remains
in progress. Installed 0.27 stays frozen.

The user selects a workspace, browses its ordinary files, and opens each in its
associated native host tab. Reuse Wright's refined workflow editor and existing
compatible viewers. Keep compact contextual workspace tools rather than another
set of document tabs. No new executor, auth framework or gateway policy.

## Existing owners and first slice

Workspace repository/session ownership, WorkspacePath and file/source use cases
resolve scope and accepted bytes. The current fixed-file manifest is diagnostic,
not the general boundary. Add an opt-in read-only prototype backend presentation
boundary for descriptors and reverse host-path resolution. It must never parse
opaque resource URIs, guess workspace roots, activate sessions or create sources.
Explicit remembered scope wins on continuation and must still match the actual
path and source. Ambiguous fresh scope is rejected rather than guessed.

Client qualification must verify same execution-host filesystem and byte identity
before native open. A remote/container path without a qualified host mapping is
unsupported, not silently translated via shares/SSH. This phase does not relax
host security. Existing backend is not restarted or changed; use isolated state.

## Tasks

- [x] Backend descriptor/reverse-context boundary, disabled by default.
- [x] Negative controls: wrong agent/session/root, hidden paths, traversal, links,
  missing/oversized files, changed source and ambiguous scope; no source writes.
- [x] Thin app-only MCP descriptor/file-context tools, exact source and local-byte
  checks, and frozen capability/module pins. Fixed proof and general modes are
  mutually exclusive. Fresh ambiguous sessions fail closed; remembered exact
  session scope remains usable without activating another session.
- [ ] Public file-open UI integration and ordinary-file lifecycle proof. The new
  MCP mode is not yet selected by the Home UI; do not enable it in the installed
  plugin simply because backend tests pass.
- [ ] File-centered workspace entry, reusing current controls/owners and fallback.
- [ ] Qualify compatible existing STEP/DXF viewers; do not build CAD renderers.
- [ ] Full visible journeys, Windows qualification, exact candidate and handoff.

V1–V7: engineering source/runs/reviews remain with existing owners; file viewing
never validates engineering output or authorizes an external action. Source,
workspace, session and representation identities remain explicit. Closing and
reopening reconcile; no uncertain action is replayed. Existing working UI and
shared canvas remain available. A different workflow (Robot Tracking Diagnosis)
proves the common file/source mechanism without executing engineering processes.

## Qualified boundary and next change

The backend exposes opt-in POST `/api/desktop/native-files/describe` and
`/api/desktop/native-files/context` reads. Workspace/session ownership and file
confinement remain in existing owners. The MCP adapter checks that the exact
returned path and bytes are accessible on its own execution host. No share/SSH
mapping or opaque resource-URI interpretation occurs. PNG/JPEG signatures select
the image presentation; this does not qualify decoding or engineering fidelity.
Other formats explicitly have no qualified native viewer. The checks observe
bytes at reads, not a promise that a file can never change after a host open.

The next coherent UI batch must connect ordinary file selection to the documented
host-open operation and pass remembered exact session scope on continuation.
Replace the category-tab landing layout in that opt-in mode with workspace files,
keep setup/history available as contextual tools, and retain the existing source,
draft, editor and exact-run fallback. Reuse current file/editor components where
appropriate; do not reuse inaccessible click-only file rows merely for visual
consistency. Test visible focus, keyboard navigation, bounded lists and narrow
panels. New-workflow/template/import saves must enter the same file-open path.

Linux evidence: `.local-run/native-workspace-files-20261027/`. The full prototype
regression has 364 passing tests and 10 Windows-only skips. A final focused suite
also exercises the added cross-workspace source-reply denial. Windows and actual
native general-file rendering remain unverified. The existing 0.27 walkthrough
continues to test only the fixed A/B/PNG proof.

Official extension guidance rechecked 27 October:
https://developers.openai.com/plugins/build/extensions documents file entrypoints
and opaque file resource input. Public host-file opening remains the previously
qualified native-tab operation; no dynamic tab-title or arbitrary host automation
capability has been established by this backend work.
