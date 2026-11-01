# Research first

Start with a plain request and any images, documents or links already available.
The saved Astra-authored instructions tell Wright to reuse that material, preserve
its limitations, calculate only what the evidence supports, and identify targeted
research gaps. A declared question step asks only about consequential unresolved
user choices. It grants no engineering approval.

`build_workflow.py` renders ordinary Wright source. Upload selected files through
the existing workspace mechanisms, then supply their confined workspace-relative
paths as attachments. It does not run models, tools or jobs. The existing source
runtime owns input snapshots, exact file dependencies, model freezing, outputs,
questions and durable state. Use the normal Workflows/common workspace view;
this bundle adds no separate UI or executor.

Two paths are currently available for qualification:

- Supplied-material synthesis uses the existing model-only task. It can finish
  without a web call and handles attached image content through the selected SDK.
- Targeted external research binds an explicitly installed independent provider
  and its discovered search/fetch tool names. Its call count, timeout and context
  budget are accepted typed source settings. Missing capabilities remain visible.

These are separate authoring choices today. **Automatic optional web research in
one tool-enabled task is blocked:** the current MCP completion contract requires
at least one successful tool-call evidence number. Do not force a redundant
search or weaken engineering tool evidence to work around that rule. The shared
platform needs an explicit supported way to complete from supplied evidence or
conditionally dispatch research. Local source-only synthesis remains useful.

The current web provider reads HTML, not mechanical PDF drawings. A successful
HTTP fetch containing raw PDF data is not evidence that dimensions were read.
PDF extraction/rendering and video frame inspection need separate qualified
capabilities. Failed or inaccessible sources remain recorded, never guessed.

`research-first-v2.workflow.wflow` is the corrected reusable supplied-material
template. The first `research-first.workflow.wflow` is retained as a rejected
draft: its request regex is outside the current input-schema subset. The proposal
`user-input-schema.json` is also not a deployable runtime input contract. Actual
input blocks use Wright's supported bounded string schema. The full research
response schema is checked independently in qualification; JSON output formatting
alone does not enforce that schema at runtime or establish CAD readiness.

`authoring-provenance.json` identifies actual Astra/high authoring requests.
Execution uses the isolated profile and observable SDK receipts; source wording
does not select a model. Accepted older workflows/instructions remain unchanged.
New source/settings/reference versions require fresh inputs and invalidate their
dependent results; pending runs retain their frozen sources and routing.

Windows qualification and redacted receipts are retained in pilot state at
`research/20261020-research-first/`. Text reuse, photo input, mixed Roadster input,
and external research are separate cases. The earlier Robot Tracking proof tests
the same source/result/validator mechanisms in another engineering domain; none
of these cases grants Roadster reconstruction or proves a complete CAD chain.

The downstream [native-inspection segment](../native-inspection/README.md) now
authors a connected independent measurement and exact-report validation workflow
for an existing supplied STEP. Its preserved defective/corrected pocket controls
pass their stated scopes. It does not yet connect this research stage to CAD
authoring, private export transfer or bounded native correction; those full-process
qualification gaps remain visible.
