# SDK model-observation semantics

Date: 2026-10-23. This is a source inspection and controlled regression proof;
no model request, auth operation, native restart, or build was performed.

## Observed boundary

Installed Hermes `agent/auxiliary_client.py`, SHA-256
`a3a644f121fb97397e3dbdc23e2f19e190d444f0540a64cc6dbc74fdd8c1e2c3`,
selects the requested `model` at line 1175 and returns
`SimpleNamespace(model=model, ...)` at lines 1577–1581. Its Codex completion shim
does not forward a provider response model at that boundary. A successful call
and the returned alias therefore do not establish an upstream model revision.

Wright previously copied that SDK result into `upstream_reported_model` in the
worker evidence, ordinary workflow response evidence, and confined decision
bridge evidence. The original request and configured/resolved routing remain
valuable observations; the returned alias needs a different label.

## Implemented correction

The existing standard-library SDK evidence helper now emits:

- `adapter_returned_model`: the bounded model value returned by the adapter,
  or null when missing/invalid;
- `model_observation_scope: hermes_model_sdk_adapter_result`;
- `upstream_reported_model: null`.

The worker uses these fields for new SDK evidence, including image adapter
results. Ordinary response generation and the decision bridge select this
metadata only for the frozen typed `hermes-model-sdk` adapter. An alias that
differs from the requested alias still does not imply an upstream observation.
The scope deliberately allows adapter echo/fallback behavior without pretending
to observe provider internals.

The legacy `response_model`, completion `model`, and usage fields remain
compatible. Frozen configuration/routing and request capture remain unchanged.
Actual HTTP response metadata retains its existing treatment. No historical
invocation records, run evidence, or request identities were rewritten. The
previous GPT-6.1 readiness evidence remains a successful model-call observation;
its adapter-returned alias does not identify a provider-internal revision.

## Controlled verification

Synthetic SDK/HTTP transports only; scoped escalated execution avoids the known
host sandbox asyncio thread-wakeup limitation.

- `test_hermes_sdk_invocation_evidence.py`, `test_workflow_sdk.py`,
  `test_workflow_model_routing.py`, and
  `test_workflow_bridge_instruction_resources.py`: **64 passed in 4.51 s**.
- After adding the raw 160-character alias bound controls, the SDK invocation
  evidence file alone: **25 passed in 1.46 s**.
- Ruff and `git diff --check` passed.

Controls cover echoed, different and absent aliases; worker response
compatibility; text and image evidence; ordinary report and bridge forwarding;
unchanged HTTP reported-model observations; and missing, non-string or
whitespace-padded oversized aliases. Existing failure redaction and frozen-route
controls remain passing.

Files changed: `hermes_sdk_evidence.py`, `hermes_role_worker.py`,
`report_generation.py`, `hermes_openai_bridge.py`, and the two SDK test modules.
Independent source/contract review passed with no actionable finding. Root owns
commit/build and native verification.
