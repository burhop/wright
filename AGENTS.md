<!-- SPECKIT START -->
For additional context about technologies to be used, project structure,
shell commands, and other important information, read the current plan
at specs/082-output-content-validation/plan.md

Feature 082 is a runtime process-output validator with actionable AI correction
feedback and report-consumable results. Read its scope-amendment.md, quickstart.md
and implementation-goal.md. Earlier 081 content-validation analysis is reference
material. Submitting the revised goal approves replacing its all-30-output G0 gate
with per-subject checks. Implementation starts after human plan approval. Preserve
the separate generation campaign; use isolated runs for validator/rework
demonstrations. The reporting UI
belongs to another branch; publish a shared result contract here.
<!-- SPECKIT END -->

Before selecting, describing, changing, or evaluating engineering workflow
examples or planning their campaign, read
`docs/design/engineering-demonstration-principles.md`. Wright's central
demonstration is an extended process using multiple existing engineering tools
through MCP servers, with actual engineering outputs handed between meaningful
stages to accomplish an overall job. A long graph, valid files, or campaign
counts alone do not establish demonstration value. Show engineering tools and
their contributions; keep software plumbing secondary. Align and reuse the
existing 30 examples, not a wholesale rewrite without explicit agreement.

Before changing the workflow/process editor or its workspace entry point, read
`docs/contributing/workflow-ui-integration.md`. Locate the latest reviewed UI
implementation and preserve its authoring capabilities when integrating runtime
work. Verify the served build through the workspace Workflow/Workflows control;
component tests or a separate editor route alone do not establish UI completion.


Before every push to a branch with a pull request targeting `dev`, read
`docs/contributing/dev-push-runbook.md` and run `scripts/check-dev-push.ps1`
on Windows or `scripts/check-dev-push.sh` on Unix. Direct pushes to `dev` are
not supported. Before merging a feature branch to `dev`, run
`scripts/check-dev-merge.ps1` on Windows or `scripts/check-dev-merge.sh` on Unix,
or document why a local host limitation prevented a specific gate. Before merging
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
