# Isolated final-response formatting repair

Observed 2026-09-12. Robot tracking dataset 01 attempt 001 successfully converted
its uploaded CSV inputs into a real ROS2 bag, then stopped because the final
response string was prose instead of the requested JSON. Its original run
record remains unchanged at
`runs/campaign-robot-tracking-diagnosis-01-attempt-001/20260912T151518Z-bffab58d5df6.json`
inside the demo workspace.

The previous repair included the full task prompt, image attachments, assistant
tool calls and tool results while passing an empty tool list. The Hermes bridge
forwards empty-tool requests directly to the model, so that repair crossed from
the translated single-action protocol into a raw conversation while retaining
the engineering transcript. The failed correction text was not recorded, so
its precise malformed response cannot be reconstructed from the original run.

The generic MCP runtime now makes one isolated formatting request with a system
instruction and a JSON data message containing only the previously accepted
status, evidence numbers and response string. It includes no tool schemas,
prior task history or images. The response must preserve status and the exact
integer evidence array. Requested tool calls, altered evidence/status and an
invalid target format fail without executing another operation. Boolean values
cannot substitute for integer evidence numbers through Python equality.

A failed correction emits a bounded diagnostic: reason, original evidence,
SHA256 of the correction content, a maximum 2,048-character preview and its
truncation flag. Provider failures are also retained under the existing error
contract. The single correction remains inside the current task deadline and
does not resume or replay the prior operation.

Seven repair regression cases plus nine exact-tool restriction tests passed.
The tests assert an isolated two-message request, exclusion of prompt/images
and tool history, no additional tool dispatch, exact evidence and status,
rejection of invalid formatting and preservation of provider-failure diagnostics.
Ruff passed for the changed runtime and tests.

An actual model-only probe through the existing configured Hermes endpoint
`http://127.0.0.1:8642` reformatted the exact saved robot response successfully in
5.9 seconds. The completion retained status `completed` and evidence `[1]`,
produced valid inner JSON, and dispatched zero engineering calls. The probe
did not resume or change the failed workflow or campaign counters. Local evidence:
`.local-run/feature-081-live/isolated-response-repair-probe.json`.

Deployment and actual fresh workflow execution remain the campaign runner's
responsibility; this bounded repair task did not restart the API.
