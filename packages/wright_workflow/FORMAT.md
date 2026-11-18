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
