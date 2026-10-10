# Mechanical workflow failure and recovery coverage

**Current reconciliation, 10 October (087):** [malformed-output repair](process-malformed-output-087.md)
adds the served-browser nonempty malformed-file case and fixes repeated correction
text, retaining every failed finding and the downstream hold.82 affected tests
and five final browser steps pass. [Observation-scope repair](process-observation-scope-086.md)
adds served-browser software fixtures for a missing required file and an
unconfirmed cancellation, with explicit diagnostics and unavailable actions.
These fixtures do not certify arbitrary live providers. Use the
[assertion-to-requirement mapping](mechanical-lifecycle-coverage-085.md) for current
backend scope. 59 selected cases passed at085;086 adds159 affected UI checks.
Later browser evidence closes several historical gaps below. Preserve the earlier counts and limitations
as their original checkpoints. PPT/deck work is deferred and no longer a gate.

**10 October 2026.** Current backend/API checks and engineering observation
fixtures. This is a coverage record with explicit remaining work, not a claim
that every failure has been exercised in the served browser or a live CAD system.

## Evidence from this increment

Forty selected existing contract cases pass on the current worktree. Nine new
wheel-handoff regressions also pass. Their assertions exercise the existing
canonical runner, result-file checks and unchanged engineering validation
profile. No real CAD application, model, printer or supplier was invoked.

The new fixture is a subset of the recorded inspection from correction run
`3843a8c98e0f40e1a15f90790a33b6b8`, producer attempt 2. Its origin file hash and
each selected value were checked independently. Every failure mutation is
deliberately synthetic. Test data is not new engineering measurement evidence.

| Required negative | Verified scope | Remaining scope |
| --- | --- | --- |
| Wrong units / feature dimension | Incompatible units and separate observed/required units remain explicit. The wheel fixture's mis-scaled height and incorrect socket flat fail their named checks; the consumer is not called. | Served-browser presentation of these exact fixture failures. |
| Manufacturing method / material mismatch | The existing focus-wheel preparer rejects a changed PLA profile against the original PETG requirement before staging. Four additional route-selection fixtures (048) enforce this assignment's sheet-metal route: the matching choice passes; polymer extrusion, machining from stock and an absent choice hold the consumer. | Declared route selection does not prove the actual CAD/manufacturing method. Its browser presentation remains unverified. No platform-wide ban on valid user-defined combinations was introduced. |
| Stale drawing / changed output | The corrected wheel observations combined with the old 5.2 mm drawing dimension fail `drawing-SocketAcrossFlat`. Generic artifact mutation blocks a retained answer with `SUBJECT_STALE`; mutation during measurement prevents release. | This does not by itself prove native detection of a geometrically stale drawing that reports unchanged values. Preserve that distinction. |
| Missing measurement capability | An unavailable required reader persists its blocked assessment and holds the consumer. | Relevant browser diagnostic should be included in final negative walkthroughs. |
| Unavailable provider | Disabled tool/server and provider error fixtures cannot publish success. Public diagnostics do not reveal raw private provider text. | These fixtures do not certify every provider's recovery behavior. |
| Provider success, absent/invalid output | Missing/stale expected-file fixtures hold their consumers. New empty inspection output stops before assessment. Malformed inspection JSON creates 20 failed checks with `output.invalid_json`; no dependent step runs. | Live provider fault injection is neither needed nor claimed. |
| Incomplete required input | Missing input blocks preparation before a later step can execute. | Reuse the existing readiness UI evidence; include it in the final manual checklist. |
| Invalid, duplicate, stale answer | API schema/scope/subject failures preserve the checkpoint. Concurrent duplicate answers are idempotent; response consumption is single-use. | Field-level browser correction and same-run recovery deserve a fresh explicit walkthrough. |
| Uncertain cancellation | Durable request, provider acknowledgement and observed outcome stay separate. Lost observers and uncertain publication do not replay remote mutation or release downstream work. | No physical cancellation or generic CAD interruption is qualified. |
| Disconnect / restart / duplicate Start | SSE disconnect retains backend work; an identical Start attaches to the existing run. Recreated API/missing log reconcile or report unknown without starting again. | Two fresh different full engineering journeys after the final product fix are still required. |

## New wheel gate regressions

The normal observation fixture passes all **20** existing profile checks and
releases its fixture consumer. Each of the six single-defect cases fails its
named check while the other 19 still pass:

- Mis-scaled overall height.
- Incorrect D-socket flat position.
- Drawing retaining the old socket across-flat dimension.
- Missing socket-depth dimension in the drawing observations.
- Open mesh.
- Native and neutral geometry disagreement.

Two output-integrity cases additionally cover malformed JSON and an empty file.
The former fails all 20 checks with the specific parsing diagnostic. The latter
is rejected by the file-output owner before a validation assessment is created.
Each fixture calls its simulated provider once; rejected cases never invoke the
dependent consumer. Criteria, source profile and acceptance values are unchanged.

The first version of this test supplied an inline value to a profile that only
accepts files. Wright correctly blocked all checks. The fixture was corrected to
write an actual declared result file through the simulated provider; the profile
was not relaxed. A later assertion used the wrong diagnostic category name;
it was corrected to the existing `output_defect` / `output.invalid_json` contract.
Both earlier failure reports remain preserved. These were test-authoring defects,
not product defects repaired in this increment.

## Exact records

- [Selected cases, command and test source hashes](D:/repos/wright/.local-run/process-interfaces-083/mechanical-engineering-20261008/negative-contract-selection-040.json)
- [Forty current contract checks](D:/repos/wright/.local-run/process-interfaces-083/mechanical-engineering-20261008/tests/negative-contracts-040.xml)
- [Nine wheel handoff checks](D:/repos/wright/.local-run/process-interfaces-083/mechanical-engineering-20261008/tests/mechanical-handoffs-044.xml)
- [Report and fixture provenance audit](D:/repos/wright/.local-run/process-interfaces-083/mechanical-engineering-20261008/negative-evidence-audit-044.json)
- [Reusable regression tests](../../../tests/test_mechanical_validation_handoffs.py)
- [Recorded-observation subset](../../../tests/fixtures/workflow-validation/focus-wheel-measurements.json)

Ruff reports no issues in the new test file. The 49 cases are distinct between
the two final reports; earlier attempts are not added to that count. Two existing
FastAPI/Starlette test-client deprecation warnings remain. All 41 original
engineering run records remain byte-identical. No saved source, instruction
policy, engineering review or production service was changed by these checks.

## Next work

Complete the remaining negative browser journeys and actual manufacturing-method
inspection scope, then perform two fresh different actual engineering journeys on the final
served build. The dock requirements decision and the original swim-lane ownership
remain separate unresolved dependencies. The final two-job deck and handoff must
retain those limitations until their required evidence exists.

## 10 October continuation: historical findings and declared route selection

Four new fixture cases retain the original wall-dock prompt hash and compare an
explicit route value through the existing validator and canonical runner. Rejected
routes persist `PROCESS_VALIDATION_REJECTED` with the specific requirement and
selector, and never call the dependent consumer. This local fixture vocabulary
does not prescribe the routes supported by Wright. Its single pass cannot release
an engineering job; the original full engineering checks remain required.

The final `tests/method-negative-048b.xml` records 13 passes: the four new route
cases plus the nine prior wheel cases. The earlier 13-pass report overlaps fully.
Across 040/044/048 there are 53 distinct selected regression cases, not 62.

Actual browser inspection of the retained native correction run exposed
`ME-UI-HISTORICAL-ASSESSMENT-048`: the first attempt was listed, but its assessment
navigation returned 403. The shared navigation owner now uses the existing
historical-result projection. Exact alias, run, subject, assessment and file hash
checks remain enforced; stale evidence remains stale and grants no new action.

Walkthrough 126 preserves the failure. Walkthrough 127 passes seven steps through
normal Workflows entry, historical HOLD, two real socket/drawing findings, exact
download, reload and the corrected 20-pass assessment. Raw screenshots were
visually inspected. This proves actual failed-dimension presentation; it does not
establish browser coverage of every synthetic unit/output failure above. The same
real human review remains pending and all 42 current run files are unchanged.

Evidence and exact report links:
[assessment-history review](../../../artifacts/process-interfaces/083/20261010-assessment-history/README.md).

## 10 October continuation: fresh actual journeys and presentation (049–052)

Thermal005 and mechanical051 provide the two fresh substantially different
engineering journeys after repair048 on build29. Thermal records25passing
checks and one required human-review hold. Mechanical records65passing checks
across six assessments and one required human-review hold, with64actual files.
The source022 cold-start drawing failure050 and accepted correction051 remain
separate evidence. Walkthroughs129–133 and138/140 inspect current outputs,
assessments and reopen. These complete the fresh-journey item above within their
recorded scope; invalid/stale-answer browser coverage and the dock remain open.

The [new review deck and exact evidence](../../../artifacts/presentations/20261010-engineering-validation-review/output/index.html)
presents those results with the original physical and human-review limits.

## 10 October continuation: explicit input and missing-reader browser proof

053–055 now cover field-level quantity correction, invalid/stale backend answers,
an explicitly attributed exact-subject synthetic answer, same-run continuation,
duplicate completed responses, saved result reopening and finished-run cancellation
guidance. Pending-execution duplicates are service-test evidence; actual duplicate
API submissions occurred after completion. No real engineering review was answered.

056 is a labelled software fixture with an unavailable mandatory length reader.
The runtime holds the consumer, retains3passing file checks and1blocked check,
and records no invented input question. Walkthroughs148/149 exposed report quote
escaping; the existing formatter was repaired. Walkthrough151 passes6steps with
the actual HOLD, no recorded measurement, byte-identical download and reload.
No process action or browser diagnostic occurs during that read-only inspection.
See [illustrated evidence](../../../artifacts/process-interfaces/083/20261010-missing-measurement/index.html).

New gap ME-READINESS-READER-056 remains: the unavailable reader should be diagnosed
before Start when it is already missing in the configured profile. This negative
proves runtime protection, not complete validation-capability preflight. These
later repairs also mean049/051 must not be described as fresh executions after
every final implementation change; they retain their original captured scope.

## 10 October continuation: required-reader preflight (057)

ME-READINESS-READER-056 is corrected for known reader registration and evidence
method gaps. Preparation uses the same registry factory as the existing validator,
without reading future upstream files or evaluating requirements. Both public
readiness and Start qualify the pinned profile. Optional checks, explicit
exclusions and review steps remain preparable; capability loss after preparation
still records the normal runtime HOLD. This is not a claim that registration
proves external tool availability or engineering compliance.

101 focused backend cases pass. The same accepted056 fixture now reports blocked;
one direct Start is rejected with the established HTTP503 CAPABILITY_UNAVAILABLE
response. The helper initially expected409; its original evidence is retained and
the request was reconciled without resubmission. No start receipt/new run exists,
all47 run files are unchanged, and the historical assessment hash is unchanged.

Walkthrough152 passes5steps through Workflows, the earlier run, preparation,
reload and its preserved assessment. Start stays disabled, no question is
invented, and browser process actions/diagnostics are empty. Raw preparation
capture was visually inspected. See the [illustrated readiness evidence](../../../artifacts/process-interfaces/083/20261010-reader-readiness/index.html).

The screen still labels capability unavailability as “Inputs need attention” and
duplicates the correction below Start; record this presentation issue separately.
This new preflight proof does not complete the original sheet-metal deliverables,
actual swim-lane integration or fresh final engineering journeys.

058 subsequently corrects that heading to “Not ready to start” and places the
duplicate action reason under Why unavailable.137 UI checks, typecheck/build32
and six actual browser steps pass.173distinct backend cases across057b/c protect
preparation and execution. All47 historical run files stay unchanged. See the
[before/after UI evidence](../../../artifacts/process-interfaces/083/20261010-readiness-clarity/index.html).
No physical or full fresh engineering run is added by this presentation check.

## 10 October continuation: route and scale handoffs (060–062)

Saved route060 deliberately publishes a polymer material-extrusion choice against
the original sheet-metal assignment. The existing validator records the specific
manufacturing-route finding and holds the consumer. Its baseline/checks are
unchanged; profile version2 updates only the limitation describing this actual
model-backed synthetic diagnostic. One request is recorded at two invocation
capture boundaries (hermes-http / openai-codex / gpt-5.6-sol).

The first scale060 attempt was a test-construction error: an ordinary prompt
output remained an inline value while the native inspection profile requires a
file. It records20blocked checks and zero measurements, so it is not evidence
that the dimension defect was evaluated. The complete attempt remains preserved.

Corrected scale061 uses the existing workspace-document gateway capability and
an exact isolated test write grant, with no review or external destinations.
Public readiness correctly lacks that test authority; Start independently
qualifies the exact enrolled source, tool schema, arguments and output root.
The file equals the declared synthetic fixture. All original20checks retain
their normalized profile/reference identity. The height of0.0180000001mm fails
the18mm numerical correspondence requirement;19other checks pass. The consumer
does not start, and no model or native CAD invocation occurs. This is a synthetic
measurement-report mutation, not a new native or physical measurement.

Walkthrough154 passes11steps on build32 but exposes raw rule syntax in the
finding summary. The existing readable-report formatter now presents typed
Required, Observed and Next action fields. It does not change the assessment,
profile, currentness, permission or exact download. Specific capability/review
corrections remain intact. Four red regression cases reproduce the problem;
45focused report/preview/access cases pass on the final code, including typed
numbers, strings, booleans, escaping and immutable assessment content. An initial
invalid test-file selection executed no tests and is not counted.

Walkthrough155 retains the first formatting improvement;156 verifies the final
separate-line layout in11steps through Workflows, exact findings/requirements,
byte-identical downloads and reload. Both baseline154 and final156 have no
browser errors or process mutations. All50run files remain unchanged across API
reload; no native application was started. All three report structures validate.
The screenshots were visually inspected. Tests are45distinct cases, not summed
across the repeated formatting checks.

[Before/after captures and independent audit](../../../artifacts/process-interfaces/083/20261010-handoff-findings/index.html).
The dock scope/native deliverables, actual swim-lane reuse, final fresh engineering
journeys and full M5 audit remain outstanding.

## 10 October continuation: fresh final journeys and audit (063–065)

The fresh-journey item above is now satisfied after the final062 report repair:
thermal006 retains20 outputs and25 passed checks/one human-review hold;
wheel064 retains64 outputs and65 passed checks/one human-review hold. Their
original criteria remain unchanged. The final browser journeys inspect actual
outputs, exact downloads and reopened state; captured engineering waits precede
their attributed synthetic responses. Recorder159's content-selection failure
and its corrected continuation remain distinct. No physical operation occurred.

Wheel064's post-cleanup audit confirms one Start receipt, all52 run records and
198 previous wheel files unchanged. The one receipt is preservation evidence,
not a new duplicate-Start test. Test applications are closed; result viewing
does not depend on reopening them.

The current package-boundary/resource suite065 passes60 checks. Its separate
source/command/report snapshot is `boundary-resources-audit-065.json`; source
hashes record provenance and do not imply coverage of every implementation file.
Do not add these counts to earlier overlapping suites as a unique total.

See the [current completion audit](mechanical-completion-audit-065.md) for the
remaining evidence reconciliation, dock deliverables, product swim-lane reuse
and final two-job handoff. The completed fresh journeys do not close those items.

## 10 October — workspace settings and repeat entry (066)

Five new settings regression cases reproduce the byte/MiB mismatch before the
repair. The final 46-test workspace/Git component run passes; see
[scope and retained failures](mechanical-workspace-followup-066.md). Browser 167
proves loading, refresh, new-case entry and exact prior-result reopening without
Start. It does not prove Git writes or a live settings save. New preparation
remains too verbose; that visual finding is retained for a shared UI repair.

## 10 October — declared defaults and readiness (068)

Five new component cases cover inspectable/editable defaults, blocked readiness
expansion, unresolved/invalid/live-choice visibility, edit invalidation and frozen
recorded inputs. The final affected 168-test batch passes. The first combined
slider test failure and its asynchronous-mount test correction are retained.
[Scope and browser evidence](mechanical-preparation-followup-068.md) distinguish
controlled readiness tests from the passive production journey.
