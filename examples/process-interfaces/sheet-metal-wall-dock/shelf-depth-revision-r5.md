# Wall dock R5 — separate 130 mm shelf variant

**Authority:** On 10 October 2026 the user answered “Create a separate 130 mm
variant” to the recorded choice in
`specs/083-process-working-interfaces/mechanical-engineering-decisions-059.md`.
This is an accepted input change for a separate digital design study. It is not
approval of an as-yet unproduced model or a manufacturing release.

## Input precedence and retained original

Retain the original scenario uploads, R1 stock selection, R3 CAD choices and R4
company capabilities unchanged. Apply this R5 after those documents, including
the original concept drawing and approved campaign brief. The original 75 mm
design, accepted source, run and evidence remain protected. Do not overwrite or
resume them. The old drawing illustrates the original design; its depth label
does not override this revision. Label new outputs **130 mm variant / R5**.

## Exactly what changes

| Definition | Original | R5 variant |
| --- | --- | --- |
| Outside virtual-sharp shelf depth along Y | 75 mm | 130 mm |
| Outside front datum | Y=75 mm | Y=130 mm |
| Front lip station | At original front | At new front; retain two 12 mm upward lips |
| Center cable notch Y interval | 55..75 mm | 110..130 mm; same 20 mm depth |
| Centered conceptual reader footprint, Y | 12.5..62.5 mm | 40..90 mm; same 50 mm footprint depth |

The footprint remains centered on the shelf as originally required; it is layout
reference only, not a cutout or evidence of physical contact/stability. Its X
interval stays 22.5..87.5 mm. Retain the 6 mm minimum side clearance.

Keep X=0..110 mm, rear outside plane Y=0, bottom outside plane Z=0, rear top
Z=60 mm, lip tops Z=12 mm, shelf inside Z=T, all bends upward and both sides
open. Keep the rear slots centered at X=20/90 and Z=38, width 5.5 mm, overall
height 12 mm, end radius 2.75 mm. Keep notch X=46..64, root radius 3 mm, and
the original external-corner treatment. Move the associated front reliefs with
the new front datum; recalculate native sketch offsets from actual T/R.

Retain quantity four, bare/deburred requested finish, the original loads and
excluded anchor/strength/physical-fit claims. R1 still selects actual eligible
stock and native material identity. R3 still controls K-based development,
relief construction, coordinate interpretation and flat-pattern settings. R4
still controls company forming assumptions and which supplier confirmations may
remain open. This revision supplies no new supplier exception.

## Recheck before CAD

Retrieve current primary supplier requirements and the complete eligible stock
row. Evaluate base/flange definitions using that source and the selected T/R,
not just the nominal arithmetic 130/60. Recheck the front flange minimum, rear
slots, interrupted bends, notch/relief interference, die-width cautions, blank
size, tool access and forming sequence.

Recalculate R4's throat planning expression with the new depth:
130+60+10=200 mm against the unchanged 300 mm capacity. The unchanged scalar
clearance checks and surviving straight bend intervals still apply. These
planning calculations are not native measurements, collision simulation or
physical brake trials. A known applicable supplier hard-limit conflict or an
unsupported mandatory requirement still holds CAD/affected downstream work.

## Verification and release

Before modeling, issue a new manufacturing intent with old/new requirements,
selected stock/rule, assumptions, sources and verification criteria. Review that
exact revision through the declared workflow step. Verify actual native geometry
and the exact exported files against R5; retain all failed attempts and bounded
corrections. Never edit an observation to match the requirement.

Required package remains native Solid Edge sheet metal, folded STEP, genuine
developed DXF, inspection image, dimensioned drawing and verification/inspection
documents. No polymer slicing. Only the original local simulated supplier
preview/handoff is permitted. Keep manufacturing_release=HOLD,
supplier_acceptance=unverified and physical_fabrication=not_performed.
