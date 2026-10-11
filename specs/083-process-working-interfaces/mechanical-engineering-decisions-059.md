# Decisions needed to finish the engineering demonstrations

10 October 2026. The options below were initially proposals. The user subsequently
accepted **Option B: create a separate 130 mm variant**. Implementation and
manufacturing qualification remain pending. Existing runs, the original 75 mm
design and its evidence remain unchanged.

## Accepted decision, 10 October: separate 130 mm shelf variant

The user's exact response was: **"Create a separate 130 mm variant"** to the
choice between the company study and the separate supplier-targeted variant.
This authorizes the proposed Option B below: a new accepted source/intent with
130 mm shelf depth, the existing 60 mm rear wall, and the specified front-datum
adjustments. Preserve 110 mm width, rear slots, root radii, stock/bend rules and
all other original requirements. Do not overwrite or resume the protected
75 mm source or run. A new isolated revision and run are required.

Recheck the applicable current manufacturing limits before CAD. This geometry
decision is not supplier approval, a review of future artifacts, a waiver of
other checks or permission for physical manufacturing or supplier contact.
Option A was not accepted. The swim-lane location question remains unanswered.

Initial reference recheck after that decision: the supplier's current
[CNC bending page](https://sendcutsend.com/services/cnc-bending/) still states
the 2:1 sheet-metal base/flange rule for U/C channels (retrieved10October).
The nominal130/60 ratio is approximately2.17. This arithmetic is only a planning
check; actual flange/base definitions, stock-specific bend specifications,
clearances and all other applicable constraints still require verification for
the new model. No supplier acceptance has been obtained or inferred.

**Later priority clarification, 10 October:** PPT/deck work is deferred and is
excluded from the active goal. The historical presentation continuation below
does not authorize resuming it. The dock choice was subsequently accepted as
Option B; the swim-lane location remains unresolved. Independent shared Wright fixes and the concise product-testing
handoff continue under the revised saved goal.

## Sheet-metal wall dock

The accepted [R4 company revision](../../tests/datasets/engineering-workflows/scenarios/sheet-metal-supplier-handoff/01-barcode-reader-wall-dock/company-fabrication-capabilities-r4.md)
allows three supplier confirmations to remain open during nominal CAD work, but
explicitly keeps a known applicable supplier hard-limit conflict as a pre-CAD
blocker. It retains a75mm shelf and60mm rear wall.

The supplier's [current CNC bending page](https://sendcutsend.com/services/cnc-bending/),
retrieved10October, states under Flange requirements:

> Sheet metal: base must be at least 2x the flange length (2:1 ratio)

The referenced channel FAQ redirects to that page. The nominal75/60=1.25 ratio
does not meet2.0. The company's candidate gooseneck equipment does not establish
this supplier's acceptance. The previous exact intent and run remain held.

Two concrete new-revision options are available:

| Option | New accepted scope would say | Retained requirements and deliverables |
| --- | --- | --- |
| **A — Company fabrication study, original geometry** | Produce and verify the original geometry against the declared company equipment. Carry the supplier ratio conflict as an explicit failed supplier assessment, rather than a blocker on company CAD construction. No supplier-compatible-design claim. | Original110×75shelf,60rear,12lips, slots/notch, selected stock and native sheet-metal rules. NativePSM, foldedSTEP, true developedDXF, drawing and inspection package. Every applicable company/native check remains mandatory. Supplier release staysHOLD. |
| **B — Supplier-targeted geometry revision** | Increase outside shelf depth from75to130mm for a new variant; keep the60mm rear. Move the front lips and20mm-deep notch with the front datum; retain110mm width, rear slots, root radii and all other requirements. Recheck all current supplier limits before CAD. | Existing75mm revision preserved. A new intent, exact review, native model, measurements, flat pattern, drawing and simulation-only handoff are required. The proposed130mm depth is not a supplier approval or a promise all other checks pass. |

OptionA changes the timing/scope of the supplier gate and needs the user's
acceptance because R4 explicitly forbids proceeding with that conflict.
OptionB changes a protected dimension; the user's later response above supplies
that acceptance for a separate variant. A synthetic integration-test review
cannot authorize additional requirements revisions.

The original supplier-targeted 75 mm job remains blocked and preserved; its
missing native deliverables cannot be counted as complete. The newly authorized
130 mm variant has not yet produced or qualified those deliverables. No supplier contact,
file upload, order or physical manufacturing is proposed.

## Existing swim-lane tools

The located Feature079 FirstPartyDraftCanvas and DraftProjection implement phase
columns with ports and relationship lists. Feature080 deliberately removed
mandatory phase stripes from the refined editor. Searches of this checkout and
retained editor/dashboard worktrees have not identified the separate reviewed
responsibility/swim-lane capability requested for the engineering examples.

Please identify its branch, file, screenshot or workspace entry. That will let us
reuse the actual tool and connect it to current blocks and exact run evidence.
The explanatory lane diagrams in the current deck are explicitly illustrations;
they do not prove reuse of the product capability.

## Independent work still possible

Continue the remaining negative/lifecycle coverage and the full requirement audit.
Perform final fresh wheel and thermal journeys after implementation changes settle.
The final two-job presentation is deferred and excluded from the active goal.
Readiness fixes057/058 are verified in their documented scope;
they do not resolve either decision here.
