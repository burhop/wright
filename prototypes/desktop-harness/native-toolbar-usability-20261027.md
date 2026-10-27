# Native document toolbar correction — 27 October 2026

## User journey and evidence

Opening either prepared workflow in a real native desktop tab now displays the
shared diagram; the reference PNG displays an image. User observation and two
screenshots are retained under the main repository's
.local-run/desktop-usability-evidence-20261026/native-observation-20261027/.
The user rejects excessive Wright chrome above the canvas. Both native tab
captions are generic; host caption support is a separate unresolved boundary.

## Smallest correction

- Reuse the existing shared editor fileActions slot for desktop view navigation
  and Workflow details. Keep the accepted editable title once and preserve the
  existing editor toolbar, source, instructions, Undo/Redo, Save and Check.
- Remove the file-test heading for native file surfaces; the host already shows
  exact document identity. Other entry points keep Workspace home navigation.
- Put workspace/path/revision, transfer, explanatory context and draft recovery
  into Workflow details, using existing clients and state. Unsaved, uncertain
  draft outcomes and selected-run context remain visible without opening it.
- Place Report UI problem in a compact footer, preserving its capture/send flow.
- Scope layout styling to the desktop composition. Hermes/shared canvas and
  execution behaviour stay unchanged. No new framework, executor or viewer.

## Qualification

Measure canvas position/area at normal and narrow panel sizes against the exact
previous resource, with actual owners and harmless fixtures. Exercise details,
transfer, draft restore, source/diagram, editing history, save/reopen, and retained
result -> producing step -> same run. Assert real visible evidence and preserve
source mismatch detection, including Robot Tracking Diagnosis regression. Run
focused checks and final appropriate frontend gates. Freeze a new candidate only
after visual review; exact installed bytes and native observation remain distinct.
No engineering execution, account change, push, merge or publication.

## Tasks

- [x] Preserve native observations and screenshots; classify prior turn as progress.
- [x] Inspect clean feature worktree, existing owners and current goal authority.
- [x] Implement scoped toolbar/context composition.
- [x] Qualify measured density and complete Linux user journeys; inspect screenshots.
- [ ] Qualify independent Windows boundary where available.
- [ ] Freeze/verify/update only named plugin after gates; update evidence index.
- [ ] Record remaining native limitations without claiming user acceptance.

## Current local evidence

Exact tested resource SHA256:
`62d6e6028129bde92e907c91bf7e50c0cd275e09f779ff20f231cd55273a4298`.
Evidence: `.local-run/native-toolbar-20261027/` (private clients are not handoff
artifacts). In the measured native-file simulation, wide/narrow diagram tops
improve from 233/327px to 82/147px; at 800x700 and 150% display scale, 292px to
118px. Actual backend/source owners, visible nodes, viewport bounds, details,
Escape/focus, source bytes and footer report focus are checked. Accepted sources,
draft list and history are unchanged in this read-only density test.

The exact final resource also passes six disposable authoring/transfer/file
journey phases and the retained-run journey (Results1/1, exact retained PNG,
producing step, same run, no false mismatch). Initial harness selector/envelope
and missing expected-image-hash input errors are retained separately. A first
full gate mixed old/new module snapshots during the revision-display test edit;
it is not counted as a final gate. The stable final gate is run separately.
Independent Windows requalification is in progress. This resource is not yet
installed and has no new actual native desktop observation.
