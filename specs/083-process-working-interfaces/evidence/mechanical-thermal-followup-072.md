# Fresh thermal journey with offline review (072)

10 October 2026. This advances M3 review/result usability and M4's fresh-journey
and observable-request evidence after the shared fix in [071](mechanical-review-availability-071.md).
The complete mechanical-engineering goal remains active and incomplete.

## What an engineer can inspect

[Illustrated review and exact outputs](../../../artifacts/process-interfaces/083/20261010-thermal-offline-review/index.html)
contains the saved basis, original assumptions, STEP models, numerical fields,
assessment, eight unmodified Wright captures and exact downloads.

The existing AgentCAD/build123d provider authored and measured the two plates.
The bound OASiS/scikit-fem provider computed coarse and fine numerical fields
from the exact upstream geometry. Wright's existing runtime, gateway, validator,
review owner, working view and result readers carried out the process.
No source, criterion, product implementation or provider protocol was changed.

| Candidate | Fine-field maximum | Original inclusive limit | Finding |
| --- | --- | --- | --- |
| 100 × 40 × 2 mm | 50.0 °C | 45 °C | Above the limit |
| 100 × 60 × 2 mm | 41.67 °C | 45 °C | Meets the idealized model's limit |

The 60 mm candidate is the narrowest of the two declared candidates that meets
the criterion. Both fields agree with the separate one-dimensional calculation
within the original 2% comparison criterion. The original heat-balance and
refinement checks also pass. This remains a synthetic conduction-only study:
no convection, radiation, contact resistance or physical hardware qualification
is represented. Twenty-five automated checks pass; one mandatory authenticated
human-review check remains held. The runtime is terminal at that validation
hold, rather than still computing or awaiting an opportunistic AI question.

## Decision availability and actual continuation

1. Started one new run of the unchanged accepted thermal002 source through the
   scoped Wright process service with an enrolled isolated test grant.
2. Observed its declared basis checkpoint before answering. Stopped only the two
   identified test-owned providers while the run was waiting.
3. [Walkthrough 172](../../../artifacts/ui-walkthrough/mechanical-engineering/20261010-172-thermal-offline-review/report.html)
   verifies Approve enabled and Continue disabled with those providers offline.
4. Recorded the authorized synthetic decision for this exact new subject,
   attributed `integration_test:083-mechanical-engineering-heat-007`. This grants
   no human engineering acceptance or manufacturing authority.
5. [Walkthrough 174](../../../artifacts/ui-walkthrough/mechanical-engineering/20261010-174-thermal-approved-offline/report.html)
   shows the recorded test decision and disabled continuation. The backend names
   the unavailable CAD tool and instructs the user to reconnect it.
6. Reconnected the same providers and checked all seven declared tool/schema
   identities. Continued the same run once through the existing review owner.
   Its CAD and numerical-field producer steps each started once.
7. Preserved all outputs and stopped the two providers after the terminal hold.
   The working view, field plot, basis and assessment remain usable with the
   applications stopped. This is explicit campaign cleanup; it does not prove a
   newly implemented automatic application-shutdown feature in Wright.

Twenty-three steps pass across the five successful walkthroughs: 172, 174,
[175 results](../../../artifacts/ui-walkthrough/mechanical-engineering/20261010-175-thermal-results/report.html),
[176 assumptions](../../../artifacts/ui-walkthrough/mechanical-engineering/20261010-176-thermal-documents/report.html)
and [177 assessment](../../../artifacts/ui-walkthrough/mechanical-engineering/20261010-177-thermal-assessment/report.html).
All five reports validate, browser diagnostics are empty, and the read-only
captures submit no review or execution action. Basis and assessment downloads
match the exact saved bytes. Reload retains the same run.

Walkthrough 173 is preserved as a recorder failure: it expected a disabled
Approve button after approval, while the product correctly removes that control
and presents the recorded decision. Only that expectation changed for 174.
A console encoding error during passive basis inspection was also corrected;
neither incident changed a result or caused a second execution.

## Source, request and preservation evidence

- New run: `f01d057d9842441797ef7c803c3a2044`.
- Source: `workflows/heat-spreader-sizing-thermal-002.workflow.wflow`;
  SHA-256 `2430de4cb970a448febbbf82c3d300957be0cfdb9f0793d7f3836571de5f2e4d`.
- Assessment: `assessment-dbd4b81f5ded489e8dc3649c1a501e6e`; 25 pass,
  one blocked, no failed/error/inconclusive checks; release ineligible.
- One Start receipt, one same-run continuation, 20 new output files.
  All 52 earlier run records and 100 earlier thermal files remain unchanged.
- 626 correspondence assertions over the retained invocation evidence pass,
  including 19 observed submission/response pairs. These are audit assertions,
  not 626 independent integration tests. Effective instructions, saved helper
  templates, schemas, observable bridge requests and frozen routing correspond.
- Actual frozen workspace route: `hermes-http / openai-codex / gpt-5.6-sol`.
  The response's reported label is `hermes`; this does not identify a hidden
  upstream model revision. The goal's implementation-agent choice did not
  overwrite the workspace's configured model.
- API 8067/PID 84296, UI 5250/PID 27764, production build 34. Both owned thermal
  containers are stopped. No Solid Edge session or unrelated container changed.

Private exact receipts are in the existing mechanical control root:
`final-thermal-audit-072.json`, `thermal-transport-audit-072.json`,
`heat-providers-offline-007.json`, `heat-providers-online-007.json`,
`heat-provider-cleanup-007.json` and the `heat-*-007` run receipts.
The review package verifies 31 copied files, eight loaded images and 35 links;
all local link targets exist and its 1280-pixel render has no horizontal overflow.
The eight source captures and report preview were visually inspected.
A final read-only check (`thermal-preservation-end-072.json`) confirms all 53
current run records remain unchanged after browser inspection, the protected
native-correction checkpoint is still pending without an actor, and both owned
thermal providers remain stopped.

## Remaining acceptance scope

This is the first fresh, substantially different engineering journey after 071.
A fresh focus-wheel journey is still required; the prior 064 wheel run predates
that implementation change. The thermal job does not replace either primary
mechanical assignment. Dock scope resolution, actual existing swim-lane reuse,
the other completion-audit items and the final two-job presentation remain open.

Presentation limits remain visible: the full graph is too dense for a readable
slide, the earliest review capture frames its lower controls, and assessment
numbers still expose excessive numerical precision. The approved-review capture,
focused assumptions and field/assessment captures are readable. These artifacts
do not establish completion of the final PPTX's all-slide readability gate.
No protected review was answered or resumed, and no physical or supplier action
was performed.
