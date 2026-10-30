# T015: source-run local diagnostics

Implemented locally on 23 October 2026. This is implementation and verification
evidence, not user acceptance or qualification of the handle's engineering tools.

## Journey and ownership

The normal workspace's common working view has **Progress → Diagnose this run**.
Opening it sends no diagnostic request. **Preview support file** reads the exact
source run; the user reviews the contents, explicitly confirms, and downloads the
same inert JSON once. **Inspect step** and **Inspect recorded run** use the existing
scoped navigation. Changing run/workspace discards the prior preview/confirmation;
a late response cannot attach to the new scope. No automatic upload exists.

- `CommonProcessView` supplies its existing client workspace and attached run ID.
  `SupportDiagnosticsPanel` reuses `workspaceService`'s preview/export endpoints.
- `DiagnosticScope.source_run_id` is distinct from Rivet `scenario_run_id`.
  Mixing it with scenario/session scope is rejected; a source start receipt does
  not prove session ownership. The UI omits session scope for a source run.
- `SupportDiagnosticService` reads the existing immutable `process_start_receipts`
  through a read-only connection. The receipt supplies the accepted source and
  retained recorder locator; no caller-supplied path is accepted.
- `support_source_diagnostics.py` projects `workflow_run_record`'s existing safe
  reader. It is not another logger, run-state owner or executor. Missing,
  mismatched, symlinked or unreadable evidence fails with a safe explicit error.
- The export includes source/run identities, the canonical recorder-content
  digest, **recorded** status, recorded times, and at most the last 100 allowlisted
  timing events with exact sequence and safe step IDs. Paired completed-step
  timestamps provide durations; repeated attempts retain distinct sequences.
  Truncation/invalid metadata are explicit. Names, raw errors, paths, prompts,
  responses, tool payloads, credentials and reusable authority remain omitted.
- Existing principal/workspace binding, five-minute expiry and one-use grants
  remain the export authority. Exact source-run material joins the existing state
  digest; even a same-count event-content change or deleted record invalidates
  export. The common view remains the live state/recovery authority.

The optional projection extends the existing support-diagnostic schema and API;
old workspace/Rivet scopes retain their behavior. Current tools, costs, remaining
time and physical outcomes are not inferred from the recorded timing projection.

## Focused verification

| Check | Evidence |
| --- | --- |
| Backend diagnostics, existing privacy/one-use scope behavior | 45 passed across the source tests, existing service/contracts tests and diagnostic leak test. |
| Added source recorder cases | Initial 13 passed, including cross-workspace/mixed-scope denial, exact local bytes, redaction, failed/missing/mismatched evidence, replay, changed/deleted evidence, bounded metadata and repeated attempts. After review, 13 affected cases passed, with 11 unchanged cases deselected; this adds three normal run-event sentinel cases and eight unsafe-schema rejection cases. |
| API diagnostics | Existing six cases passed; one added source projection/export serialization case passed separately. |
| Frontend | 132 passed across `SupportDiagnosticsPanel.spec.tsx`, `CommonProcessView.spec.tsx`, and `workspace-service.spec.ts`; TypeScript build passed. |
| Served Chromium | One journey passed in `tests/ui-integration/process-support-diagnostics.spec.ts`: saved workspace source → common working view → exact failure → preview → confirmation → one local download → same run's step. One start, no cancellation or source edits. |

Browser evidence is under `artifacts/first-contact/084/local-diagnostics-final/`;
`local-diagnostic-preview.png` was visually inspected. This uses controlled HTTP
responses, not a live backend/model/provider. The run reported a ResizeObserver
loop warning; passing interactions do not establish an error-free console.

Retained stops: the initial schema assertion lacked a registry for the existing
sibling schema, so it attempted remote resolution; the corrected assertion uses
both local schemas and passed. The first browser helper raced the console's
automatic collapse; the focused test now uses the normal saved-file entry without
that cosmetic helper action. The API test run stalled inside the sandbox and
terminated at its 45-second bound; the same six cases passed outside it. No
runtime workarounds were added for these harness/host limitations.

Independent review found two bounded issues, both corrected: the recorder's empty
task ID on whole-run events is a normal sentinel and no longer raises an omitted
metadata warning; nonempty malformed IDs still do. Explicit safe-ID, SHA256 and
uppercase-reason constraints now appear in both the typed fields and published
JSON Schema. Negative fixtures reject path-like/overlong IDs, malformed digests
and free-text/lowercase reasons. No UI, export authority or execution changes
were needed for these corrections.
