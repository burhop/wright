<!-- SPECKIT START -->
For additional context about technologies to be used, project structure,
shell commands, and other important information, read the current plan
at specs/047-python-oci-release-train/plan.md
<!-- SPECKIT END -->


Before merging a feature branch to `dev`, run `scripts/check-dev-merge.sh` or
document why a local host limitation prevented a specific gate. Before merging
`dev` to `main`, run `scripts/check-prod-merge.sh`. These scripts are the
merge-gate source of truth; when CI catches a failure that the scripts miss,
update the scripts and contributor docs in the same fix.

For engineering MCP server validation, follow the clean-container process in
docs/mcp-catalog/mcp-server-testing-process.md. Do not add MCP-specific host
software to the base Docker image just to make catalog validation pass.
