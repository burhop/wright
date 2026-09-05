# Process language authority and Rivet replacement

**Decision date:** 2026-09-04. The user's follow-up explicitly confirms Rivet replacement and asks for the process language to be the official source of truth for AI and the canvas. This clarifies the existing single-document architecture; it does not claim AI authoring or legacy migration is already implemented.

## One authoritative language

The versioned Wright process language is the canonical semantic document, initially serialized as `wright-native-process` JSON. Its schema, versioned operation signatures and semantic invariants define what a process means. Readable prose, canvas nodes/edges and execution views are projections. Renderer-specific state, generated text and an AI conversation cannot introduce hidden steps, connections, parameters or executable behavior.

The canvas and Inspector edit this document through atomic commands. AI clients read the same document and schema and submit candidate definitions through the same authorized create/update/check API. Both receive the same structural/readiness diagnostics and stale-writer protection. Frontend validation improves feedback; the shared backend validator remains authoritative for every caller. No AI-only schema, runtime, save path or interpretation of a diagram is permitted.

Stable step/port/connection identities survive labels and layout changes. Layout is separate presentation metadata. Moving a node does not change process meaning or its semantic digest. Bindings are separate exact tool/environment choices; immutable run records snapshot the definition digest and bindings actually executed. Declared outputs do not count as observed results.

Publish the versioned schema and supported operation descriptors from the native service/package so UI and future AI integrations discover the same contract. Hand-maintained frontend types must be checked against shared conformance fixtures; they cannot become a second specification. An editable textual DSL may be added later only as a lossless frontend to this language, with explicit unsupported-feature diagnostics and round-trip tests.

## Milestone boundaries and replacement path

This milestone establishes the official language and native editor/runtime for new engineering processes. Programmatic clients can use the shared document APIs. An autonomous AI authoring experience remains deferred under the submitted goal; compatibility tests use explicitly labeled simulated client payloads and never claim a real AI study.

Rivet is the legacy implementation being replaced. New native work must not depend on Rivet serialization, runtime, editor, bridge or example-specific dispatch. Reuse existing generic workspace/vault/gateway services through their public boundaries; extract generic helpers where needed rather than importing Rivet-specific modules into the native path. Do not add new Rivet features to deliver native behavior.

Retain existing legacy behavior during this milestone. Subsequent migration work must inventory used Rivet capabilities, analyze imports without executing them, report unsupported/lossy cases, copy supported definitions to new native identities, preserve originals, and demonstrate equivalent outputs and recovery. Retirement follows verified migration and explicit removal scope. The dashboard must distinguish native milestone delivery from remaining migration and Rivet retirement; it must never report full replacement simply because the native editor works.

## Required conformance evidence

1. A programmatic create/update/check payload is rendered by the canvas with the same stable IDs, values and exact endpoints; it saves/reopens without semantic loss.
2. Canvas edits produce a valid canonical definition consumable through the headless API. Equivalent UI and headless runs bind that same semantic digest and independently checked output content.
3. Invalid programmatic edits and stale tokens receive the same rejection as equivalent UI submissions, preserve committed data, and expose actionable findings.
4. Layout-only changes preserve semantic identity. Presentation fields cannot affect runtime dispatch; unknown schema/operations cannot silently execute.
5. Native imports/build/runtime are checked for Rivet dependencies, and legacy regression checks remain separate. Report simulated client evidence, actual native execution and live tools accurately.

T002 freezes this contract; T006/T011/T012 implement and verify common semantics and discovery; T013/T014 project/edit it; T016/T021/T023 verify round trips and execution parity; T003/T004/T032 expose the replacement boundary. Existing task identities and denominators remain unchanged; this clarification is recorded in the milestone decision.
