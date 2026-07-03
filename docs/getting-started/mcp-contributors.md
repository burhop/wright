# MCP Contributors

MCP contributors should start with the Docker appliance and the clean-container validation process.

1. Start Wright from a clean container.
2. Read the selected MCP catalog metadata.
3. Install only the selected server package and required free/open host dependencies.
4. Run protocol probes: `initialize`, `notifications/initialized`, `tools/list`, and one safe backend-touching probe.
5. Record setup recipes and blocked dependencies in the MCP catalog docs.

Do not add MCP-specific host software to the base image just to make a catalog entry pass.
