# Native workspace files prototype — 27 October 2026

Status: file-centered UI and ordinary-file lifecycle locally qualified on Linux.
Windows and actual desktop general-file qualification remain pending. Installed
0.27 stays frozen.

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
- [x] Public file-open UI integration and ordinary-file lifecycle proof on Linux
  with real MCP/API/storage and a simulated host. Actual host display is separate.
- [x] File-centered workspace entry: compact sorted rows and title/path search,
  contextual tools, normal creation, shared editor, and explicit preview fallback.
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

The opt-in Home mode now opens workspace files through the documented host-open
operation. Its backend flag and advertised host capability must both be present;
otherwise the existing editor/previews stay available with a visible explanation.
The shared observation model passes exact remembered scope in both fixed and
general modes, including input-only file entrypoints. A stale remembered digest
holds before rendering; the explicit current-saved-revision action rereads that
same file without a digest pin. It does not activate another session or replay
work. Source saves update the existing per-file navigation/draft owners.

The new landing view has no category tab strip. Workflows sort first, other files
sort naturally, accepted titles and normalized filenames are searchable, exact
paths remain in keyboard-accessible details, and setup/history are contextual.
New workflow creation opens another native tab and refreshes the file list; its
form resets only after the open request is confirmed. Opaque uploaded `.wflow`
files keep the existing read-only text preview. Damaged canonical accepted files
still hold; an ordinary owner read may create its normal private lock file but
cannot create accepted source heads or history.

Linux evidence: `.local-run/native-workspace-files-ui-20261027/`. Ten visible
journey checks pass on a fresh workspace: real normal-owner creation, two different
workflows, independent file views, edit/Undo/Redo/save/search/reopen, retained PNG,
stale-pin hold and explicit reconciliation, unsupported STEP, and opaque-upload
preview, and browser export plus one inspected import into another native file
view. Original source/instructions/history are preserved. Three viewport/scale
configurations are measured. The new compiled UI
also passes the established read-only retained-run regression through the
unchanged installed MCP/API. This preserves Results 1/1, producing-step evidence,
return to the same run, and absence of a false mismatch.

The broad prototype regression has 366 passing tests and 10 Windows-only skips;
52 file/probe checks cover the subsequent opaque-file distinction and 109 affected
protocol checks cover import routing and presentation-mode continuity. The full
frontend gate has 2072 passing tests. Type, focused lint and self-contained native
build checks pass. Windows and actual native general-file rendering remain
unverified. The existing installed 0.27 walkthrough still tests the fixed A/B/PNG
proof; it does not expose this new mode.

Current resource: `6e2c52c2464837e817e0d2d71776f05008090527d6840e5b7c5ef249d71ccd01`.
All three thread/file entrypoints preserve the frozen file-presentation choice.
The old fixed probe remains available separately; the installed plugin is unchanged.

Next: [independently qualify the exact code/resource on Windows](native-workspace-files-windows.md) using the reusable
`native_workspace_files_setup.mjs` and `native_workspace_files_acceptance.mjs`.
Keep API workspace state outside the checkout; Wright correctly protects code
directories. Do not install or enable the general candidate before qualification.
Then qualify existing compatible engineering viewers and the remaining native
boundaries. Dynamic native tab captions are still an unverified host capability.

Official extension guidance rechecked 27 October:
https://developers.openai.com/plugins/build/extensions documents file entrypoints
and opaque file resource input. Public host-file opening remains the previously
qualified native-tab operation; no dynamic tab-title or arbitrary host automation
capability has been established by this backend work.
