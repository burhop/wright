# Feature 084: A useful first engineering process

**Date:** 23 October 2026. **Status:** Accepted by goal submission; implementation active.
**Confirmed scope:** one complete first-contact journey on native Wright through
Hermes, plus one measured reduction in quality-work cost. The user selected a
mainstream replacement handle/foot job. The user submitted [the goal](implementation-goal.md)
and accepted the detailed implementation scope below on 23 October 2026.

Read [the discussion record](../../docs/design/first-contact-delivery-brief.md),
[plan](plan.md), [tasks](tasks.md), and [current progress](progress.md).

## User and outcome

An engineer or technically capable maker wants to replace a broken drawer handle,
check the important dimensions, and prepare an inspectable 3D-print package.
They should understand the job before installing tools or starting expensive
work. Wright coordinates substantive geometry and slicing tools, validation,
decisions, and a useful correction; producing a plausible shape alone is insufficient.

Use the existing [repair-cart drawer handle assignment](../../tests/datasets/engineering-workflows/scenarios/printed-replacement-part/02-repair-cart-bow-handle/context.md)
and its supplied sketch, request, and scenario metadata. This is an original
fictional sample, not a photograph or evidence of a real repair. Preserve its full
requirements, including 96 mm bolt spacing, M4 clearance, finger clearance, bow
features, PETG/P1S profile, two-orientation comparison, and real support evidence.
The selected provider produces the engineering files. Physical fit, strength,
printing, and certification are outside the demonstrated digital preparation.

## User stories and acceptance

### P1: Understand the job and get ready

**AC01 — Explore without MCPs.** From the ordinary workspace, open the starter,
see the supplied intent and an inspectable example outcome, and understand each
tool's contribution. Exploration requires no model call, provider execution,
credentials, or new MCP installation. Distinguish supplied sketches, recorded
results, and live results. Recorded results need actual retained provenance;
fresh handle evidence must be obtained before claiming a recorded handle success.

**AC02 — Resolve intent early.** Identify the expected deliverable and supplied
measurements, expose unresolved required inputs, and show the visual design basis.
A user can correct it before downstream preparation. A vague image request cannot
silently authorize an expensive engineering chain or pretend to establish scale.

**AC03 — Set up this job.** Explain only the selected process's missing tools,
models, profiles, and host prerequisites through existing readiness and catalog
mechanisms. An unavailable or incompatible capability has an actionable reason;
it cannot appear ready because discovery or installation succeeded.

### P1: Run, inspect, and correct

**AC04 — Bounded work.** Before a long stage, show the intended work, configured
limits, and available time/cost estimates with their basis. Unknown cost stays
unknown. Distinguish estimates from enforced limits and identify spending outside
Wright's control. No arbitrary whole-program budget manager is required.

**AC05 — Actual engineering.** In a fresh run, geometry creation/repair feeds the
actual independent slicer. Inspect source/repaired geometry, measured dimensions,
orientation/support consequences, profile identity, and the actual print package.
Use a handle-specific requirement-to-check mapping; focus-wheel proof cannot
qualify the handle. Retain failures, exact output identities, and declared reviews.

**AC06 — A useful change.** Make one change already permitted by the assignment,
such as the selected preparation orientation, with a visible impact explanation.
Change the accepted preparation choice, bind a new final package, invalidate its
affected assessments/reviews, and record what actually reran. Merely opening the
other already-computed result does not satisfy this case. This proves a
preparation correction, not inexpensive arbitrary geometry/design-intent edits.
Use the existing bounded correction or explicit new-revision/new-run mechanism.
Retain unchanged geometry only with valid identity/dependency evidence; regenerate
and recheck affected preparation outputs. A full rerun, if required, must be
disclosed. General minimal recomputation is not claimed by this feature.

**AC07 — Return and recover.** Close/reopen the working tab and reconcile the same
durable run without duplicate execution. Demonstrate a missing capability and a
failed/timed-out operation with useful recovery information. Declared input waits
and reviews resume the same run; uncertain external effects are not blindly retried.

### P2: Learn and explain a problem

**AC08 — Local diagnostics.** Link user-visible errors and delays to their exact
run/stage and retained evidence. Offer a reviewable, redacted local diagnostic
export through existing owners. No automatic upload or general session recording.

**AC09 — Reproducible introduction.** Provide an installed-native guide and a short
local walkthrough video or screen recording of the actual journey, including a
correction. Label recorded/live evidence and limitations. Publication is separate.

### P1: Deliver without unnecessary verification cost

**AC10 — Measured saving.** Deliver one measured reduction in an identified QA
stage's elapsed time or runner cost while retaining its required unique coverage,
environment claims, thresholds, and failure detection. Report baseline/candidate
conditions, repetitions, and uncertainty. Static overlap or fewer commands alone
does not establish the claimed runtime saving.

**AC11 — Preserve shared behavior.** Exercise changed shared mechanisms against a
substantially different existing workflow. Preserve the refined editor, existing
reviews, exact-output validation, and common-view fallback. Source inspection,
fixtures, live-provider proof, installed UI verification, and user acceptance are
separate evidence classes.

## Boundaries and product acceptance

Apply V1–V7 and the linked platform documents. Backend services retain state,
execution, validation, review, recovery, and permitted actions. The working view
and editor share one accepted process/run; no second executor or status authority.
Saved interfaces retain versioned bindings and compatibility checks. Reuse
existing independent MCPs; vendor fixes stay external.

The first qualified native OS/architecture, Wright/Hermes/model/provider versions,
and prerequisites must be recorded at M0. The current planning host is Linux
aarch64; that observation is not compatibility qualification. Required new
capabilities or material engineering changes must be surfaced rather than
silently replacing the assignment. Local diagnostic export is the default.

The user requires Wright to improve engineering results beyond a generic Astra
prompt. The [comparative-demonstration requirement](../../docs/design/first-contact-delivery-brief.md#comparative-demonstration-requirement)
defines the follow-on Pi case proof. Feature 084 creates the complete first journey
and exact evidence needed for evaluation; it cannot declare comparative superiority
or customer acceptance without that evidence. A tie/loss remains a product gap.

## Measurable completion

All AC01–AC11 have evidence on their applicable subjects; one fresh handle process
and a meaningful correction are demonstrated; no live operation occurs during
recorded exploration; reopening causes zero duplicate submissions; missing
prerequisites block before dependent work; one QA saving is measured. Record
time to first inspectable intent, live outcome, and correction without inventing
a universal speed or price promise. User acceptance remains explicitly open.

The customer pilot, Pi comparative execution, broader platform/distribution
support, wholesale example rewrites, general DAG recomputation, physical actions,
publication, and production release are outside this first goal.
