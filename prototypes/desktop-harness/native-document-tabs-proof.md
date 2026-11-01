# Native document tabs: bounded proof

Date: 2026-10-26. This is an opt-in experiment, not general file-viewer support.

The intended journey is to open a workspace file in its own OpenAI desktop tab,
using the shared Wright workflow editor for `.wflow` and existing compatible
viewers for other formats. The desktop owns the outer tabs; Wright retains
workspace identity, accepted source, drafts, recorded runs and evidence.

## Current observation — 27 October 2026

The user now directly confirms the prepared A and B files show Wright workflow
**diagrams** in separate native desktop tabs, and the retained PNG shows an
**image**. Two actual desktop screenshots are retained with the relayed report
under the main repository's
`.local-run/desktop-usability-evidence-20261026/native-observation-20261027/`.
Actual 0.26 receipt records resolve both exact manifest paths/source hashes and
report opened/rendered/activated stages. Those stage reports are self-reported;
the user observation/screenshots supply visual evidence. No save or execution
was performed. Close/reopen/draft retention in the actual host remains unverified.

Both workflows required the normal host file-access prompt, which the user
accepted. The tabs share the generic caption “Wright workflow file”; breadcrumbs
distinguish A/B. General file support is still restricted by the proof manifest.

The user rejects excessive Wright-owned UI above the canvas. The focused
[toolbar correction](native-toolbar-usability-20261027.md) reuses existing editor
composition and keeps host tabs. Earlier observations below are historical and
do not supersede this new evidence. Native rendering is proved for the fixtures;
layout usability and general integration acceptance are not established.

## What this experiment establishes

The user directly confirmed that three requested native file tabs appeared on
Windows, but reported text instead of the expected viewers. Multiple native tabs
are therefore observed; the custom workflow renderer and image display are not.

The opt-in `--native-file-tab-probe` adds the documented file entrypoint for
`.wflow`, a three-file launcher and bounded diagnostic receipts. It resolves a
file through host-supplied `openai/resource` metadata and an exact local manifest.
Opaque resource URIs are not paths or authorization. Existing Wright source,
draft and process clients remain the owners; this adds no executor or file-save
bypass. Normal bridge startup does not register the probe.

**Test restrictions:** registration covers the extension, but the manifest only
allows `native-tab-a.workflow.wflow` and `native-tab-b.workflow.wflow` in the
disposable workspace `Native document tabs test 2026-10-26`. Other native `.wflow`
opens fail closed. Accepted saves change the fixed source pin and prevent later
probe resolution. For this proof use unsaved draft edits only; do not save or run.
The normal Wright panel remains available for other workflows.

## Qualification

Candidate: named plugin `wright-desktop-gb10-prototype` 0.24.0.
Compiled UI SHA-256:
`a841f4e8f3969a99adffa53e6ada7d9da093b1c1607fca18ce8f98de0f130353`.

| Check | Result | Boundary |
| --- | --- | --- |
| Three separate native file tabs | PASS | Direct user observation on Windows; content reported as text |
| File-handler metadata, resource bytes and unchanged existing tools | PASS | Actual candidate MCP command; 56 existing tool contracts preserved |
| Exact file/path/source binding and rejection of missing or changed scope | PASS | 47 server/probe tests |
| Two workflow editors, independent drafts, explicit draft recovery | PASS | Compiled candidate, real MCP/backend/source/draft owners; Linux simulated host |
| Accepted sources, revisions and run histories preserved | PASS | Same simulated journey; no accepted save or engineering operation |
| Retained PNG bytes render | PASS | Simulated host only |
| Narrow panel after expanded draft recovery | FAIL usability | Stacked headers/details and retained canvas viewport obscure the graph |
| Actual custom viewer, native image display and native draft close/reopen | UNVERIFIED | Requires observation with this file handler loaded |
| Selected retained-run restoration in file tabs | UNVERIFIED | Disposable copies have no runs; no historical run was changed |

Local evidence is indexed in
`.local-run/native-document-tabs-20261026/`, including `candidate-024.json`,
`candidate-024-protocol.json`, `native-file-open-baseline.json`,
`receipt-provenance.json`, and `simulated-file-viewers-e/REVIEW.md`.
The last file links the screenshots and complete browser report. Earlier failed
attempts remain retained and explained. Simulation uses a separate receipt sink
from the actual host; an accepted open request is not visual acceptance.

## Next observation

After the candidate is loaded by the desktop, open **Test Wright native document
tabs** and use **Open all three**. Verify A and B show the workflow diagram rather
than source-only text. In A, make an unsaved title edit in Source and apply it to
the draft, switch to B and back, then close/reopen A and explicitly resume its
preserved draft. Do not Save, Check readiness or Run. Confirm B remains distinct
and the retained PNG displays. A stale conversation may still expose the older
plugin; record that boundary instead of claiming a new renderer was loaded.

## Engineering viewers: reuse decision

The user explicitly directed reuse of existing compatible open-source viewers.
Do not implement STEP, DXF or other CAD parsers/renderers in Wright. Keep the
integration limited to file selection, scoped bytes, host lifecycle and styling.
Reuse the same selected viewer in Hermes and the desktop where compatible.

Preferred candidate for multi-format 3D is
[Online 3D Viewer](https://github.com/kovacsv/Online3DViewer), whose published
import list includes STEP, IGES, STL, OBJ, 3MF, IFC, BREP and FreeCAD. Its
[EmbeddedViewer API](https://kovacsv.github.io/Online3DViewer/Class_EmbeddedViewer.html)
is intended for embedding. The project declares MIT licensing; transitive
libraries and bundled assets need their usual version/license inventory.

DXF is absent from that published format list. Evaluate a dedicated existing
component such as [dxf-viewer](https://github.com/vagran/dxf-viewer), which declares
MPL-2.0 and documents limitations around dimensions, styles and layouts. Do not
claim drawing fidelity from the extension alone. Reuse existing Wright document,
image and STL viewers where they already satisfy the journey.

These are researched candidates, not installed or qualified CAD dependencies.
Before selecting versions, test representative retained STEP/assembly and DXF
files, units, colors/layers, dimensions/text, WebGL/WASM/worker loading, resizing
and memory cleanup within the supported desktop sandbox. Prefer locally packaged
engines with scoped file bytes; do not upload engineering files to a public
viewer service. Keep unavailable formats explicit. Visual rendering does not
replace engineering validation or exact-output verification.

## Protocol sources

- [Official OpenAI extension guidance](https://developers.openai.com/plugins/build/extensions)
- [Pinned official extension specification](https://github.com/openai/mcp-extensions/blob/36f8b38df179144b44d157133bbc5f7c6e353ace/docs/spec.md)
- [Official native file-open wrapper](https://github.com/openai/mcp-extensions/blob/36f8b38df179144b44d157133bbc5f7c6e353ace/typescript/src/app/files.ts)

The checked upstream SDK source is `@openai/mcp-extensions` 0.2.1. No SDK upgrade
was needed for this proof: the launcher uses its documented extension method.

## Narrow-panel follow-up, qualified separately

Successful explicit draft recovery now closes its chooser and focuses the
summary. Failed recovery keeps the chooser open. This uses the existing draft
generation and owners; it changes no save, restore, permission or run contract.
The isolated actual-owner journey verifies independent A/B drafts, accepted-source
and history preservation, keyboard focus, a 456px canvas in a 480×850 viewport,
and all nodes entering the viewport after the user's existing **Fit workflow to
view** action. The simulated-host screenshots and receipts are under
`.local-run/native-document-tabs-20261026/narrow-followup-b/`.

This follow-up is not installed: 0.24 remains frozen for the fresh native test.
The fresh chat **Wright native workflow tabs test**
(`01a17a03-e0bd-7be3-8d1a-c155db1cc3b9`) exposes the new probe tools and queued
the three opens, but has no file-entrypoint receipts or direct visual acceptance
yet. Source/diagram density and native viewer behavior still need qualification;
the focused recovery correction does not establish a finished narrow UI.
