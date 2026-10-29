# Replacement handle: editable desktop qualification draft

This is unfinished authoring work, not an executable or qualified engineering
example. It implements the intended journey as a saved Wright definition so the
remaining binding, review and presentation gaps have concrete subjects.

The original Printed02 prompt and context are embedded verbatim as input text;
the source dataset remains unchanged. Its 40 N load remains design intent, not a
validated strength requirement. The proposed FEA extension requires a separate
human-reviewed material/load/support/acceptance basis. No physical printing,
transfer or simulated success is performed.

The graph connects the specification and its review to CAD, exact geometry
checking, strength analysis and checking, repair/orientation/slicing, print-package
a final manufacturing-applicability check, a readable report before print-package
review, and an explicitly simulated receipt stage. The specification uses Wright's durable manual review. The local final-package draft uses its existing multi-artifact local-review declaration. Order edges express dependency, not approval authority.
No check is replaced with an AI assertion of success.

## Current evidence

- The existing source store accepts the definition. Current compiler readiness
  rejects the unbound CAD task: `WORKFLOW_NOT_READY`, “Create the editable handle
  and exports needs a supported execution type.”
- Saved through the actual desktop MCP in the fresh workspace named
  **Replacement handle — desktop engineering qualification**, revision 1.
  Exact identity is in `desktop-draft-receipt.json`. The saved digest matches
  the original local source-store digest. That receipt is historical: the
  reviewed draft was saved as revision 3 and is now at revision 4; original revision 1 remains in history. See the current round-trip evidence below.
- An editor-open request succeeded, but compiled-editor review subsequently
  found missing required fields and duplicate port identities in that original
  draft. The revised local source fixes both; its parse/save/reopen regression
  passes. Actual Windows rendering remains unverified.
- No process was prepared, started, resumed or approved. Historical subjects and
  the independent Windows pilot were untouched.

## Remaining binding work

1. The original `concept.png` and `context.md` are now uploaded through the actual UI into hash-addressed workspace paths; [exact receipt and qualification limits](../evidence/handle-reference-upload/README.md). Revision 3 binds that exact uploaded concept path and preserves original reference provenance.
2. Qualify and select the engineering tools. The separate isolated 036 workspace
   now has protocol-validated OASiS and offline slicing providers, enabled through
   Connections. This does not change the older installed workspace or grant tool
   invocation. SteveCAD sign-in and CAD binding remain outstanding. See
   [setup evidence](../evidence/candidate-036-provider-setup/README.md).
3. Bind exact geometry and strength profiles, including meaningful independent
   measurements, applicability and convergence. Qualify the bounded correction
   intervals against those exact outputs. Stage instructions describe the intent;
   executable correction edges are intentionally not invented before binding.
4. Prove the full run, real declared review, same-run continuation and full rerun
   through the candidate backend. Add a readable report and exact result previews
   as declared outputs. Do not replace this with another retained-block run.

The initial local draft used an unsupported approval edge for manual review and
was rejected. The corrected draft uses the existing order dependency; the review
step itself still owns the durable wait. Both local readiness receipts remain in
`.local-run/experience-review/handle-draft-readiness*.json`.

## Reviewed local revision

The current local draft follows reviewed dimensions rather than fixing downstream
CAD instructions to the initial 96 mm spacing. It carries editable model identity
into the report, checks whether manufacturing changes invalidate analysis, and
places the report before package review. The simulated receipt remains unbound
and cannot authorize a real printer transfer. All task bindings and independent
engineering checks still require qualification. The desktop revision-1 receipt
is preserved as evidence, not rewritten to claim these local changes are live.

## Desktop revision 3 input qualification

[Actual UI save/reopen evidence](../evidence/handle-source-roundtrip/README.md) records the exact source digest and visible 2/2 configured inputs. The original requirements are unchanged. Source correction preserved revision 1 and used the existing editor/source owner. Provider bindings and declared human reviews remain outstanding; configured inputs do not imply engineering readiness.

## Final-review authoring attempt and correction

The local draft now declares the seven-input final package review using Wright’s existing `local_review` / `review_only` binding. All seven inputs and upstream connections remain. The first attempt was **not saved in the desktop workspace**: the normal Source editor correctly rejected changing the step type and managed review declaration as an unsupported structural change. Desktop accepted revision 3 remains unchanged; its pending editor draft is preserved. The attempted UI path and screenshot are retained in `.local-run/experience-review/candidate-035/handle-review-02/`. Use a supported structural authoring path or qualify the missing edit capability; do not bypass the editor’s authority guard or discard review subjects. No workflow was run or approved.

The subsequent narrow editor correction now saves and reopens **revision 4**, retaining every review subject. [Evidence](../evidence/handle-review-authoring/README.md). The paragraph above records the earlier failed attempt; accepted revision 4 is current. No human approval or engineering execution is implied.

## Proposed analysis binding (not yet accepted)

The local source now proposes the isolated OASiS `run_simulation` binding with
per-run, per-attempt field and analysis-basis outputs. [Exact schema and image](analysis-binding.json)
record the selected provider. Its instructions require a reviewed material, load,
support and acceptance basis; missing values stop the work rather than becoming
assumptions silently accepted by the solver. This is not a strength qualification.

Neither accepted desktop source has been overwritten. Full readiness still rejects
the unbound CAD stage. Geometry and strength validators, repair/orientation/slicing
handoffs and bounded correction edges remain to be qualified. A protocol-valid
slicer alone does not fulfill the manufacturing stage’s repaired-mesh, orientation
comparison, print-package and preview requirements.
