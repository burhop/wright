# Connected tool observations — local contract qualification

The handle's two-orientation study needs actual slicer response evidence at
inspection. An AI completion summary is not that evidence. The canonical task
runner already retains gateway call records. This change projects those records
through the existing bounded/redacted evidence owner and existing saved/connected
response path; it adds no executor, dispatch authority or status owner.

## Saved setting and boundary

`mcp_response_source: "tool_observations"` is opt-in on plain JSON MCP tasks using
required tool evidence. Default `"model"` preserves accepted workflows. CAD,
application, design-check, image-output and supplied-input completion variants
reject this setting during compilation. The setting is included in the compiled PromptStep and accepted source digest,
which the existing continuation owner checks. Source edits
require the existing visible accepted revision and invalidate affected subjects.

Output schema `wright.mcp-tool-observations/1` includes server ID, recorded attempt count
and the existing evidence projection: ordered call number, qualified tool name,
schema digest, status, arguments and result. Duplicate raw text is omitted. Standard JSON
text envelopes are decoded before field redaction; opaque text marks the output
incomplete. Projection retains its
completeness, redaction, size limit and digest metadata. Its digest identifies
projected evidence, not inaccessible provider internals or unredacted bytes.
Only the model-summary hash and byte count are retained separately in the step
record; its raw body is never substituted into this response. Existing raw call records and transport events retain their owners.

A consumer must check projection completeness, required fields, actual provider
success, exact source/output paths and artifact identities. A successful task or
transport response is not an engineering pass. Missing/truncated/redacted required
fields cannot establish such a pass. No validator, review or action authority is
created by this option. The passive manufacturing inspector has not yet been
adapted or bound to this envelope; do not claim the handle chain is ready.

## Qualification

Focused tests exercise actual canonical execution with a controlled gateway:
actual provider data versus a contradictory model claim, saved response, connected
consumer input, separate model summary, default compatibility, invalid setting
readiness, explicit redaction and oversized-result incompleteness. These are
fixture proofs, not live slicer evidence. Affected regressions include existing
Robot Tracking Diagnosis analysis tests, task/file dependencies and bundle tests.
Test results are retained alongside this record.

Candidate 036 accepted workflow remains revision 6. Its service/wheels and the
installed desktop plugin are unchanged; this implementation is local source only.
Windows acceptance, full engineering execution, inspector binding and real
rerun/invalidation remain open in the main plan.

## Review corrections

Independent review found duplicate serialized JSON could bypass field redaction.
The output no longer includes raw duplicate text or model-summary text. JSON text
is decoded before projection. A second review caught supplementary provider
warnings: only equivalent JSON is treated as redundant; separate opaque text
makes the envelope incomplete rather than silently disappearing as success.
Tests cover both cases. Recorded calls include rejected attempts; consumers must
inspect status/result rather than assume every entry was dispatched successfully.

The first final-suite attempt included an incorrectly scoped test expecting a
bare compiler to populate the storage digest. The existing preparation/storage
owner supplies that digest, not the compiler; the invalid assertion was removed.
Its failed log is preserved. Final results are in pytest-final-reviewed.txt.
