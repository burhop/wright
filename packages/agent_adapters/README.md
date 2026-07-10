# Wright Agent Adapters

This internal package owns Wright's provider-neutral agent runtime interface and
provider-specific context/configuration adapters. It does not own workspace
persistence, generic workspace workflows, or the canonical MCP catalog.

Provider adapters receive application-owned content and paths through explicit
requests or callbacks; they must not import `workspace_service`, `data_vault`,
or API routes. The approved graph is enforced by
`architecture/python-packages.toml` and `tests/test_import_boundaries.py`.
