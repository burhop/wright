# Native Data Model

| Entity | Identity | Invariant |
|---|---|---|
| Definition | process ID/schema version | Ordered steps, ports/connections/output declarations; semantic digest excludes presentation/revision. |
| Step/port | document-unique stable ID | Versioned operation; exact direction/type/cardinality; one producer per input, output fan-out. |
| Quantity | decimal string + unit | Bounded exact finite decimal; explicit compatible conversion. |
| File reference | workspace logical identity | Reauthorized containment/ownership/digest; no absolute host path. |
| Presentation | keyed semantic IDs | Bounded integer positions; dragging does not reorder execution. |
| Saved document | workspace/process + token/revision | Transactional CAS; stale/invalid saves retain last complete envelope. |
| Save request | workspace/request ID + request digest | Exact retry returns prior result; changed payload with same ID fails. |
| Binding | exact server/tool/schema | Separate from definition; revalidated policy before invocation. |
| Run | immutable ID/snapshot + optional prior run | Definition/inputs/bindings/mode/actor/trace; terminal state immutable. |
| Event | run + increasing sequence | Timing, bounded inputs/outputs, cause/recovery; atomic with transition. |
| Artifact | workspace/run/step + digest/size | Complete staged output, authorized bounded access, explicit retained lifetime. |
| Milestone task | T-ID + acceptance links | Separate implementation/verification/integration with supporting evidence. |

Run states: queued → running → succeeded/failed/cancelled/timed_out/interrupted. Restart marks abandoned runs interrupted. Correction creates a linked new run. Cancellation winning terminal CAS prevents late publication.
