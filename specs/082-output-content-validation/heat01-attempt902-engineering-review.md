# Heat 01 — corrected thermal basis review

The original copper-case scope error is removed. **Do not approve the replacement
yet:** it contains one remaining contradiction about the mesh-refinement check.

## The engineering job

Compare two flat aluminum conduction straps for a fictional sign controller.
Both are 100 mm long and 2 mm thick; widths are 40 and 60 mm. Carry 4 W to a
25 °C cold face while keeping the hot end at or below 45 °C. No contact resistance,
convection, holes or physical testing is part of this idealized case.

The analytical screen predicts 50 °C for the 40 mm strap and 41.667 °C for the
60 mm strap. These calculations are correct for the stated model; they are **not
finite-element results or final design approval**. CAD and numerical analysis
have not run in this attempt.

## What needs correction

Section 8.6 of the [generated basis](C:/Users/markb/wright-feature-081/engineering-workflow-demos/campaign/heat-spreader-sizing-01/attempt-902/artifacts/thermal-basis.md)
says the inputs provide no numerical mesh-sensitivity threshold. The existing
context and frozen validation baseline require the coarse-to-refined **hot-end
temperature-rise change to be at most 2%**, retaining both mesh identities.
The 2% analytical-agreement and 1% heat-balance requirements also remain fixed.

Recommended decision: **request changes**, retaining every existing engineering
input and limit. This would authorize the second bounded correction, not a new
unlimited retry or an engineering approval. The preparer now includes the exact
three numerical requirements from the pinned baseline; 15 focused tests pass.
No further attempt has been staged or dispatched while this decision is pending.

After an acceptable basis is reviewed, the process should create the actual CAD,
run the numerical thermal models, compare coarse/refined fields and heat balance,
and check the selected STEP against the analyzed design. None of those results
is claimed yet. No Solid Edge operation is involved.

## Traceability

Attempt 901 preserves the user's recorded request-changes decision and its
original files. Attempt 902 is unchanged and awaiting an actual human decision:

- Run: `a01fefe4badd4e6bb7418d4704f75a65`
- Checkpoint: `checkpoint-875a69002c5f61ec041f3b25`
- Subject: `d9a7b3eb2a0a3f58d1516fb422bc8ba2c3ab89d050f468d79ce142c89cedd7f5`
- Basis SHA-256: `78e2c8d1e5fe8e5e9578c0501899a6656193dee621779f15f3476c72c69463e2`
- Retry episode: `heat01-aluminum-basis-scope`; one correction used, one remains.
