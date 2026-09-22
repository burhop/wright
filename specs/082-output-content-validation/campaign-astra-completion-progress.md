# Astra campaign completion progress

Updated: 22 September 2026. Active goal: `campaign-astra-completion-goal.md`.
User selected Astra for implementation; actual campaign inference remains
`openai-codex::gpt-5.6-sol`. One agent, no broad campaign dispatch yet.

## Current result

- Implementation dashboard is open at <http://127.0.0.1:8765/> and its status API
  responds against this checkout. Campaign dashboard:
  <http://127.0.0.1:8771/?view=recovery>.
- Historical ledger remains `30/30/24/0`; retained automated inspection adds 17
  to the displayed historical `30/30/24/17`. Current-revision metrics remain
  one run, zero complete output packages and zero full passes. Do not count
  isolated repair probes as renewed campaign completion.
- R0/R1/R2 remain complete. R3 is in progress; R4/all-30 queue readiness is pending.
  The active goal authorizes broad execution after these gates; the older
  renewal instruction to finish ready but stopped is superseded.

## Modelica repair and staged successor

Water 901/902 are preserved failures. The new no-network
`wright-082-modelica-renewal` runtime retains the approved immutable image but
uses a fresh native store and exact qualification/903 exports. It passed a real
native simulation, ten-file sealed export, host byte/hash readback and a repeat
export with unchanged files. All six native scenario manifests were obtained
through the actual gateway. This proves the repaired export boundary, not a
finished CAD/thermal-package workflow or public catalog qualification.

Evidence: `artifacts/campaign-example-renewal/qualification/modelica-renewal-native-export.json`.
Native proof: `.local-run/renewal-qualification/modelica-runtime/production-stdio-gateway.json`.
Setup/registration: `.local-run/renewal-qualification/modelica-runtime/installation.json`.
New server: `4328a581-59ea-49d4-a90e-fb40fe8f75b7` (15 tools).

The installer now verifies the observed runtime identity/image/mounts/running
state and requires same-container export proof for a renewal runtime. Separate
registration names avoid collision with the historical provider. The enroller
forwards every selected supplemental provider and AgentCAD initialization flag.
Eighteen focused tests passed; Ruff and `git diff --check` passed.

Water 903 was initially staged/enrolled without dispatch:

`.local-run/renewal-qualification/water01-canonical-903/modelica-attempt-903.json`

It has 16 canonical steps, 13 staged inputs, the new Modelica binding and an
initialized isolated AgentCAD project. The non-dispatch preflight found zero
errors and four review warnings about native output files named `scenario.json`.
These are named native solver metadata outputs, not the input dataset metadata;
review the exact contracts before release. The manifest now includes a bounded
retry episode linked to 901/902 and the actual repair proof under the existing
campaign-global ledger root. The follow-up `preflight-linked-retry.json` rechecked
that exact manifest and again found zero errors and the same four review warnings.
That manifest is preserved as the pre-handoff-correction record, not the current
dispatch manifest. See the live successor checkpoint below.

## Earlier inference failures (preserved)

Two minimal `/api/agent/chat` requests were made through the actual campaign
session/model, with no workflow dispatch. Both were rejected before a model
answer; do not report authentication/inference as proven by health alone.

1. `campaign-inference-20260922.json`: HTTP 503 during automatic workspace gateway
   rebinding. Hermes was briefly unavailable. The native log subsequently showed
   a clean restart and the API listener restored; no extra manual restart was made.
2. `campaign-inference-after-gateway-recovery-20260922.json`: HTTP 503 with exact
   message `Hermes gateway did not become ready after workspace rebinding`.
   The request took about 64 seconds. The existing API waits 45 seconds after its
   restart command, while the observed earlier cold startup took about 62 seconds.
   The sync manager retains its refresh-required flag after failure, so another
   request triggers another restart. This is a startup/readiness boundary to
   diagnose; no evidence currently establishes revoked credentials as its cause.

Both failed receipts and the opt-in probe script are under
`.local-run/renewal-qualification/`. Preserve them; do not overwrite or repeatedly
probe until a material recovery is established. The selected model was unchanged.

## Recovery and latest qualification checkpoint

Local commit `dde97095` separates successful gateway restart from readiness
observation. A still-starting gateway is re-observed for the same binding rather
than repeatedly restarted; readiness is bounded at 120 seconds. Cancellation,
concurrent requests and changed bindings are covered. Sixty-four focused gateway,
agent and scoped API-restart tests passed.

The authorized API restart helper timed out while the replacement PID 51012 was
still checking the 2.7 GB database. No second restart was made. The API finished
startup at 18:02:40 UTC. Follow-up readback verified the committed backend source
and module origins, the exact staged water source, and Robot 010's protected
pending checkpoint. The original all-workflow pre/post comparison did **not**
finish; do not claim that missing verification. Evidence:
`.local-run/renewal-qualification/gateway-readiness-api-restart/post-start-readback.json`.

Actual campaign-route inference then returned exactly `READY` at 18:03:10 UTC,
with no tools or errors, using the unchanged Sol model. Receipt:
`.local-run/renewal-qualification/campaign-inference-readiness-fix-20260922.json`.

Before first dispatch, local commit `f7c8a4e8` repaired the Windows-to-Linux CAD
handoff: absolute host export locations, a canonical workspace-relative STEP
reference, explicit container geometry binding and matching-byte verification
before thermal calculation. The CAD author now receives the preceding actual
AgentCAD context. Versioned operation-source inputs preserve the old staged
bytes. Twenty-six focused binding/path tests passed; Ruff and diff checks passed.

Water 903 was re-enrolled against those exact inputs/source and dispatched once
at 18:05:34 UTC. Run: `61a39518aefe46f5beb7983b39660f43`. It terminated **failed**
at 18:07:16 UTC; do not restart/re-enroll this historical attempt.
Current manifest:
`.local-run/renewal-qualification/water01-canonical-903/path-correction/modelica-attempt-903.json`.
Runner state: `.local-run/renewal-qualification/water01-canonical-903/runner-state/`.
The runner exited and saved its terminal summary; it is no longer executing.

The final preflight again had zero errors and four reviewed basename warnings.
Native exported `scenario.json` describes solver/time-grid controls, unlike the
input dataset's identically named metadata file. Exact Modelica/OASiS mounts were
read back; no concurrent campaign runner or retained active native lease was
found. The global bounded retry episode remains attached. This is the fifth
isolated qualification dispatch, not a broad campaign wave or a claimed pass.

The first 350 W native simulation and actual ten-file export succeeded, proving
the previous export repair in canonical execution. Registering the exported
result then failed: its `run:step:port` identity exceeded SubjectBinding's erroneous
single-component 160-character bound. There is no complete design package/pass.

The correction preserves the exact result address and uses the finite composite
bound of 482 (three valid 160-character components plus separators); producer
components, digests, requirements and review authority are unchanged. Shared
request/assessment/report schemas and contract documentation were regenerated.
Eighty-six validator/core/canonical/review/report tests pass. Forty-one restart
helper tests pass, including a simulated 455-second startup and bounded failure.
The helper now persists its pre-restart source/code fingerprints and observes the
single launch for up to 900 seconds rather than prematurely reporting failure.
Four additional installed-wheel/offline-gateway/native-boundary checks pass.
The retained proof is also saved in
`artifacts/campaign-example-renewal/qualification/result-identity-repair.json`.

Offline replay verified all ten actual 903 native files by size/hash and
registered its exact long named-file result in an **isolated** validation DB:
`.local-run/renewal-qualification/water01-result-identity-repair/proof.json`.
The live database and historical failure were not changed; no solver/model rerun
or campaign credit was created. This is material repair proof, not a passed case.
Deploy the committed fix with a verified owned API restart before any successor.
The three failed water attempts trigger the no-progress gate: no expensive retry
until repair deployment/readiness and exact successor mounts/grants are verified.

## Next safe work

1. Finish verified deployment of the result-identity fix. Preserve 903's failure
   and native artifacts. Stage a separate successor only after exact provider
   mount and grant checks; the present Modelica runtime mounts 903, not 904.
2. Preserve the recovered API/profile and actual inference receipt. A dashboard
   or health response alone is not an engineering result. Check existing runtime
   and retry state before any follow-on dispatch.
3. Finish water's full Modelica → physical CAD package → thermal screening chain,
   then the remaining harness ERC/correspondence, Solid Edge flat-DXF preservation
   and Robot corrective CAD/CalculiX qualification. Preserve family/branch-specific
   proof requirements and pending engineering reviews.
4. Assemble and preflight the current 30-case queue, execute controlled waves,
   and independently audit all four current-revision counts through 30/30/30/30.

Historical Robot 010 remains protected: run `1e10a25958694ce2ab4d9454029b1fcf`,
checkpoint `checkpoint-46ef3ff2d5107b0b5f55455e`, pending actual human review.
No approval, retry reset, push, merge, publication or physical action is authorized.
