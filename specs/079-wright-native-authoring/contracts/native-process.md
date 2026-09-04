# Native Semantic and Authoring Contract v1

The complete [JSON schema](native-process.schema.json), concrete `examples/`, and [frozen implementation appendix](implementation-appendix.md) govern exact shapes, bounds, operation signatures, units, API, ownership and recovery. They resolve the high-level descriptions below; schema acceptance is followed by the explicitly listed semantic invariants.

The [language-authority contract](language-authority.md) makes this process language the official source of truth for AI clients, the canvas and runtime, and defines the Rivet replacement boundary. Readable text and renderer state are projections of this definition.

Format `wright-native-process`, version `1.0.0`. Definition contains process ID/title, ordered steps, exact ports/connections and output declarations. Stable IDs are lowercase ASCII letters/digits/hyphens, begin with a letter, 3–80 characters, unique across semantic entities and unrelated to labels/indices. Bound documents to 1 MiB, steps to 100, ports/connections to 400 each. Reject duplicate keys, nonfinite numeric values, unpaired surrogates and unknown fields. Freeze per-field/config bounds in the executable schema before persistence.

Initial logical port types: text, quantity, workspace artifact reference. Direction/type/one-or-many cardinality must match; one producer per input, output fan-out allowed. Missing required connections/values are readiness findings; dangling IDs/incompatible edges are structural errors. Forward dependencies must be acyclic; declared step order breaks execution ties.

Quantities use canonical decimal strings: finite, no negative zero, at most 34 significant digits, absolute exponent at most 18; explicit versioned supported unit table. Conversion is an explicit operation and dimensional incompatibility fails. Other numeric fields are safe integers. Freeze cross-language canonical JSON vectors before implementation; semantic digest excludes presentation/revision/digest, document token covers persisted semantics and presentation.

Every accepted command validates a whole candidate and forms one undo unit. Invalid field text stays in a buffer while the valid/saved document remains unchanged. Review cascading deletion impact; cancel is a no-op. Saving retains session undo; history is bounded to 100 commands with a visible limit. Undo cannot rewind stored revision. Positions are bounded integers keyed by semantic IDs; renaming/moving/display-port reordering preserves identity.

Save sends semantic/presentation content, expected token and request ID. Create cannot overwrite. Update uses CAS. Conflict retains working copy and offers explicit reload or save-as-new. Same-request retry returns its original response; changed payload with the same request ID fails. Interrupted writes return an old or new complete document.

Operations use registered versioned identities, never labels/domains/examples or arbitrary code. Unknown operations can be saved as unbound drafts but cannot run. Readiness checks operation config/ports, sources, file authorization and binding requirements. Snapshot definition/inputs/bindings before run. Failed assertions identify correction targets; a rerun gets a new ID and optional `derived_from_run_id`. General expressions, implicit coercion, parallel/cyclic scheduling and human-approval runtime steps are unsupported.
