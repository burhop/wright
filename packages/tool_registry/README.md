# wright-tool-registry

`wright-tool-registry` contains Wright's Model Context Protocol catalog models, engineering tool schemas, stdio runner integration, validation metadata, and safety policy helpers.

The main Wright repository is the source of truth for development, issues, documentation, and releases:

- Source: https://github.com/burhop/wright/tree/main/packages/tool_registry
- Issues: https://github.com/burhop/wright/issues
- Documentation: https://burhop.github.io/wright/
- Releases: https://github.com/burhop/wright/releases

This package depends on `wright-core` and is published so the Wright Hermes plugin mirror can remain thin while still using the canonical tool registry implementation.
