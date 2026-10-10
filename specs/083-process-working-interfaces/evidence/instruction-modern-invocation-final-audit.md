# Independent modern invocation audit — 8 October 2026

## Scope and subjects

This read-only audit inspected already completed isolated durable records and
their exact saved source, CAD screenshot and generated image files. It did not
execute a process, activate a provider, submit a model request, grant review
authority, rewrite history or reconstruct omitted historical request bodies.

| Actual completed run | Saved policy | Bridge submission/response pairs | Native SDK image captures |
|---|---|---:|---:|
| `d09152ea0e094335bcc05b68b38dcf6f` | `document_reasonable` | 6 | 1 |
| `e3a2f56a090f4e9cb765582b42cb21d8` | `require_specified` | 7 | 1 |

Sources respectively:
`workflows/action-intent-shape-documented-choices-e998b58e.workflow.wflow` and
`workflows/exhaustive-strict-shape-9663f682.workflow.wflow`.
Both current source byte hashes exactly match their durable accepted source
digests. Both embed profile `wright.workflow-defaults` **1.2.0**, **34** instruction
resources and `wright.workflow-action-intent/1`. Every body digest and the four
new helper role/substitution contracts validated against those saved values.
No current defaults were substituted into a saved request.

## Observed capture and routing checks

- Every actual invocation records the exact source instruction collection digest.
  Resolved MCP/image role records retain their saved resource identities and
  independently matching text digests.
- Runtime decision inputs equal the primary adapter's recorded messages and
  model-facing tool schemas. The saved action declaration is present as a system
  message; the saved workspace helper is present in the task prompt.
- The actual bridge submission contains the saved translation-system body and a
  translation preamble rendered from the accepted resources. Its recorded JSON
  transcript retains the pinned task/user/system messages. Visible tool schemas
  extracted from that already captured transcript match their recorded model
  schema digests and the shared action wrapper. No second executor is inferred.
- All 13 submission records precede their response records. Submission snapshots
  contain no later response model enrichment. Request digest, messages, schema
  digest, instruction collection and lock identity are unchanged across each pair.
  No unmatched submission remains in these completed records.
- Each pair records a fresh created session and an accepted exact lock for
  `hermes-http`, `openai-codex/gpt-5.6-sol`, with configuration digest matching the
  frozen run context. Both runs have only model-routing execution context; no
  integration grant, approval or dispatch authority was inferred from it.
- Action validation events retain the same original provider schema identity as
  the available-tool catalog records. The documented run has five validated
  actions and two assumption-recording events. The strict run has six validated
  actions, empty action assumptions and no assumption-recording event. No
  approval/dispatch/answer decision event appears in either subject.

These actual model schemas reach depth17. The separate controlled boundary
regression proves native depth16/wrapped depth18; this audit does not claim that
the live provider happened to exercise that exact upper boundary.

## Image handoff and final file identities

Each primary image request and actual SDK capture use the same saved image role
instructions and the same single JPEG reference. Independently reading the CAD
export confirms its recorded raw file hash and size; its encoded data URL hash
and size match the submitted image reference. The generated final PNG file has
the recorded hash/size and valid PNG signature. The SDK records the exact frozen
image resolution, selected `gpt-5.6-sol` model, explicit native image-edit tool,
`store=false` and request field names. This establishes CAD-image-to-image
handoff and actual final files, not dimensional or manufacturing certification.

## Evidence and limits

Bounded report with both immutable run-log hashes, 68 resource identities,
per-pair indexes/digests, tool identities and image input/output references:
`C:/Users/markb/.codex/visualizations/2026/09/24/01a0d4b8-b5fa-79d0-8e8b-fc78c3dfd056/instruction-portability-20261007/provider-live-evidence/modern-invocation-independent-audit.json`.

The earlier `e333f6183c704380bac48be20b402ccb` proof retains five ordered pairs
and one SDK capture. It is a separate historical post-snapshot-fix qualification;
it is not relabelled as a modern profile1.2 action-contract run. The fresh subjects
above supply that modern coverage.

Text HTTP responses report the alias **`hermes`**. The accepted exact session lock
and frozen configuration confirm the selected provider/model before transport,
but the HTTP response does not independently expose the hidden provider's actual
reported text model. The audit retains the alias honestly rather than replacing
it with an inferred model. The SDK image capture reports `gpt-5.6-sol`.

Two uncalled tool schemas have redacted `confirmationToken` fields and token
format descriptions. Their original pre-redaction digests remain recorded, but
cannot be independently recomputed from redacted records. Other visible schemas
are verified from the actual captured transcript; no omitted field is guessed.
Request digests cover original submissions before redaction, so omitted image
bytes are checked through the existing reference/file identities rather than
recreating a request and presenting it as transport evidence.

Provider-internal prompt additions remain outside Wright's captured transport
authority. This audit verifies the shared runtime, primary adapter, bridge and
native SDK paths used by these subjects; general chat/UI authoring and other
providers retain their own scoped capture/unit evidence in the broader inventory.
Engineering validation and human acceptance remain separate authorities.
