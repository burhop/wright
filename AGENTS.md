<!-- SPECKIT START -->
For additional context about technologies to be used, project structure,
shell commands, and other important information, read the current plan
at specs/060-rivet-wright-nodes/plan.md
<!-- SPECKIT END -->


Before merging a feature branch to `dev`, run `scripts/check-dev-merge.sh` or
document why a local host limitation prevented a specific gate. Before merging
`dev` to `main`, run `scripts/check-prod-merge.sh`. These scripts are the
merge-gate source of truth; when CI catches a failure that the scripts miss,
update the scripts and contributor docs in the same fix.

A production integration is not complete when the PR merges or the `main`
push checks pass. Follow `docs/release/release-runbook.md` and track the release
workflow through public PyPI verification, identical GHCR and Docker Hub
digests, published native lifecycle tests on Linux, macOS, and Windows,
versioned docs, and the GitHub Release published last. If a registry has just
accepted an artifact but public lookup fails, check for bounded propagation
delay and retry verification; never rebuild or republish the same version.

After merging `dev` to `main`, compare their Git tree hashes when checking
content synchronization. Different commit IDs are expected because `main`
contains PR merge commits; matching tree hashes mean the files match.

For engineering MCP server validation, follow the clean-container process in
docs/mcp-catalog/mcp-server-testing-process.md. Do not add MCP-specific host
software to the base Docker image just to make catalog validation pass.
