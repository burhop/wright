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

Water 903 was staged/enrolled, **not dispatched**:

`.local-run/renewal-qualification/water01-canonical-903/modelica-attempt-903.json`

It has 16 canonical steps, 13 staged inputs, the new Modelica binding and an
initialized isolated AgentCAD project. The non-dispatch preflight found zero
errors and four review warnings about native output files named `scenario.json`.
These are named native solver metadata outputs, not the input dataset metadata;
review the exact contracts before release. The manifest now includes a bounded
retry episode linked to 901/902 and the actual repair proof under the existing
campaign-global ledger root. The follow-up `preflight-linked-retry.json` rechecked
that exact manifest and again found zero errors and the same four review warnings.
No episode authorization or attempt budget has been consumed for 903.

## Inference readiness is not yet established

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

Both receipts and the opt-in probe script are under
`.local-run/renewal-qualification/`. Preserve them; do not overwrite or repeatedly
probe until a material recovery is established. The selected model was unchanged.

## Next safe work

1. Reconcile live Hermes startup and its readiness/rebinding timeout. Read the
   current gateway log through the shared redactor; preserve the existing profile
   and credentials. If code changes are needed, test the cold-start and failure
   paths, then restart only the exact owned API using verified process identity
   and private environment preservation. Do not switch profiles based on a stale
   PID file (a retained profile PID has been reused by an unrelated OS process).
2. Prove one actual inference response, finish warning review and re-run the
   actual 903 preflight. Audit its provider mounts, leases, grants and final
   package output paths before one isolated dispatch. Use the existing runner and
   global retry ledger; inspect any existing state before launching.
3. Finish water's full Modelica → physical CAD package → thermal screening chain,
   then the remaining harness ERC/correspondence, Solid Edge flat-DXF preservation
   and Robot corrective CAD/CalculiX qualification. Preserve family/branch-specific
   proof requirements and pending engineering reviews.
4. Assemble and preflight the current 30-case queue, execute controlled waves,
   and independently audit all four current-revision counts through 30/30/30/30.

Historical Robot 010 remains protected: run `1e10a25958694ce2ab4d9454029b1fcf`,
checkpoint `checkpoint-46ef3ff2d5107b0b5f55455e`, pending actual human review.
No approval, retry reset, push, merge, publication or physical action is authorized.
