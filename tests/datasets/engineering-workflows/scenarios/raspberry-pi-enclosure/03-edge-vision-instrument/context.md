# Edge-vision instrument enclosure

## Business and design goals
Northline is exploring a small computer housing for a fictional tabletop optical-inspection station. The prototype connects only to low-voltage computing equipment and does not perform personnel protection, emergency stop, or machine interlock functions. A charcoal body, aligned vent rhythm, crisp chamfered edges, and a single narrow light bar should make it look like a deliberate instrument. Prototype quantity is three; no production-release decision is implied.

## Source research and interface rules
Retrieve the manufacturer-controlled Raspberry Pi 5 mechanical drawing and relevant connector/cooling documentation. Record revision/digest/date evidence and list unresolved accessory dimensions. Board geometry must come from that evidence, not from the attached block sketch. If an actual fan is selected later, replace the synthetic curve with retrieved vendor data and issue a new design revision; the current curve is not a real product rating.

The enclosure envelope is 145 mm X by 110 mm Y by 48 mm Z. Front face is Y=0 and rear connector face is Y=110. Nominal shell walls are 2.5 mm PETG; use an assumed 0.20 W/(m K) for this comparison. Maintain a 22 mm deep rear cable-service channel without blocking a nominal 85 by 56 mm board silhouette. Verify actual board/cable fit after research. A 5 by 28 mm front status-light opening lies at X=100..128, Z=18..23; optical performance is not analyzed. Four underside fasteners and two sliding service tabs are preferred; tabs need 0.30 mm nominal clearance per side, explicitly unvalidated for fit.

## Flow and heat model
Ambient is 30 degrees C. Total synthetic internal heat is 11 W: 9 W from a board patch and 2 W from a power-interface block. Use thermal-loads.csv coordinates relative to a board-local origin and map that frame into each CAD alternative explicitly. A nominal 30 by 30 by 10 mm fan envelope sits behind the front inlet. fan-curve.csv supplies an invented static-pressure curve in Pa versus volume flow in cubic metres per second; interpolate monotonically without claiming measured fan performance. Do not substitute a constant velocity silently. If the backend cannot use the curve, record a bounded single-flow assumption as a different case.

Both variants require 900 square mm nominal inlet opening and 900 square mm outlet opening before grille obstruction. Variant A is straight-through with no guide. Variant B adds a curved 1.5 mm guide wall with a minimum 4 mm clearance to the board/component keepout and no contact with the case lid. Keep the fan model, heat loads, domain extents, and mesh strategy comparable. Project target is maximum source-patch temperature below 68 degrees C with the lowest practical pressure loss; it is an internal design objective, not a published Pi limit.

## Review and limits
Retain a source-separated design document, both editable CAD alternatives, STEP exports, corresponding fluid domains, solver fields, and comparison data. Record assumptions for turbulence, buoyancy, radiation, wall contact, and fan direction. No machine-protection, EMC, thermal qualification, noise, ingress, or electrical-safety claim is authorized. Automated existence checks are distinct from later engineering validation. No supplier communication or hardware dispatch is part of this pack.

## Campaign recovery notes

Attempt035 was held by the pre-dispatch storage guard and is not a workflow result. Attempt036 verified the corrected 30 by 30 mm fan and outlet faces in the actual exported fluid domains, then exposed a compiler/contract mismatch: the CAD authoring contract included bounded inspection provenance under `evidence`, while the fixed compiler rejected that key. A fresh attempt must retain this provenance and use the closed compiler schema; arbitrary source or dictionary fields remain forbidden. Attempt037 is the current fresh recovery run and its output credit depends on the normal expected-file checks only.

Attempt037 completed all CAD authoring and independent output inspection but stopped before CFD when Hermes rejected the next model request for `workflow_context_limit`; the 32-call inspection task retained too much per-file observation for the next stage. The next fresh attempt uses an 18-call inspection budget for the 16 expected CAD/contract files. No output credit or content-validation credit was assigned.

Attempt038 reached AgentCAD after source research, approval and source
authoring, but its generated source placed the PETG floor at Z=2.0..4.5 mm.
The resulting fluid shape measured zmin=4.5 mm and AgentCAD stopped before any
expected export. The next source must use a Z=0.0..2.5 mm floor and preserve
the fixed final fluid bounds, with the 18-call scoped inspection budget.

Attempt039 regenerated valid CAD and completed its 18-call export inspection,
then stopped before CFD when Hermes rejected the next request for
`workflow_context_limit`; inline contract pages made the retained inspection
too large. The next attempt uses identity-only inspection (`includeText=false`)
while the full contracts remain durable for the compiler.

Attempt040 then produced valid CAD and compact inspection but hit a stale
long-lived compiler process at CFD preparation; that server was restarted via
the MCP lifecycle API. Attempt041 passed read-only preflight but was stopped by
the workspace storage guard before dispatch (about 49 MiB free versus the
256 MiB requirement). No engineering operation or output was produced. The
storage cache repair is complete; preserve attempts040-041 and use a fresh
attempt with the same geometry, contract and identity-only inspection rules.

Attempt042 passed the repaired storage preflight, completed native CAD and
identity-only inspection, and reached the restarted compiler. The compiler
rejected the authored evidence because domain bounds were a six-item list and
face records used `area_mm2`, `matching_count` and `selected_face` aliases.
No CFD mesh or output was produced. The authoring prompt now requires the exact
named-key evidence objects; preserve attempt042 and use a fresh attempt.

Attempt040 used the identity-only inspection and again produced valid native CAD
with the required fluid lower plane. It stopped at CFD preparation because the
API-managed fixed compiler process had imported an older module that did not yet
allow the bounded `evidence` object. The process was restarted through the
normal MCP lifecycle API after the failure; preserve attempt040 and use a fresh
attempt to exercise the patched compiler. No mesh or output credit was created.
