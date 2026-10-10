# Fresh mechanical journey and application shutdown (073)

10 October 2026. The second fresh engineering journey after [review fix 071](mechanical-review-availability-071.md) is complete in its digital test scope. Together with [thermal 072](mechanical-thermal-followup-072.md), it provides current evidence for M4.10. The full goal remains incomplete.

## Useful engineering results

[Open the illustrated review](../../../artifacts/process-interfaces/083/20261010-wheel-post-review-fix/report.html). It links actual STEP/native CAD, the inspection drawing, verification matrix, orientation comparison, assessments and exact Wright run.

The unchanged accepted workflow uses the existing FreeCAD provider to create editable CAD and a drawing from the saved STEP. Blender prepares the resulting mesh. The existing slicer produces offline PETG packages; the engineering inspection provider measures geometry and support paths. Eighteen observed tool responses match the prepared tool/schema allowlist, including workspace document operations. These are connected workflow outputs, not substituted illustrations.

| Observation | Socket down | Socket up |
| --- | ---: | ---: |
| Layers | 90 | 90 |
| Support midpoint paths inside nominal socket | 573.603 mm | 0.000 mm |
| Total nominal support paths | 573.603 mm | 9398.015 mm |
| Geometric bed contact | 896.315 mm² | 78.440 mm² |
| Slicer-reported material | 11.41 g | 12.30 g |
| Slicer-estimated total time | 27m 36s | 31m 29s |

The source and PETG profiles remain unchanged. Support screening uses segment midpoints and omits bead width, boundary crossing and unclassified extrusion. Removal, printed fit, torque, creep, layer adhesion and temperature performance remain physical questions. No print was dispatched.

Six assessments contain 65 passed digital checks and one blocked authenticated human-review check. That one check covers several requirements, so multiple requirement rows await the same review. The runtime is terminal at `PROCESS_VALIDATION_NEEDS_INPUT`, not still computing. The final continuation's expected 422 is retained.

## Review and result experience

Four current production-build walkthroughs pass, with 21 total steps:

- [178: basis review](../../../artifacts/ui-walkthrough/mechanical-engineering/20261010-178-wheel-basis/report.html).
- [179: simulated transfer review](../../../artifacts/ui-walkthrough/mechanical-engineering/20261010-179-wheel-transfer/report.html).
- [180: drawing, matrix, comparison and support readers](../../../artifacts/ui-walkthrough/mechanical-engineering/20261010-180-wheel-results/report.html).
- [181: exact assessment, human-review hold and reload](../../../artifacts/ui-walkthrough/mechanical-engineering/20261010-181-wheel-assessment/report.html).

Each starts through Workflows. Reports validate; diagnostics are empty. Comparison and assessment downloads match saved bytes. Read-only captures make no process decisions or execution requests. Separate authorized responses use exact checkpoint subjects and actor `integration_test:083-mechanical-engineering-final-wheel-073`; they confer no human acceptance. Transfer uses the declared local simulation.

Drawing, matrix, comparison, both support captures, assessment summary, human-review finding and rendered review page were visually inspected. Ten report images load at 1280 pixels without horizontal overflow; all 23 local links resolve. There are 89 exact copied evidence files. Dense graph overviews, excessive numerical precision and fine drawing labels still need clearer presentation/enlargement in the final deck. This is not M5 completion.

## Exact source and preservation

- Run: `79b02848cf4e481bbee3f7a26a9d19ae`.
- Source: `workflows/printed-replacement-part-native-focus-wheel-051.workflow.wflow`; SHA-256 `cc914d841858eb0c8c4a64f3437c4ab144b6f763cd1425ae021fc37bbc0b8477`.
- One Start receipt, three same-run continuations, 64 new output files. All 53 prior run records and 262 prior wheel files remain unchanged.
- Native projection readiness took 12.388 seconds within the declared 30-second bound. The earlier startup observation timeout was reconciled against the original live processes, without duplicate launch or Start.
- Request audit: 157 correspondence assertions over four observed submission/response pairs; five primary request captures, three runtime decision captures, six bridge request captures. These are evidence assertions, not 157 independent tests.
- Frozen route: `hermes-http / openai-codex / gpt-5.6-sol`. Reported upstream label `hermes` does not establish a provider-internal model revision.
- Two FreeCAD documents and the owned Blender scene were saved before closing their sessions. Both exact owned containers are stopped. Post-cleanup verification confirms Blender PID 11740 exited and all 54 run records and outputs remain unchanged. Solid Edge was untouched. This is campaign cleanup, not a newly implemented automatic Wright shutdown feature.
- The separate native-correction product-review checkpoint remains pending without actor or external action. It was not answered or resumed.
- API 8067/PID 84296 and UI 5250/PID 27764 serve production build 34. No accepted source, instruction, criterion or production code changed here.

Exact receipts are retained in the mechanical control root under `final-wheel-*-073.json`, `wheel-transport-audit-073.json` and `wheel-handoff-check-073.json`. The report is a review-copy bundle, not a portable export or final presentation.

## Remaining scope

Thermal 072 and wheel 073 now demonstrate two substantially different journeys after 071. No new critical/high defect was observed in these journeys. They do not resolve the dock conflict, identify the existing swim-lane implementation, complete remaining document/negative/portability audits or deliver the final two-primary-job presentation. Follow the [full audit](mechanical-completion-audit-065.md) and [pending decisions](../mechanical-engineering-decisions-059.md). Thermal remains a regression example, not a replacement primary assignment.
