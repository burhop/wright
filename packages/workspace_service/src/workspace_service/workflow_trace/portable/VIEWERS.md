# Standalone Evidence Viewers

Rebuild the checked-in PDF and Markdown bundles from the repository root:

```sh
npm ci --ignore-scripts
node scripts/build-workflow-trace-pdf-viewer.mjs
node scripts/build-workflow-trace-model-viewer.mjs
```

The pinned build-only dependencies are in the root package manifest/lockfile.
Python exports consume the generated JavaScript directly; recipients need no
Node installation, network service or Wright application.

PDF.js renders the original retained PDF bytes into a canvas. Its worker,
character maps and standard fonts are embedded. The worker is bundled as a
classic script because Chromium rejects module workers at file origin.
No document JavaScript, active annotations or XFA forms are executed. WASM
decoders and external resource fetching are disabled; unsupported or password-protected
documents fall back to the original download. The canvas is a visual preview,
not a selectable/searchable PDF text layer.

PDF originals must be included in the export before they can be embedded.
Limits are 16 MiB per PDF, 32 MiB per report and 12 million canvas pixels.
Oversized PDFs remain downloadable. Workers/render tasks are disposed on
navigation and dialog close. Libraries and font licenses are bundled under
`assets/licenses/` and hashed separately from engineering evidence in the
manifest's `viewer_licenses` list.

The PDF frame is size-contained with a stable scrollbar gutter. Resize handling
observes the frame's border box and skips unchanged page/zoom/size requests.
Each replacement page is rendered into a detached canvas and published only
after completion; zoom, resize and canceled requests do not clear the visible
drawing. The previous page remains visible with the viewer marked busy until
the requested page is ready. Pending resize work is canceled when closing.

Markdown uses micromark with GFM tables, with raw HTML and dangerous protocols
disabled. Image URLs are made inert before inserting the document; uniquely
matched local document links open retained evidence. Unresolved relative links
are not turned into broken or external requests.

Reference APIs: [PDF.js examples](https://mozilla.github.io/pdf.js/examples/)
and [PDF.js API](https://mozilla.github.io/pdf.js/api/draft/module-pdfjsLib.html).

Regression coverage is in `test_workflow_trace_export.py` and the real-campaign
`workflow-trace-campaign-visual.spec.ts` file-origin tests.

## Activity Geometry

The bundled Three.js STL viewer uses retained mesh bytes, not generated example
geometry. Each activity occurrence exposes its own meshes, including intermediate
geometry that is not a principal final deliverable. Inspection records may expose
an existing mesh when their SHA-256 uniquely identifies that retained document.
Different occurrences are not collapsed into a single model history.

A single-pass CAD-source-authoring activity may show a subsequent, single-pass
CAD activity's geometry as explicitly labeled later-run context. This does not
add that mesh to the author's outputs or establish a source-version-to-model
relationship. Multi-pass authoring does not use this contextual association.

Viewers provide orbit, zoom and fit-to-view. Model extents determine framing at
the actual container aspect ratio. Inline mesh limits are 8 MiB per model and
32 MiB per report, with principal models prioritized. Geometry exceeding those
limits keeps its original-file access in full-data exports. Three.js is bundled
offline and its license is included in `viewer_licenses`.

STEP and 3MF originals are not decoded by this viewer. A useful retained preview
can be displayed, but absent previews are not fabricated or produced by rerunning
CAD source. These coverage gaps are tracked in PEX-011 of the feature's process
execution improvements backlog.
