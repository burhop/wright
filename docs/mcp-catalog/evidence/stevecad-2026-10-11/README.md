# SteveCAD connection evidence — 11 October 2026

Observed on native Windows using isolated state and the existing Wright source
registry, installer, OAuth transport and gateway. Provider initialize reported
**STEVE CAD 4.0.10**, MCP **2025-11-25**.

| Receipt | Scope |
| --- | --- |
| registration.json | Exact official endpoint and isolated registration |
| native-initialize.json | Actual provider initialize response and instructions |
| native-tools.json | 26 discovered live tool definitions |
| native-list-skills.json | Successful read-only skill discovery |
| native-api-reference.json | Successful read-only API discovery |
| gateway-discovery.json | 26 tools exposed through Wright's gateway |
| gateway-api-reference.json | Live proxied `api_reference(Model.box)` response |
| gateway-summary.json | Gateway result and redacted audit events |
| workspace-summary.json | Normal isolated API/UI returned 200; SteveCAD installed and active with 26 tools |

The gateway probe uses the repository's qualification workspace/audit ports with
the real database catalog, engine lifecycle and remote provider. The workspace
receipt separately uses the normal running Wright API on port 8891. No CAD
geometry, solver correctness, clean-container qualification or user engineering
acceptance is established by these read-only calls.

Final checks: **17 passed** in the existing engineering-catalog, catalog-resource,
platform and normalization suites; `git diff --check` passed. The expected
catalog cardinality was updated from 81 to 82. Credentials and local API tokens
remain in ignored runtime state and are absent from these receipts.
