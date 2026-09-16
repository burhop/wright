# Sheet-metal concept revision review

Date: 2026-09-12. Initial concept-only proposal retained below as review history.

**Current decision:** the active `stock-selection-revision-r1.md` uploads prefer
stock-compatible geometry selected from actual retrieved supplier evidence,
within explicit fictional thickness/radius/relief bounds. The original requests
are preserved and no supplier rule is invented or transposed. These supersede
the adjacent unactivated concept-rule drafts; K=0.40 is not an active dataset
rule. Mandatory geometry/DFM gates cannot be waived by a release HOLD.
The new manifests and unchanged original-file hashes are recorded under
`tests/datasets/engineering-workflows/revisions/2026-09-12-sheet-stock-r1/`.
Source preparation now enforces attribution: supplier H32 is not an original
customer requirement, and absent properties not required for the explicitly
allowed geometric mapping do not become fabricated preconditions.
Fresh actual API instances will use attempt-003; prior attempts remain intact.

The three synthetic input packs can legitimately authorize a geometric concept
revision with an explicit internal bend rule while manufacturing release remains
on HOLD. The native recipe accepts independent thickness, radius, neutral factor
and relief dimensions. An installed material label is assigned and read back as
that label; it does not certify supplier stock or temper. This does not establish
that any of the three resulting geometries will pass native creation, independent
measurement or developed-DXF verification.

## Actual failed attempt

Case 01 attempt-002 reached the exact intent review and then stopped before CAD.
Its canonical run ID is `1f16e7d62f6e4cafb9eff6369aca85cb`. The original input
digest is `296f9c7198ef9a15e5d4f48ca5474e52fc0467f747797e9ab22ba7549cb8e77e`.
The source digest is
`d4eace008dedf0b29c600553f0b1e8e80b832c38c440b11ea1ece95a2d10044c`.

The observed installed material is exactly
`Aluminum Alloy:3.3523 , AlMg2.5, EN-AW 5052 `, including trailing whitespace,
from `Materials-DIN`. The result does not contain temper or physical properties.

There is also a source-attribution defect in the generated intent: section 12
and criterion V-39 call H32 a **requested** temper. The original case 01 prompt,
context and manufacturing policy request 5052 aluminum without specifying H32.
The installed-material task correctly says a 5052 label cannot prove H32, and
supplier research reports an H32 offering; neither creates a human H32 request.
The same distinction applies to case 03, whose original brief also lacks a temper.
A fresh intent must distinguish original requests, sourced offerings, observed
native identity and new explicitly supplied concept choices. Do not edit the old
intent or its accepted checkpoint in place.

The saved intent records supplier `.063 inch` data separately from the requested
1.5 mm/2 mm prototype: it reports K=0.42 for that supplier row, with its own radius
and relief requirements. This review does not independently reverify those
supplier values. They must not be transplanted to a nominal 1.5 mm concept as
supplier-approved rules. Current source retrieval remains mandatory in the next
workflow; missing supplier facts stay missing.

## Concrete proposed revision

The adjacent `sheet-metal-concept-addenda/` contains three draft human-uploadable
documents, one for each fictional company. They provide concept-only native
inputs: thickness 1.5 mm, inside radius 2 mm, neutral factor 0.40, square bend
relief width 2 mm/depth 4 mm. These are deliberately explicit synthetic design
choices, not material test results, standards or supplier requirements. Native
validation is still required; a syntactically accepted recipe is not proof of
manufacturability. Geometry checks and actual flat-pattern development remain
mandatory, including all cutouts, four trough bends, and both chassis parts.

The addenda supply a CAD comparison tolerance of 0.05 mm for nominal linear
geometry and 0.1 degree for nominal angles solely for this fictional concept.
Original minimum clearances, envelopes and required features remain hard
requirements; the tolerance cannot excuse a violation. These tolerances are new
human-input assumptions requiring the same exact intent gate, not hidden checker
defaults or supplier manufacturing tolerances.

For cases 01/03, the exact observed 5052 entry may label a geometric concept
without a temper claim. Case 02 is conditional: no case 02 native material result
was available in this review. Its next material inventory must find one unique
entry explicitly identifying the requested low-carbon steel class; the intent
must record exact spelling/library. A generic `steel` search hit, stainless or
tool steel is not authorized as a substitute. Missing or ambiguous identity
remains a blocker before CAD, not an invented mapping.

Case-specific provisions retain the dock's notch/contact-footprint conflict as
an acknowledged concept fit limitation, the trough's service clearance and
unresolved coating allowance, and the chassis's already supplied 75 mm keepout
resolution, styling, vent banks, corner/lid details and separate deliverables.
No feature may be dropped merely to get files.

## Native contract evidence

The selected immutable snapshot is
`.local-run/feature-081-live/sources/solid-edge-campaign-001/`.

- `src/CadMcp.Api/Recipes/CadSheetMetalRecipe.cs` declares material thickness,
  inside radius, neutral factor, bend relief width/depth, calculation method and
  exact installed material designation separately.
- `src/CadMcp.Core/Recipes/CadSheetMetalRecipeValidator.cs:253` requires positive
  lengths, `0 < neutralFactor < 1`, and calculation method `neutral_factor`.
- `src/CadMcp.Api/Recipes/CadSheetMetalRecipe.cs` declares per-step square relief
  and explicit corner treatment; geometry authoring still has to construct the
  actual features with supported operations and measured frames.
- `src/SolidEdgeMcpServer/Tools/CadMaterialTools.cs` forbids inferring unlisted
  temper/certification from the installed name. Native creation refuses an
  absent or ambiguous requested designation.

These local implementation facts support feasibility of an input-derived concept
recipe, not a claim that a particular recipe is already validated or created.

## Activation and evidence preservation

1. Preserve original prompt/context/policy/images/CSVs byte-for-byte and retain
   attempt-001/002 sources, intent, checkpoint and run evidence. Draft addenda
   do not change campaign fingerprints merely by existing outside the packs.
2. After review, copy each addendum as a new top-level uploaded Markdown file in
   its existing scenario directory; append it to `scenario.json.files.context`.
   Record its superseding scope and original manifest/file hashes in a revision
   ledger. Do not add an eleventh workflow or thirty-first scenario.
3. Run the existing observer dataset sync so the changed human-input manifest
   and bytes receive a new dataset digest while `dataset_revisions` retains the
   earlier registered revision. Use a fresh attempt and empty output directory.
4. Prepare and save fresh canonical source from an actual template instance,
   preserving all original stages. The existing preparer includes context files
   and CSVs; no recipe fixture or template-ID executor is needed. Explicitly
   instruct intent authoring to resolve source hierarchy, include the addendum
   and prevent supplier facts from becoming invented customer requirements.
5. Enroll the new source/input/tool-schema digests. The exact local intent review
   still precedes any CAD mutation; approval of old intent cannot authorize the
   new revision. No automatic retry of the already failed attempt.
6. Independent measured checks, bounded corrections, per-part exports and DXF
   verification remain intact. If those require unresolved supplier acceptance
   as a prerequisite rather than concept measurements, leave that step blocked;
   do not force a pass or relabel it merely because the addendum permits drafting.
7. Both external checkpoints remain separate exact test-simulator approvals.
   Set review/handoff metadata explicitly to `concept_only=true`,
   `manufacturing_release=HOLD`, `supplier_acceptance=unverified`, actual modeled
   stock/rule, and unresolved requested-versus-sourced differences. A simulated
   receipt may document this hold, but must never claim supplier compatibility,
   live price, purchase or production authority.

No active dataset, source, grant, receipt or dashboard was changed by this review.
No native CAD operation, enrollment or retry was performed. The proposed revision
requires actual execution evidence before any completion count can increase.
