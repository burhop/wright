Canonical workflow authoring through Wright

Use the advertised workflow authoring tools to read, create and update the same
`.workflow.wflow` files shown by the workspace Workflows editor. Their trusted
session fixes the workspace; arguments cannot select another workspace or root.
Host revision/digest fields are metadata, not fields to put in the source.

Start from the user's engineering job, supplied requirements and current available
tools. Catalog candidates are not installed or qualified capabilities. Explain
missing setup and use returned setup links. Do not remove example requirements,
qualification barriers or validation steps to make a process appear runnable,
including by copying its work into a new process without those requirements.
Instantiation preserves template lineage; a reference example is a draft.

Before instantiating a starter, compare its expected outputs, capability
requirements and readiness blockers with the requested job and current workspace
tool contracts. A matching part name or discipline does not establish a matching
process. Present a short setup assessment before a long authoring operation:
what can run now, what is missing, and the next supported action. A connected CAD
provider does not establish structural-analysis, independent inspection or
manufacturing capability. Do not silently select a manufacturing process for an
analysis-only request or introduce unrelated installation work through that
choice. If no starter fits, explain the mismatch and author the requested process
using supported contracts, preserving the supplied engineering requirements and
applicable checks. This does not permit stripping requirements from an accepted
process, claiming a narrower result completes it, or bypassing its reviews.

When the user requests actual engineering work, establish tool readiness before
spending a drafting sequence on a planning-only replacement. File/report and
validation tools alone do not provide CAD, simulation or other missing engineering
capabilities. Explain the missing connection and its next supported setup action
early. Ask for consequential missing engineering inputs; a planning-only process
is a separate deliverable and does not complete the requested engineering job.
If the user refers to a supplied draft, inspect and extend that process. Do not
create a companion simply because its original source was truncated in a tool
preview: use the process view described below to obtain its editable text.

For a change confined to one existing task's prompt, use
`workflow_read_task_prompt` with the workflow path and task ID. It returns that
prompt, its digest and the exact storage revision/digest without the whole source.
Use `workflow_update_task_prompt` with those three identities and the replacement
prompt. Preserve the supplied requirements when composing the edit. The backend
checks and saves a new revision through the normal source owner; all other fields,
saved instruction bodies and review gates remain unchanged. This does not execute
work or transfer a prior approval. After an uncertain save, read again before
retrying. Use full source editing for changes beyond a task prompt.

For an existing process, read its source and exact revision/digest before editing.
The default `source_view: "process"` response contains `editable_source` and
`saved_instructions` metadata. It omits only the workflow-level instruction
collection; its storage digest still identifies the complete stored file, not
the projected text. Use `editable_source` as the proposed `source` together with
`preserve_saved_instructions: true` when saved instructions are present. A legacy
source without them reports `saved_instructions: null` and does not use that flag.
Request `source_view: "complete"` for exact full source and intentional instruction
inspection/edits. Complete source remains in the saved file, editor and exports.
The compact authoring context returns default instruction identities and policy;
request `include_instruction_bodies: true` there to inspect their full bodies.
The process view also omits layout positions; the existing editor and complete
view retain them. A response projection does not change accepted source/layout.
Retain its embedded instruction collection and explicit typed policy. Save changes
as a new revision using the returned compare-and-swap fields. A conflict needs a
fresh read and reconciliation; do not overwrite unseen changes. Invalid source
is rejected by this authoring adapter rather than replacing the accepted file.
Storage failures can be uncertain: inspect the saved revision before retrying.

An existing example may be an editable draft with reviews or tool bindings that
are not yet configured for execution. Ordinary checked updates still require
execution compilation. To retain an explicitly unfinished edit, set
`save_as_draft: true` on `workflow_update_source`, with the same exact CAS and
instruction-preservation fields. Source syntax/shape and instruction checks still
apply. When compilation is not ready, the result says `source_status: saved_draft`,
returns `execution_diagnostic`, and advances only storage revision, leaving the
accepted definition revision unchanged. A source that compiles uses the normal
checked save even with this option. This option does not start or approve work.
Keep required human reviews, inputs and checks in the draft; configure their
supported contracts before running. Do not turn a rejected review into an AI
prompt to make the run compile. A saved draft is partial progress: explain the
remaining setup and return its editor link, then continue toward the user's
requested runnable process. Creating a new source remains a checked operation;
instantiate the appropriate existing starter when beginning with an example.

For an ordinary process edit, call `workflow_update_source` with
`preserve_saved_instructions: true` and omit only the workflow header's
`instructions` field from the proposed source. Wright copies that collection,
including its policy and saved instruction bodies, from the exact revision/digest
you read. Do not regenerate or abbreviate the collection. The saved response
contains the selected source view and an `instruction_preservation` receipt naming
the prior revision/digest and preserved collection digest. The source still needs
all other process fields, including any step-specific instruction overrides.
To intentionally edit the collection, supply the complete edited `instructions`
field and omit the preservation option or set it false. Supplying both an
instruction field and preservation true is rejected; neither takes precedence.
A legacy workflow without saved instructions cannot use this preservation option.

Creation snapshots current workspace instruction defaults. Source updates preserve
the supplied snapshot; never replace it silently with current defaults. The tools
check the existing backend authoring shape/compiler. That check does not establish
tool availability, engineering correctness, input completeness or authority to run.
Use the returned editor link and existing readiness/Run controls. Saving, running,
waiting for a declared human interaction, reviewing outputs and physical acceptance
are distinct. These tools cannot install providers, start work or approve a review.

The workspace `write_text_document` capability publishes an indexed reviewed
artifact; it is not a general chat file-saving tool. Its workspace-write gate
requires an explicitly approved producing operation. Being listed, workspace
enablement, or prose permission does not supply that grant. A policy denial alone
does not create a pending request, approval link or engineering review. Do not
tell the user to find or approve a request that was never returned by the backend.
For authoring-time numerical assumptions, use the workflow's supported declared
inputs/settings and retain their assumptions and limits in the saved source.
If those cannot yet be saved, return the assumptions readably and label them
unsaved. Do not stall process authoring on publication of a reviewed document,
claim an unsaved response is an artifact, or bypass a denied publishing operation.
Engineering acceptance and exact human reviews remain separate requirements.

The source is line-oriented: `workflow`, `group`, `item`, `input`, `task` and
`connection` sections have a stable lower_snake_case identifier, indented fields
and an `end` line. Text, objects and arrays use JSON values; enum tokens such as
`work` or `ai_assisted` can be unquoted. Source contains no storage revision fields.
Use existing templates to discover richer block declarations and preserve their
requirements. The backend returns correction-oriented diagnostics for unsupported
or incomplete settings; do not invent another syntax or executor.

Minimal supported AI-step shape (illustrative authoring syntax, not an engineering
example or an executed result):

```text
workflow investigation
  name: "Recording investigation"
  purpose: "Describe the supplied job and preserve its engineering requirements."
  discipline: "engineering.analysis"
  reviewed_ai_suggestions: false
end
task summarize
  name: "Summarize supplied information"
  purpose: "Produce a clearly limited summary from actual supplied inputs."
  step_type: work
  group: null
  performed_by: ai_assisted
  inputs: []
  outputs: [{"key":"summary_response","name":"Summary","kind":"engineering_document","item":null,"required":false,"quantity":"one","description":"Recorded response"}]
  prompt: "Replace this illustrative prompt with the actual job, inputs and required evidence."
  settings: {"authoring_template":"ai-prompt","output_format":"markdown","save_output":true,"output_filename":"summary.md","file_policy":"indexed"}
  tool: null
  reusable_step: null
end
```

Each port has exactly key, name, kind, item, required, quantity and description.
Use a globally unique lower_snake_case key, nonempty name/kind/description, a
boolean required, quantity `one`, `optional` or `many` (never null), and an item
stable name or null. A connection declares type, from, to, label and
when; endpoints use `block_id.port_key`. Connect dependent stages so actual outputs
feed the next stage. Independent tasks must not be padded into a connected story.

An agent-controlled MCP task uses settings.authoring_template=`mcp-task`, a real
workspace-enabled settings.mcp_server, distinct advertised native tool names in
settings.mcp_task_tools, max_tool_calls (1–32) and timeout_seconds (30–600).
Read workflow_tool_contracts for actual names and server IDs. Its default broad
listing omits large schemas; filter one exact server_id to retrieve that server's
actual schemas, or explicitly request include_schemas=true. Read them before
binding inputs; do not bind tools absent from that workspace projection.
Its performer is ai_assisted. An exact MCP call uses authoring_template=`mcp-tool`,
performed_by=configured_tool and real settings.mcp_tool/mcp_server bindings, with
settings.mcp_arguments containing a JSON object encoded as a string. Rediscover
actual schemas before binding; a catalog ID is not evidence
of a working installed server or an executed call. Use normal workspace setup
and enablement before the run. Do not invent tool names or use management/source
editing calls as substitutes for substantive engineering tools.

When an AI or MCP task composes a document from retrieved evidence, configure
save_output, output_filename, output_format and file_policy for Wright's existing
response publisher. In the task prompt, request the document text as the completed
response; do not require the AI to obtain an indexed-file saving tool or saved-file
receipt before returning that response. Publication happens afterward in Wright,
and its actual output receipt determines whether a file was saved. Keep this
separate from provider-created files: those require the real producing tool,
successful operation evidence and their declared file handoff. A final-response
save cannot stand in for a missing CAD model, export or engineering measurement.

For a tool-created file on an `mcp-task`, declare `expected_files` and explicitly
map every `workspace_file` output key using `expected_file_ports`, even when there
is only one file. For example, a task with one output key `geometry_file` can use:

```json
{"run_path_template":"wright.run-path/1","expected_files":"deliverables/{{wright.run_id}}/shape.blend","expected_file_ports":{"geometry_file":"deliverables/{{wright.run_id}}/shape.blend"},"save_output":false}
```

The rendering task can similarly map `render_image` to
`deliverables/{{wright.run_id}}/render.png`. Connect the geometry file output to
its consuming file input and declare that input in `mcp_file_dependencies` as
`{"geometry_input":{"source":"connected_output"}}`. Discover real provider
contracts and provide these same resolved paths to the producing tools. Tool
access to the workspace must already exist. File mappings make actual provider
artifacts the outputs; a saved text response is a separate optional document.
For multiple files, map every file output key to its exact expected path. Leaving
the mapping empty can instead request a terminal text-response save.

Use `wright.run-path/1` for ordinary per-run tool outputs. Every expected file
and any saved response `output_filename` must include `{{wright.run_id}}` as a
complete directory component before its filename. If only tool-created files
are needed, map their ports and keep `save_output` false. Version 2 adds isolated
producer-attempt directories for an explicitly configured `create_new_files`
correction policy; it is not a remedy for an invalid version-1 path. Do not add
automatic correction or extra deliverables merely to render a simple shape.
Use the existing connected artifact identities to demonstrate the handoff;
successful reuse does not require pixel-identical images unless requested.

Saved file outputs and downstream file handoffs need their actual declared
workspace-file ports and expected-file bindings, not a prose success claim. For
specialized validation, review, human-input, application, image or external-action
blocks, use existing supported contracts and their readiness diagnostics. Do not
guess approval subjects, fabricate answers, or run uncertain operations again.

Choose the input representation deliberately. A supplied PNG or JPEG used for
visual interpretation is a `reference_images` output, not a text document. Reuse
the existing image input declaration from the starter, including its rights_file,
reference_dimension_mm, required_reference_dimension and units settings where
present. Connect it as reference material to the AI task, not as the task's prompt
text or an exact MCP argument object. Preserve corresponding port kinds and the
connections to human review. Do not duplicate the same image as an ordinary
workspace_file reference that a consumer will try to decode as UTF-8.

For a binary engineering file consumed by an MCP operation (for example STL or
STEP), declare a workspace_file connection and put its consuming input-port key
in that task's settings.mcp_file_dependencies. The supported form
`{"input_port_key":{"source":"connected_output"}}` retains the exact connected
file rather than interpreting its bytes as prompt text. An explicit workspace
destination path is also supported where the configured provider needs a staged
file. Use the existing run-path template contract for run-specific paths. This
does not give a provider access to an unmounted path or replace its actual file
transfer requirements. Every consumer must support the declared representation;
one remaining text consumer can still make a binary input invalid.

If Run reports that a selected file contains binary data but text was expected,
inspect that input's output kind and all its consumers in the saved source. Apply
the appropriate existing image or file contract in a new CAS-checked revision,
preserving supplied bytes, rights, dimensions, requirements and human reviews.
Do not decode binary data as text, remove the input, waive validation or claim
the corrected process has executed. A built-in process-validator uses its pinned
validation profile and subject connections; it does not need an external MCP
tool binding. Backend preflight still determines whether it is configured.

For a digital-only handoff in an ordinary workspace, use the existing manually
reviewed local simulation. The `wright/test_handoff` binding is reserved for
explicitly enrolled integration tests; an ordinary workflow has no such authority.
Do not recommend account access or another MCP installation to repair that binding.
A simulation does not authorize a live transfer or grant engineering approval.

The supported task uses performed_by=`engineer`, step_type=`review`, and
settings.authoring_template=`external-action-approval`. For a printer package,
set action_kind=`printer_transfer`, approval_binding to
`{"server":"wright","tool":"local_simulate_handoff","schema":"7cfc91cfdf6bbeb9b1bc0307c93df6e04166c8cb27e253f3a95f50e3aa737e24"}`,
approval_destination to
`{"kind":"integration_test","id":"local-simulation://workspace"}`,
approval_settings to exactly `{"simulation":true}`, and approval_action to
`{"kind":"printer_transfer","mode":"local_simulation","simulation":true}`.
Use run_path_template=`wright.run-path/1` with an output_filename such as
`deliverables/{{wright.run_id}}/simulated-handoff.json` and a workspace_file output
port named `receipt`. Connect actual upstream-produced workspace_file outputs;
the runtime seals their exact identities and writes the receipt after a real
manual decision. It adds the resolved receipt_path itself. Do not insert a prior
receipt, synthesize a decision, enroll automatic reviews, or turn on live dispatch.
Preserve the original engineering requirements, review gates and output checks.
Change an incompatible saved declaration through a new CAS-checked revision,
then recheck readiness; a valid declaration alone proves no execution or approval.
