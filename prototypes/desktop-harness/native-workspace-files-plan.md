# Native workspace files prototype — 27 October 2026

Status: file-centered UI and ordinary-file lifecycle qualified on Linux and an
independent Windows simulated host. The exact resource is installed as named
prototype 0.28 in fresh isolated preview state. Actual desktop general-file
rendering/delivery/restoration remain unverified. Prior 0.27 packages, runtime,
client configuration, original service/state and engineering evidence are preserved.

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
- [x] Linux and independent Windows visible journeys, exact installed package,
  source/resource identity and concise native walkthrough/handoff.
- [ ] Direct native general-file rendering/delivery/restoration qualification.

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

The final prototype regression has 368 passing tests and 10 Windows-only skips;
52 file/probe checks cover the subsequent opaque-file distinction and 109 affected
protocol checks cover import routing and presentation-mode continuity. The full
frontend gate has 2072 passing tests. Type, focused lint and self-contained native
build checks pass. Independent Windows qualification passed ten actual-owner
journey checks on identical resource bytes, 126 adapted prototype and 44 frontend
checks, types/lint. Its sources/runtime remained exact, operational counts stayed
zero and owned services/ports closed. Privileged symlink cases and actual native
general-file rendering remain unverified. The old 0.27 fixed A/B/PNG walkthrough
is historical; 0.28 uses the ordinary workspace file list.

Current resource: `6e2c52c2464837e817e0d2d71776f05008090527d6840e5b7c5ef249d71ccd01`.
All three thread/file entrypoints preserve the frozen file-presentation choice.
The old fixed probe remains in the preserved 0.27 package; 0.28 replaces its
diagnostic tools with the app-only ordinary-file descriptor/context mechanism.

Qualification reused `native_workspace_files_setup.mjs` and
`native_workspace_files_acceptance.mjs` with state outside the checkout. Windows
found two test-only portability issues: snapshot keys need `Path.as_posix()`;
textarea expectations normalize CRLF only at the browser boundary. File/source,
hash, instruction and owner comparisons remain exact. Corrections are committed
through `2d133c4a`; the product/resource bytes are unchanged from `cb958784`.

The installed 0.28 preview freezes 1867 source files from `2d133c4a`. Only the named
plugin registration/cache changed; unrelated settings were hash-checked and
prior named cache versions retained. New chats intentionally use **Native file
qualification 3de8ff77** in `/tmp/wright-desktop-native028-workspace-files-state-20261027`,
served by its owned loopback API 18153. It has no engineering runs/reviews/reasoning
requests or personal accounts; provider autostart is off. It does not migrate or
silently retarget the original SteveCAD workspace. The exact installed MCP command,
resource bytes and ordinary-file flag pass; that does not establish host rendering.

Current report/walkthrough and Linux/Windows receipts:
`/home/burhop/repos/wright/.local-run/desktop-usability-evidence-20261026/native-workspace-files-installed-028-20261027/`.
The new walkthrough replaces the removed **Open all three** diagnostic launcher.
No push/merge/publication, engineering execution or desktop restart occurred.

Next: qualify compatible existing engineering viewers and the remaining native
boundaries. Isolated `dxf-viewer` 1.0.50 renders retained geometry/text with a local
font and public FitView; it is not integrated. Online 3D Viewer 0.18.0's default
STEP path requires a CDN engine blocked by the restrictive experiment policy;
its fflate pin also has an audit finding. Qualify supported local assets and a
clean dependency set before integrating. No CAD parser/viewer or security bypass
was built. Dynamic native tab captions remain an unverified host capability;
long Source instructions remain a separate focused usability item.

Source readability batch in progress: the existing shared textarea defaults to
logical unwrapped code lines, with an explicit Wrap lines toggle. No instruction
or source text is removed, projected, rewritten or automatically saved. This is
not a new editor or parser. Extend the actual-owner file journey to measure the
first engineering declaration within wide/narrow viewports, preserve the entire
source through toggles, and reject dirty/save side effects on both bracket and
Robot workflows. The installed 0.28 preview remains frozen while this separate
candidate is qualified; its binding includes the UI hash and must not be patched
in place to hide configuration drift.

That Source candidate (`3bf847a9`, resource `bd9e8a61…73be`) passed all 12
actual-owner journey checks, 2072 frontend tests and types/lint on Linux, and the
same 12 checks/75 owning tests/types/lint on independent Windows. All test-owned
services closed with zero operational counts. It remains separate from installed
0.28 while the final small observability batch is qualified.

Next bounded batch registers one read-only `wright_ui_inspect` app tool using the
already-pinned MCP Apps 1.7.5 public API and existing `captureUiReview`. It returns
only this Wright iframe's build, exact navigation subject and bounded geometry;
the fixed Report UI problem control is identified without reading DOM text or
form/source values. Empty closed input accepts no arbitrary selector or script.
No backend, storage, process, approval or host-shell action is added. A standalone
SDK protocol/privacy spike passes. The Office-only Document Control interface is
not used as a workaround. Actual OpenAI-host discovery/invocation remains
unverified until observed; SDK/browser success is not native acceptance. The
real-owner journey will exercise both workflow frames and assert no dirty/save
effect, source-value privacy and denied extra arguments. Source's explanatory
header is shortened to keep its controls in one row where space permits.

Official extension guidance rechecked 27 October:
https://developers.openai.com/plugins/build/extensions documents file entrypoints
and opaque file resource input. Public host-file opening remains the previously
qualified native-tab operation; no dynamic tab-title or arbitrary host automation
capability has been established by this backend work.
