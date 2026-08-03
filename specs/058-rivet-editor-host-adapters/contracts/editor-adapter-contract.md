# Editor Adapter Contract v1

`bootstrap(session_id, workflow_slug)` returns availability, opaque grant ID,
workflow ID, revision and ETag after server-side identity resolution.
`read(grant)` and `save(grant, expected_revision, project, datasets)` validate
the scoped grant before delegating to persistence.

A grant provides no filesystem, tool, MCP, debugger, native, or credential
capability. Asset state is `disabled`, `missing`, `incompatible`, or
`available`; no unverified upstream file is served.
