# Gate B Decision: Engineering Scenario Harness

**Decision**: Approved under the Engineering Capability Program's advance authorization.

**Selected architecture**:

- package-owned, versioned scenario/catalog resources;
- three Tier 1 deterministic multi-MCP Rivet graphs;
- existing Loop 069 Wright gateway, bindings, review, run authority, policy, lifecycle, cancellation, and evidence only;
- versioned artifact envelopes with explicit units, coordinates, lineage, and bounded payload/vault references;
- registry-based engineering assertion plugins with separate tool-completion and engineering-validity outcomes;
- additive SQLite report persistence linked to existing workflow runs;
- scenario library/preflight/report inside the current Rivet panel;
- selected Tier 2 real-package evidence only through disposable clean containers.

**Safety boundary**: Tier 1 is offline and deterministic. No scenario can command machinery, motion, heat, spindle, extrusion, printer, robot, or PLC. CAM/additive outputs are static evidence only. Credentials, network, proprietary applications, GPU, large assets, and host mutation require an explicit higher tier and never enter normal gates.

**Rollback**: Disable scenario routes and UI entry. Ordinary Rivet workflows, Loop 069 MCP execution, existing database readers, and the MCP catalog continue to operate. Migration 15 is additive; stored scenario report rows may remain inert.

**Gate C**: Deferred to the final Engineering Capability Program integration after Loop 073, where the exact dev merge gate runs once on the combined tree.

**Gate E**: Closed. No physical-system authorization is granted.
