# Current failure and recovery coverage

10 October 2026. This follow-up reconciles the original M4 negatives with current
test assertions and retained browser evidence. It does not change runtime policy,
engineering acceptance criteria, or any recorded run.

**Follow-up087:** [malformed-output diagnostics](process-malformed-output-087.md)
adds the missing nonempty malformed-file browser case and removes duplicate
correction text without changing any findings or engineering holds. See its
precise software scope; the historical085 table below remains unchanged.

**Follow-up086:** [the shared observation repair](process-observation-scope-086.md)
adds served-browser coverage for missing required output and unconfirmed
cancellation using captured runtime software fixtures. It also retains read-only
wheel/thermal checks on build45. Nonempty malformed-output UI coverage remains
open. The tables below preserve085's original verification scope and limitations.

## Current verification

**59 selected cases pass, with no skipped cases or failures.** They exercise the
current canonical runner, preparation, validation, durable run supervisor,
input-response storage and public API using isolated software fixtures. No live
model, CAD application, printer, supplier, engineering review or existing process
was invoked. These are not 59 new engineering jobs.

The selection reuses 040's cases, the 13 mechanical handoff fixtures, and three
explicit cancellation/answer-recovery checks. The checkpoint API test source has
changed since 040; the source inventory and current results are captured together.
Two existing Starlette/AnyIO test-client deprecation warnings remain. An initial
helper inventory used a nonexistent source-module name and stopped before tests;
the inventory was corrected to the existing validation service. No acceptance
assertion or product source was changed to obtain the result.

- [Selection, executed cases, source hashes and preservation receipt](D:/repos/wright/.local-run/process-interfaces-083/mechanical-engineering-20261008/lifecycle-verification-085.json)
- [Current test report](D:/repos/wright/.local-run/process-interfaces-083/mechanical-engineering-20261008/tests/lifecycle-negatives-085.xml)
- [Test output and warnings](D:/repos/wright/.local-run/process-interfaces-083/mechanical-engineering-20261008/tests/lifecycle-negatives-085.log)
- [Read-only service/run/artifact link checks](D:/repos/wright/.local-run/process-interfaces-083/mechanical-engineering-20261008/handoff-links-085.json)

## Requirement-to-assertion mapping

The exact test node identifiers are grouped in the receipt above. The table
states what their assertions prove, and identifies remaining UI/live scope.

| Required case | Current authoritative assertions | Served or live evidence / limitation |
| --- | --- | --- |
| Wrong units or feature dimension | Unknown dimensions stay inconclusive; observed/expected units remain separate. Wheel height/socket mutations fail their named checks and the consumer never runs. | Actual native correction drawings/findings in070 and current reader214; synthetic scale finding156. This does not qualify arbitrary native unit detection. |
| Manufacturing method/material mismatch | Wrong PLA profile is rejected against the saved PETG requirement. Route fixtures preserve the assignment source hash; wrong/absent choices hold the consumer. | Saved route060 and walkthrough156 expose the failed choice. A declared route is not proof of the actual manufacturing operation. |
| Stale drawing or output | Old 5.2 mm drawing observation fails against the corrected 5.6 mm requirement. Changed artifacts reject the old subject; mutation during measurement prevents release. | Actual original/corrected drawings and historical assessments remain inspectable070/214. A fabricated unchanged measurement cannot establish actual geometric freshness. |
| Missing measurement capability | Missing reader records a blocked assessment, no release, and no dependent consumer call. |056/057/058 additionally prove preparation/Start rejection and a specific browser diagnostic; no new run or invented question. |
| Unavailable provider | Disabled server/tool error cannot publish success; public errors do not echo private provider text. | Fixture protection is current. Existing provider qualifications have their own scope; these tests do not prove every provider's restart or current availability. |
| Provider claims success but output absent/invalid | Actual new/nonempty file required; empty inspection file stops before assessment; malformed JSON fails checks and prevents consumer execution. | Current backend proof. A final served-browser check of these exact failure diagnostics remains open. |
| Incomplete required input | Preparation is blocked and no first-step file is produced. |053 field correction and057/058 readiness evidence, with distinct input/capability causes. |
| Invalid, stale or duplicate input answer | Invalid schema/scope/subject leaves zero response rows and checkpoint unchanged; concurrent duplicates produce one response and one consumption; lost acknowledgement returns the original response. |053/054 demonstrate invalid/stale rejection, one attributed synthetic answer, same-run continuation and duplicate responses after completion. Concurrent pending submissions are fixture evidence. |
| Interrupted answer continuation | Recreated owner refuses replay of an uncertain segment; model-call count and original log bytes stay unchanged. | Current service fixture. No live model crash was injected. |
| Uncertain cancellation | Request is durable before the simulated remote mutation; cancel and submit each occur once; actual provider outcome is retained separately. A still-working provider requires reconciliation. Uncertain publication performs no remote cancellation or downstream output. | Nine provider-state/observer/publication cases and a public API durable-cancel case. No physical stop or arbitrary CAD interruption is certified; dedicated served-browser uncertain-cancel proof remains open. |
| Disconnect, reopen and duplicate Start | An identical Start returns the same receipt while active and invokes work once. Actual ASGI disconnect leaves execution live. Recreated supervisor requires reconciliation without restarting. Missing log returns OUTCOME_UNKNOWN without repeated work. |082 additionally proves native browser refresh and bounded read-reconnection with unchanged subjects. Supervisor recreation is not an OS crash; read reconnect is not uncertain-action recovery. |

## Current handoff and preserved state

[The concise testing guide](../mechanical-engineering-testing-handoff.md) links
the actual workspace, three exact saved runs, native model/image/drawing,
requirements, analysis assumptions and current report. UI5250 serves build43 and
API8067 responds successfully. Authenticated GETs resolve each exact run and its
source digest. All linked local report files exist and have recorded hashes.
All54 existing run records remain byte-identical before/after both checks.

The latest wheel/thermal execution records have `state=failed` at an unmet
mandatory human-review check. The common UI already maps this to **Process needs
attention**; this inspection does not prove a newly discovered bad common-view
label. The separate correction run is genuinely `waiting_human`. Any refinement
must preserve this difference: a failed validation requirement cannot fabricate
a declared interaction, approval authority, or resumable checkpoint. Inspect the
actual editor and working-view diagnostics before proposing a status repair.

No application or service was restarted. The tool catalog has no callable native
Codex browser-tab/open-in-Codex tool in this turn; the guide supplies links and
does not claim to have opened a user tab. Secure authentication is retained;
tokens are absent from the guide and receipts.

## Remaining work and next action

M4's backend negative mapping is now current within the stated scopes. Browser
coverage remains incomplete for uncertain cancellation and missing/invalid
provider outputs. Next use clearly labelled isolated fixtures through the
served UI to check specific diagnostics and unavailable actions, reproducing a
defect before changing product code. Use the existing owners; do not invent a
provider protocol or resume a protected review.

M5's concise current product-testing handoff is delivered. It cannot supply the
still-missing dock deliverables or actual reviewed swim-lane integration. The
final two fresh different engineering journeys after the last implementation
fix remain due; the valid072/073 executions precede report repairs083/084 and
must retain that qualification. Slide-deck work is excluded. The full goal stays
active; this verification and handoff are concrete progress, not completion.
