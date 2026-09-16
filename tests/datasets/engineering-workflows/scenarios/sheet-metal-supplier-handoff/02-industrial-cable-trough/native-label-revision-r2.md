# Fieldbar native geometric-label decision, revision R2

FB-MFG-12-R2 is a fictional human-uploaded decision dated 2026-09-12. It
supplements R1 only for the native CAD library mapping. Preserve the original
brief, mounting table, company policy, R1 stock bounds and every geometry/DFM
requirement. Review the exact revised intent before creating the part.

The selected native Solid Edge installation was read without creating a CAD
document. Its 137 steel entries included the exact name
`Steel - Unalloyed:1.0301 , C10` in library `Materials-DIN`. The retained
read-only observation is `.local-run/feature-081-live/sheet-material-r1-probe.json`
(2026-09-12T16:34:16.645065+00:00); the second page is separately retained in
`sheet-material-r1-probe-page2.json`. These are setup observations, not workflow
results. The workflow must perform its own fresh inventory/readback.

For geometry generation only, I explicitly permit that exact unique C10 library
entry as this prototype's CAD label. Record the material decision as
`geometry_label_only`. This is an internal modeling choice, not a claim that
C10 is the supplier's cold-rolled stock, a grade substitution approved for
fabrication, or a verification of properties. Do not infer a rolling condition,
strength, density, coating condition, stock certification or grade equivalence
from the native name. Do not create a library entry or change its name.

This explicit mapping supersedes R1's requirement to establish the native
entry itself as the selected supplier's low-carbon steel class before geometric
CAD. It does not change the purchased-stock request: select actual currently
sourced cold-rolled low-carbon steel within R1's bounds, with that exact stock's
supported bend rule. Keep requested material, sourced supplier stock and native
geometric label as three separately attributed fields. Their equivalence stays
unverified. A missing/ambiguous native name or unsupported supplier row still
blocks; missing physical properties cannot be invented.

Keep the existing 400/80/60/20 mm folded dimensions, four bends, every slot,
service clearances, finish unknowns, exact intent approval, independent native
checks, correction limits, developed-DXF verification and both simulator gates.
No mandatory supplier or geometry requirement can be waived by this label
decision, test-auto approval or manufacturing HOLD. Quantity remains six.
The simulated handoff retains actual stock/rule and native readback with
`manufacturing_release=HOLD`, `supplier_acceptance=unverified` and the material
equivalence gap. No property-dependent physical claim, real supplier upload,
cart change, order, payment, production release or communication is authorized.
