# MATLAB MCP Server follow-up

Reviewed 9 September 2026. Owner: Wright catalog maintainers. Next review:
9 October 2026.

MathWorks' official MATLAB MCP Server is a high-value simulation and analysis
candidate. The current reviewed release is v0.13.0. Its Linux x64 vendor binary
has SHA-256 `07946705e488e9e13034bf1a08f6598e685bad30d5d78b93934cbe3002250704`.

A fresh disposable Intel Linux Wright container produced two preserved attempts:

- `matlab-v0.13.0-preflight.json` initialized the native vendor binary and
  captured five valid tool schemas.
- `matlab-v0.13.0-linux.json` repeated initialization and called the read-only
  `detect_matlab_toolboxes` tool. The MCP returned the expected blocker,
  `no valid MATLAB environments found`, and shut down cleanly.

This is protocol and dependency evidence only. It does not prove MATLAB
calculation, Simulink, Wright gateway operation, or engineering output. Keep the
server in Follow up.

To resume qualification, install a licensed MATLAB R2021a or later outside the
Wright base image, set `MW_MCP_SERVER_MATLAB_ROOT`, and rerun the v0.13.0 binary.
The acceptance task should execute a deterministic numerical analysis through
Wright `GatewayService`, write a workspace-scoped MAT or CSV result, inspect that
artifact independently, exercise a controlled error and timeout, and verify
process cleanup. Record the host version and license boundary without storing
license data.

Primary sources:

- https://github.com/matlab/matlab-mcp-server
- https://github.com/matlab/matlab-mcp-server/releases/tag/v0.13.0
