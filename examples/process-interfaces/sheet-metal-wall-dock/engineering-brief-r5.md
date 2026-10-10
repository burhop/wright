# Barcode-reader wall dock — 130 mm variant verification plan

Prepared 10 October 2026 before new geometry. This supplements the original
[engineering basis](../../../specs/083-process-working-interfaces/mechanical-engineering-basis.md)
and applies the user's [R5 input change](shelf-depth-revision-r5.md).
Status: input preparation; no new engineering output has passed inspection.

## Engineer's job and tool handoffs

Prepare a fabricated aluminum dock for the fictional packing-bench reader,
quantity four. Solid Edge makes the native sheet-metal part and developed flat;
the independent DXF provider reopens the actual flat export; FreeCAD TechDraw
produces a dimensioned drawing from the exact folded STEP. Wright retains the
requirements, run, evidence, verification and declared reviews. Final supplier
preview remains a local simulation with release held.

| Requirement | Expected basis | Verification on the new exact revision |
| --- | --- | --- |
| Envelope and datums | Outside virtual-sharp 110 by 130 mm shelf, rear 60, split front lips 12 mm, R5 planes; all bends 90 degrees upward | Native face/feature observations plus independent STEP envelope; original nominal CAD comparison 0.05 mm and 0.1 degree, not fabrication tolerance |
| Wall interface | Slots at X20/90, Z38; 5.5 by 12 mm with R2.75 ends | Native edge measurements and drawing dimensions from actual geometry |
| Cable access | X46..64, Y110..130, R3 roots; no bridge across the split lip | Native topology and actual flat-contour correspondence |
| Reader layout | Centered 65 by 50 mm reference footprint, at least 6 mm side clearance | Datum/layout check; physical retention and support remain unverified |
| Material and stock | R1 complete current eligible 5052 stock row, T1.3..1.7 and inside R0.5..2.5; unique permitted installed label | Fresh public supplier source plus native material/rule readback; do not invent properties or temper equivalence |
| Development | R3 selected K controls; specified square relief and native flat settings | Measure selected native rule, relief dimensions and developed strip lengths; retain any supplier deduction discrepancy |
| Forming | R4 split-lip then rear sequence, actual surviving intervals, tool end access, current stock-specific supplier limits | Numerical criteria before CAD; actual model/flat distances after CAD; keep physical tooling and supplier acceptance separate |
| Native integrity | One continuous constant-thickness sheet-metal part, complete cuts/features, no slivers | Native inspection and exact exported geometry; tool success alone cannot pass |
| Deliverables | PSM, folded STEP, genuine flat DXF, inspection image, drawing and inspection plan | Same-revision identities/hashes, units, reopen and correspondence checks; independent DXF inventory is only part of the proof |
| Scope | Quantity4, requested bare/deburred finish, release HOLD | Exact local simulator receipts; no actual fabrication, supplier action, structural or anchor-capacity claim |

The original 0.42 kg reader and 15 N handling load are fictional design inputs,
not completed load tests. Preserve all uncertainty and physical validation needs
from the original basis. Record supplied facts, user decisions, delegated design
choices, retrieved supplier facts and native observations separately.

## Decision and invalidation rules

Use a new source, staged input set, baseline/profile and run. R5 supersedes only
the declared depth and dependent front/centered-layout coordinates. The original
75 mm process and artifacts retain their own status. A stock, geometry or rule
change invalidates affected intent, measurements, drawing, exports and reviews;
reuse no approval from the original run. Missing capabilities or failed checks
must identify the held stage and exact evidence. Keep a final actual engineering
review pending; synthetic test responses demonstrate software behavior only.

Use Wright's existing flowchart and common working view on the same durable run.
Any optional generated view must retain exact block/evidence links and the
common-view fallback. This example adds no executor, provider protocol or UI
status authority. Portable source retains the R5 body, original input references,
validation profile and its required dependencies.
