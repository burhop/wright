# Native Wright workflow profile

This profile describes Wright's existing UTF-8 `.workflow.wflow` syntax and the JSON transfer envelope `wright.workflow-bundle/1`. Its implementation baseline is public Wright commit `4f370caa9743f869f769f8c8e2332b6b63be438b`. The interchange requirements are an [October 2026 draft](https://github.com/burhop/engineering-process-spec/blob/8930173ff4b632199cfe844360aa0de921a5e338/spec/interchange-draft.md). The September CWL experiment is a different format.

## Representation

A source document has named `workflow`, `task`, `input`, `item`, `group` and `connection` sections. Each opens with a section kind, a space and a lower snake case identifier, followed by indented named fields. A field value is JSON or a bare lower snake case name. A line containing `end` closes the section. Blank lines and full-line comments beginning with `#` are ignored for interpretation. Duplicate fields and duplicate declarations of the same kind and identity are errors.

Retain the original bytes, comments, line endings and instruction bodies. Hash exact source bytes with SHA-256. For existing structured bundle digests, use compact, key-sorted, finite UTF-8 JSON with non-ASCII characters preserved. The two digests identify different subjects. A new source revision cannot reuse approval of a prior revision.

One executable graph contains one workflow and 1–32 tasks. Inputs and tasks have named input/output ports. An `item` connection links a specific producer port to a consumer input. An `order` connection constrains task order. A visual group has no execution effect. Reject missing endpoints, mismatched port direction, a disconnected process, or an unsupported cycle before calling any tool.

## Features and acceptance cases

| Construct | Reader and execution rule |
| --- | --- |
| Fixed MCP call | Bind an exact configured provider and its tool contract, validate argument mappings, then invoke through that connection. A name or matching schema alone does not authorize a provider substitution. |
| File or structured result handoff | Verify the bytes or exact structured value attributed to the producing step and output port. A stale file with a plausible name cannot satisfy a new call. |
| Inputs and declared waits | Resolve caller input, explicit default, upstream production or a declared human decision. Bind a waiting response to its pending subject and continue the same run. |
| Optional layout, saved instructions and interface metadata | Preserve their identities. Reading a definition neither runs anything nor activates imported interface code. |
| Required AI, validator, engineering review or external-action capability | Preserve the requirement. A host must supply a compatible qualified handler before executing it. A missing required capability blocks readiness. |
| Failed and uncertain tool calls | Record the native cause, retain verified upstream evidence, and hold downstream work. A lost acknowledgement of a possible external mutation cannot trigger replay on restart. |

The bundle is a JSON object with `schema_version`, `mode`, accepted `source`, its `source_digest`, and inventories for declared dependencies, optional assets and optional interface source. Preserve the existing export wrapper carrying `bundle` and `bundle_digest`. Integrity, executable validity, local readiness and engineering acceptance are separate checks. Transferring a definition does not transfer live runs, credentials, stored answers, grants, accepted reviews or trusted UI builds.

Initial conformance cases exercise exact-byte hashes across LF/CRLF and Unicode, duplicate or incomplete declarations, missing provider identity, two configured providers exchanging the first call's output, and stopped runs with partial evidence. The engineering application additionally verifies compatibility with its existing authoring, validation and review contracts.

## Run the two-provider example

Install the built `wright-workflow` wheel in a Python 3.11+ environment. The source distribution contains `examples/handoff`. From its parent directory, use that environment's Python and entry point.

```console
python handoff/configure.py bindings.json
wright-workflow parse handoff/length.workflow.wflow
wright-workflow run handoff/length.workflow.wflow --bindings bindings.json --run-dir runs/length
```

The example starts two local stdio MCP servers. The writer produces `points.csv`. The reader receives the writer's named port, reads the file, and reports its SHA-256 and a length of 5 mm. The receipt identifies both tool contracts and the producing attempt. Reopening the same completed run returns its existing receipt.

The caller's binding file supplies the executable, arguments, reviewed program file hashes and permitted tools for each logical server. Keep the binding file under local control. A portable step carries `mcp_binding` with version `wright.mcp-binding/1`, provider name, reported build, upstream tool name and tool contract digest. The digest covers the SDK's wire representation of name, input/output schemas, annotations, metadata and execution declarations when present. Provider/build qualification and the executable's reviewed bytes are checked separately. Historical `mcp_schema_digest` continues to identify the gateway-qualified name, server revision, schemas, approval requirements and Wright adapter metadata.

A declared human-input barrier yields `waiting_input`. To answer, put the pending subject and the typed `value` in a JSON object, then run `wright-workflow resume --run-dir runs/length --bindings bindings.json --response answer.json`. Completed answers reconcile by subject and value. A failed tool response stops downstream calls. An interrupted dispatch records `outcome_unknown` and keeps its attempt ID. Use the provider's evidence to investigate that attempt. A repeated run command returns the saved hold.
