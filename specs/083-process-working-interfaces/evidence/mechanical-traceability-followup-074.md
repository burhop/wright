# Existing engineering traceability exports, 10 October 2026

## Engineer journey and ownership

An engineer reviewing a drawing or process result needs to see which requirement
was checked, its source, the acceptance criterion, the actual observation and
the exact output involved. This follow-up collects the **existing Feature 082
exports**, using its existing readable formatter. It adds a static review index;
it adds no reporting application, validator, workflow executor or verdict.

[Open the review package](../../../artifacts/process-interfaces/083/20261010-engineering-traceability/index.html)
or [download the combined matrix](../../../artifacts/process-interfaces/083/20261010-engineering-traceability/combined-traceability.csv).

The six wheel assessments belong to run `79b02848cf4e481bbee3f7a26a9d19ae`.
The thermal assessment belongs to the separate regression run
`f01d057d9842441797ef7c803c3a2044`. Thermal does not replace the primary sheet-metal
assignment. The wheel retains 65 passed digital checks and one mandatory human
review hold; thermal retains 25 and one. No physical validation is claimed.

## Directly verified

- Seven actual authenticated, read-only export calls per format yielded 21
  original JSON/CSV/Markdown files. Each assessment is equal to its durable
  original, has the same typed digest and was current at export.
- All **117 traceability rows** retain their original fields, values, units,
  frames, sources, statuses and exact subject/assessment identities. The combined
  CSV adds only example, stage and run columns. Row count is not a count of
  independent requirements or tests.
- Seven readable documents are exactly the output of the existing
  `render_readable_markdown` function for those exported reports. The drawing and
  thermal field images are exact copies of their separately identified records.
- All 54 existing run records remain byte-identical. No Start, model/tool call,
  revalidation, answer, approval or external action was submitted.
- The index renders without broken images, horizontal overflow or page errors
  at 1280×900 and 768×1024; all 26 linked local targets exist. Overview, native
  stage, thermal stage and narrow-layout screenshots were visually inspected.
  The dense drawing/field previews remain context; their original full-resolution
  files and exact reports are linked for detailed inspection.
- Read-only resource inventory found all 62 managed presentations in the two
  isolated workspaces closed. The test FreeCAD/Blender sessions remain closed;
  the unowned Solid Edge session is untouched.

Private control receipts are under
`.local-run/process-interfaces-083/mechanical-engineering-20261008/`:
`engineering-traceability-export-074.json`,
`engineering-traceability-review-audit-074.json`, and
`review-resource-inventory-074.json`. Public content/render receipts and manifests
are in the linked package. A first render attempt could not locate a browser in
the restricted environment; using the already installed host browser succeeded.
No browser installation was needed.

## Limits and next work

This narrows M2.2/M2.3's evidence-access gap; it does **not** prove completeness
of every engineering requirement. The existing CSV omits explicit
`review_required` and measurement-uncertainty columns; those recorded fields are
in the exact JSON. The measurement contract defaults uncertainty to zero; a
recorded `0.0` must not be presented as physical measurement certainty. Scope
limitations and unexecuted physical tests remain applicable.

Currentness is an observation at export, not a permanent approval. A changed
output, source, profile or instruction requires the existing live currentness
checks. No UI binding, client/kit version or execution policy changed here.

The dock requirement decision/native deliverables, actual existing swim-lane
capability, remaining coverage audit and final two-primary-job presentation
remain incomplete. A broader read-only branch/source search still did not locate
the requested responsibility-lane implementation; phase columns and governance
lanes remain distinct and are not claimed as its reuse.
