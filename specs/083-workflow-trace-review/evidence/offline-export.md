# Offline Export

Chromium generated both export modes from the production exporter for the real
retained `printed-replacement-part-01` campaign run, extracted them beneath a
relocated directory, blocked all HTTP and HTTPS requests, and opened each
`index.html` through `file://`.

- Full data: the report rendered, `mesh-preview.png` and `source_mesh.stl` were
  visible, and package-relative original-file links were available.
- Report only: report rendered with its retained raster previews bundled under
  `assets/previews/`; nonvisual original files remained excluded and were
  explicitly labeled `omitted_from_export`.
- Both exact downloaded archives pass `unzip -t` and are retained under
  `evidence/live-campaign/`.
- Exporter tests cover repeated filenames, relative paths, report membership,
  external resources, deterministic ZIP metadata, and digest mismatch rejection.
- The manifest states that no interactive viewer is bundled. STL, STEP, and 3MF
  use recorded previews and original files when available; this is a truthful
  fallback, not a geometry-validation claim.

## Original Input Recovery (2026-09-17)

The campaign importer now queries the read-only `dataset_revisions` table using
the run's exact dataset/template digests. It verifies the manifest fingerprint
and each repository input file's recorded SHA-256 before copying that file into
the review workspace. Later edits to repository inputs cannot change the copy.
It does not substitute a current template for the executed AI instructions.

For `printed-replacement-part-01/attempt-003`, all five originals match: prompt,
context, requester profile, PNG sketch and editable SVG. Both report modes show
the exact prompt text and PNG; the full-data ZIP includes the five originals
under `inputs/` alongside the 15 outputs. The geometry activity links to its
original request using the exact input reference in its design record.

The assembled-context reference remains a reference, not a claimed recovered
execution snapshot. Its separate original context and profile are available.
Additional per-step AI instructions are still distinguished from the recovered
user request.

The 24-run import recovered 181 original files. `context.md` for
`raspberry-pi-enclosure-03` and `sensor-interface-pcb-02` did not match their
historical hashes and were not substituted. Original campaign evidence was not
modified. All 24 existing corpus projection checks passed.

Verification: 26 focused Python tests and six Chromium tests passed. The live
test exports both ZIP modes through the API, verifies all 20 file identities,
opens relocated `file://` reports with HTTP(S) blocked, compares displayed
prompt text against the original file, checks the input image and output links,
and exercises desktop/mobile layouts. Negative tests cover changed files,
wrong dataset revisions, corrupted manifests, and subsequent repository edits.

## Assumption Traceability (2026-09-17)

Each recorded assumption now carries its exact source document identity and an
array-entry pointer within that decoded record. Activity panels expose a source
link beside each statement. The source view highlights the verbatim statement,
identifies its producing activity and the activity completion time, and links
to input references explicitly cited by that document. It does not infer an
assumption-specific justification, approval, author identity, or requirement
mapping from nearby text. Source pointers stay in the report data; the visible
view uses engineering labels, not JSON paths.

Assumptions belong to individual activity iterations, not the final activity
output reused across earlier iterations. Tests cover two iterations with
same-named source files, exact source pointers, invalid list entries, and two
same-named prompts with different input identities. Both export modes retain
the human-readable source excerpt even when the original file is excluded.

Verification: 25 focused Python tests and six Chromium tests passed. The actual
campaign test compares all three displayed assumptions with the original
exported design record, follows each citation, checks the producing activity,
opens the cited original request and navigates back, and checks mobile layout
with HTTP(S) blocked. Screenshots: `live-campaign/engineering-review-assumption-source.png`
and `live-campaign/engineering-review-assumption-source-mobile.png`.

## Completed Engineering Process (2026-09-17)

The report presents supplied inputs, completed activities and generated outputs.
The swimlanes now include the original request excerpt, supplied sketch and
document links outside the consuming block, connected only where the retained
source record establishes the input relationship. Generated files appear below
their producing activity. The separate activity/handoff index was removed.
`source_mesh.stl` is labeled "Generated part model" for this run; supplied models
are labeled separately rather than described ambiguously as original models.

Activity details lead with what happened in engineering terms, software/version,
elapsed time and recorded activity passes, followed by brief linked inputs.
Progressive disclosure exposes lifecycle events, reported engineering operations
and source-linked assumptions. Full user requests remain in input views, not
repeated as the activity explanation. Events, inputs, operations and assumptions
remain associated with their particular recorded pass.

Bambu Studio version `02.08.02.61` comes from the generated 3MF package's
Application metadata, not a version inferred from a filename. Metadata reading
is size-bounded and does not check geometry or execute package contents.
Blender is identified by the retained repair operation; its version and the
geometry authoring tool/version are not retained. The four whole-run AI requests
are not presented as CAD iterations. Internal retry counts and an underlying
LLM version remain unknown rather than invented. Authorization remains correctly
labeled as automated, with a simulated transfer and no physical dispatch.

Verification: 31 focused Python tests, six Chromium tests and all 24 retained-run
trace acceptance checks passed. The Chromium suite exports both modes through
the API and opens relocated HTML with HTTP(S) blocked. It checks actual input
text/images, all 20 original file identities, produced-file navigation,
source-linked assumptions, package version metadata, execution details and
keyboard access directly in the diagram. Layout checks at 1440, 909 and 390 px
verify that handoff labels do not overlap activity, input or output controls.
The 909 px screenshot and desktop/mobile activity views were inspected.
Ruff, JavaScript syntax and `git diff --check` passed. These are report and
traceability checks, not validation of engineering output correctness.

Screenshots include `live-campaign/engineering-review-completed-process-909.png`,
`live-campaign/engineering-review-activity-overview.png` and
`live-campaign/engineering-review-execution-record.png`.

## Manufacturing Labels and Visible Tools (2026-09-17)

The model preview is now labeled "Replacement part design", the cleaned STL
"Part mesh after cleanup", and the package thumbnail "Slicer model preview".
The report explicitly distinguishes digital mesh cleanup from physical repair
and explains that the slicer thumbnail shows the whole model, not individual
layers. Printer/nozzle, material, layer height and infill are grouped under
"3D printing", with links to print settings, slicing results and the static
toolpath projection. This run reports supports enabled and zero support moves;
it does not retain a separate model-with-supports preview. No support geometry
or slicing results were generated to fill that gap.

The retained `support-preview.svg` is a top-down G-code extrusion projection,
not a pre-slicing support model. Its generating script,
`scripts/engineering_dataset_slice.py`, matches the operation source SHA-256
recorded by this run (`9f559f0480361b213ec0171c8510e17f55849cab0d151d299595865cf7f9a4d7`).
That source also establishes that `slice-preview.png` was taken from
`Metadata/plate_1.png` in the actual package. The supplied drawing files are now
labeled "Design sketch (PNG) / Raster image" and "Design sketch (SVG) / Vector
drawing"; both original identities and files are preserved.

Each activity block now has an explicit "Tool used" field. Activity details
have a dedicated "Tool & execution" section with software, retained version,
timing, recorded passes and a source link. Blender is visible directly on the
mesh cleanup block; the geometry tool and Blender version remain unrecorded.

Size-bounded SVG previews are included in both export modes and rendered only
through image elements. An adversarial SVG browser test confirms embedded
scripts/onload handlers and external image requests do not execute in this
image context. Original bytes are unchanged and remain digest-verified.

Verification: 37 focused Python tests, seven Chromium tests and all 24 corpus
trace checks passed. Both relocated offline exports preserve all 20 artifact
identities. Screenshots were reviewed at desktop, narrow desktop and mobile
sizes. New screenshots include `live-campaign/engineering-review-blender-tool.png`
and `live-campaign/engineering-review-toolpath-projection.png`. Interactive
layer/G-code evaluation and producer-captured support-geometry previews are
recorded as future work, not represented as implemented viewers.

## Compact Diagram and Source Recovery (2026-09-17)

The standalone report defaults to Compact blocks and handoffs. Detailed restores
the responsibility swimlanes, external supplied inputs and produced-file lists.
Both modes retain tool identity, keyboard selection, iterations and clickable
handoffs. The campaign authorization software label is now "Wright AutoTest";
the automated actor and simulated-transfer scope have not changed.

The verified PNG/SVG pair appears once as "Design sketch". The original PNG was
rendered from the editable SVG by the campaign image-normalization script for
image upload. "Editable source" exposes the alternate file without making it
look like a second design. Both original files and hashes remain in the ZIP.

The transferred bundle omitted the assembled execution-context file, not its
source documents. The importer now includes a separately labeled reassembly of
the digest-verified `user-profile.md` and `context.md`, joined with the campaign
preparation recipe. This does not assert recovery of the original runtime bytes
or capture of the entire execution context. Its source-document links work in
the offline report; the full-data ZIP stores it under `inputs/reconstructed/`.

The historical rapid-output checkpoint identifies the Blender construct/export
guidance and explicitly lists the successful case01/attempt003 pilot. A copy is
packaged under `evidence/sources/` and linked from the geometry tool field.
This is documentary attribution, not a recovered raw tool-call trace; the
geometry software version remains unavailable. Other attempts are not assigned
this attribution unless the checkpoint explicitly identifies their completion.
The raw campaign records and original output files remain unchanged.

Verification: 43 focused Python tests, seven Chromium tests, and all 24 corpus
trace checks passed. Browser checks use API-generated ZIPs, relocation, file
origins and blocked networking. All 22 resource identities/digests are checked;
the two additions are the reconstructed input and documentary source. Both
diagram modes were checked at 1440, 909 and 390 pixels for clickable handoffs,
visible tool names, page overflow and connector-label/control collisions.
Screenshots: `live-campaign/engineering-review-compact-909.png`,
`live-campaign/engineering-review-detailed-909.png` and their 390-pixel variants.

The user's new timing requirement is FR-035, with implementation tracked by
T068. New producers must retain start/end and monotonic elapsed milliseconds per
attempt, including authorization, retries and failures. That runtime work is
pending; this UI revision does not fabricate durations for the historical run.

## Independent Swimlane Disclosure and Purposeful Images (2026-09-17)

This revision supersedes the global Compact/Detailed switch above. All
responsibility and supplied-input lanes remain present. Each responsibility
cell is a keyboard-operable disclosure button with an arrow and expanded state;
it expands only that row's summaries and produced files. Other rows retain their
size and state, and shared activity columns remain aligned. Default blocks are
at most 128 pixels wide, with tool names and full detail selection retained.
Horizontal scrolling, pinned responsibility labels and explicit zoom/fit controls
support larger processes. Connector coordinates account for the selected zoom.

The results overview now contains one meaningful design preview. The redundant
green slicer thumbnail remains among the slicing activity's files and in both
exports, but is not promoted as another result or used to preview the manufacturing
package. The freed space presents layer height, infill/pattern, walls, support
strategy and threshold, reported support moves, and source-linked model
preparation. Cleanup, orientation, remeshing and decimation statements come from
the retained report. A support-geometry preview is explicitly unavailable, not
replaced by a recolored model or fabricated illustration.

Verification: 44 focused Python tests and eight Chromium tests passed. The real
case01 ZIPs were regenerated through the API and tested after relocation with
networking blocked, retaining all 22 artifact identities and digest checks.
Mixed row-expansion states were checked at 1440, 909 and 390 pixels for overflow,
tool visibility, file access, handoff selection and label/control collisions.
A separate, explicitly synthetic 30-activity/five-lane layout fixture verifies
independent expansion, unchanged other-row heights, fit-width scrolling,
zoom-correct connector endpoints, and keyboard/detail access to activity 30.
It is layout-test evidence, not an additional engineering campaign run.

Screenshots include `live-campaign/engineering-review-rows-collapsed-909.png`,
`live-campaign/engineering-review-rows-1-909.png`, their 390-pixel variants, and
`live-campaign/layout-fixture-30-compact-fit.png`.

## Compact Supplied-Input Blocks (2026-09-17)

The supplied-input row now uses individual blocks at the same compact scale as
activities (at most 128 pixels wide), showing input type, name and provenance
status. Prompt excerpts, thumbnails and secondary links are hidden until that
row is expanded. Each block remains selectable while collapsed. A dashed
connector joins the supplied set to its recorded consumer, without implying
that inputs are separate process activities.

Expanding the responsibility cell reveals the request excerpt, actual sketch
preview and context source documents inside their respective input blocks.
Consumer and complete-input access share a labeled footer in the expanded row.
Large sets show three inputs and a remaining-input block, with access to the
complete list; they do not stretch the collapsed row into a document inventory.
Other responsibility rows retain their own expansion state and height.

Verification: 44 focused Python tests and eight Chromium tests passed. Both
real-case export modes were regenerated through the API, relocated and opened
offline with networking blocked; all 22 resource identities/digests remain
checked. Browser coverage includes compact-block dimensions, keyboard disclosure,
source grouping, input-connector endpoints, independent row heights, 27-input
overflow access and the existing 30-activity layout checks. Mixed row states were
checked at 1440, 909, 702 and 390 pixels. Screenshots were visually reviewed,
including `live-campaign/engineering-review-input-blocks-compact-702.png`,
`live-campaign/engineering-review-input-blocks-expanded-702.png` and the mobile
full-page capture. No engineering tools were rerun or historical facts altered.

## Toolpath Projection Deferred (2026-09-17)

The flattened `support-preview.svg` no longer has a reviewer-facing page or
links in the printing summary, activity details or activity file list. It is
marked archive-only by the printed-part presentation adapter; file-list counts
reflect the eight remaining visible manufacturing files. Slicing results and
printing parameters remain accessible. The original projection bytes and
provenance remain in the archive, unchanged. Useful toolpath inspection is
deferred until richer retained data and an appropriate viewer are available.

Verification: 47 focused Python tests and eight Chromium tests passed. Both
real-case ZIPs were regenerated and checked offline after relocation. Tests
assert the absence of projection navigation, correct activity file counts,
continued slicing/settings access and preservation of the projection bytes.
All 22 manifest entries and their digests remain verified. The generic inert-SVG
security test still passes; unrelated images and supplied SVGs are unaffected.

## Supplied Inputs and Reassembled Context (2026-09-17)

The input overview no longer has a detached aggregate "Review all" action.
The real case shows its request followed by all three supplied files. The
summary counts only the supplied prompt, image and two documents. Reassembled
context is accessible through its own disclosure, without being counted as
another original input. The run-input drawer likewise separates reconstructed
context from supplied document groups. No input bytes or relationships changed.

Larger supplied sets show three entries with a counted inline disclosure for
the remaining inputs directly below the list. Expanded entries open their
existing detail views; complete input search remains available in the swimlane
input drawer. The 27-input case verifies all 23 remaining entries, keyboard
expansion/collapse and file access at 944, 702 and 390 pixels.

Verification: 47 focused Python tests and eight Chromium tests passed. Both
API-generated real-case ZIPs were relocated and checked offline, including all
22 manifest entries/digests, constituent-source access and separate context
grouping. The 909-pixel input overview screenshot was visually reviewed:
`live-campaign/engineering-review-supplied-inputs-909.png`.
