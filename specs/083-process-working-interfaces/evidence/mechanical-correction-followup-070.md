# Native correction: current evidence and readable review (070)

10 October 2026. This checkpoint advances M2.11 and M4.3 and supplies a usable
comparison for M5. The full goal remains incomplete. It does not run CAD again,
answer a review, change accepted criteria or substitute a thermal example for
the required sheet-metal job.

## Engineer-facing result

[Open the illustrated correction review](../../../artifacts/process-interfaces/083/20261010-native-correction-review-verified/report.html).
It includes both original drawings, the exact failed and passing assessments,
native CAD and STEP downloads, the unchanged inspection profile, current Wright
captures and a three-step manual repeat. The separate full wheel/slicing example
is explicitly linked as a different run.

The original shaft basis requires a 6.00 mm round diameter and 5.20 mm across-flat
dimension. Applying the saved 0.20 mm round/flat clearances yields a socket
radius of 3.20 mm, flat coordinate −2.40 mm and span 5.60 mm. The first attempt
deliberately violates that flat coordinate.

| Evidence | Attempt 1 | Attempt 2 |
| --- | --- | --- |
| Actual saved native sketch flat | −2.00 mm | −2.40 mm |
| Saved geometry-linked drawing span | 5.200000000000176 mm | 5.600000000000236 mm |
| Independently intersected STL span at z=5 mm | 5.200000047683716 mm | 5.6000001430511475 mm |
| Unchanged 20-check profile | 18 pass, two fail | 20 pass |

The new passive STL calculation reads triangle bytes and intersects them with
the z=5 mm plane; it does not read the reported dimension to construct its result.
It qualifies one tessellated section only. Its comparison precision is not a new
acceptance tolerance, a complete CAD/mesh bound or a physical-fit result.

## Exact execution and artifact correspondence

The retained run is `3843a8c98e0f40e1a15f90790a33b6b8`, source
`workflows/printed-replacement-part-native-focus-wheel-026.workflow.wflow`.
The actual record still says `awaiting_approval`. Its checkpoint remains pending,
with no actor, answer or external action.

The authoritative event order is first assessment → one bounded revision →
delivery of that assessment's feedback → second assessment → human review.
Both assessments use exactly the same validated profile. The source pins its
canonical digest; the execution context independently pins the raw profile file.
Both identities match. The current run's outputs refer to attempt 2, while the
previous-attempt files remain available.

Both native archives pass ZIP integrity checks. Reading the explicit sketch
Geometry property confirms the changed line and unchanged 3.20 mm arc. The
drawing's SocketAcrossFlat dimension retains SectionAA_Y0/Edge15 references,
`Arbitrary=false` and its normal numeric format. Recorded native/STEP/mesh input
digests match each attempt's actual files. All 12 files in each attempt differ
between attempts, including the regenerated native document, STEP, mesh,
measurements and drawing; the original file digests remain preserved.

Count clarification: earlier “13 files per attempt” includes the associated
assessment. There are 12 output files per attempt plus two separate assessments:
26 unique preserved files. The older preservation list has 27 rows because the
second assessment appears twice. This is an accounting clarification; no file
was deleted, fabricated or lost.

## Current product verification and limits

[Walkthrough 170](../../../artifacts/ui-walkthrough/mechanical-engineering/20261010-170-correction-current-verified/report.html)
passes three steps on the served build 34: open the exact pending review, inspect
the failed assessment, and open the regenerated drawing in Wright. Browser
diagnostics and execution/review action lists are empty. All 52 run-record
hashes remain unchanged after the walkthrough. The original drawings and current
assessment/drawing screenshots were visually inspected.

Walkthrough 169 remains a recorded selector failure: it expected the source
step title as a heading, while the existing UI displays **Review the next action**.
170 changes only that recorder expectation. Both report structures validate.

The page renders at 1280×900 and 1024×768 without horizontal overflow, missing
images or page errors. Full-size originals and PDF links remain available.
28 exact artifact copies and three unmodified Wright captures have manifests.
This is a presentation/report artifact, not a generated process UI or portable
workflow export. It does not establish final PowerPoint readability.

**Newly observed availability limitation:** the saved review and results can be
read with CAD stopped, but Approve, Request changes and Continue process all
explain that the already-completed CAD step's server has no available tools.
No action was attempted. Recording a decision and executing a continuation have
different responsibilities; investigate whether the present full-run capability
preflight unnecessarily couples them. Preserve source/subject freshness,
definition/schema identity, review ownership and continuation checks. This
observation does not authorize bypassing a frozen binding or weakening readiness.

The current assessment also exposes full floating-point observations in the
default view. The exact values are valid evidence; a subsequent shared formatting
improvement should retain them on demand while keeping the primary engineering
comparison readable. No production behavior was changed in this checkpoint.

## Audit-reader development and remaining work

The first helper used an abbreviated check ID, then an XML selector that included
sketch axes. Those assertions stopped and were corrected against actual records.
The raw profile also omits optional defaults present in its validated form;
comparison now uses the existing ValidationProfile contract and verifies both
canonical and raw identities. The partial copy directory remains labelled
incomplete. None of these helper failures changed engineering data or criteria.

Private receipts: `native-correction-current-audit-070.json` and
`native-correction-browser-audit-070.json` in the increment's control root.
The public report retains its source manifest and browser evidence separately.

This is concrete progress: an independent geometry read, reconciled correction
authority/history, current product evidence and an inspectable demonstration.
Remaining work includes the review/provider availability investigation, other
065 audit rows, the accepted dock revision decision, identification of the actual
swim-lane tool, and the final two-job presentation/handoff. No CAD application,
provider, model call, new process run or review response was started here.
