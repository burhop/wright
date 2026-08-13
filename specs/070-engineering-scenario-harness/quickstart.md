# Quickstart: Rivet Engineering Scenario Harness

## Normal deterministic validation

1. Install Wright development dependencies using the repository's existing environment.
2. Run the scenario contract, catalog, artifact, assertion, persistence, service, API, and web component tests listed in `tasks.md`.
3. Start the local Wright API/web development surfaces with the existing Rivet MCP gateway feature enabled.
4. Open the Rivet workflows tab, select **Engineering scenarios**, and choose one of:
   - Structural bracket (CAD + Python + FEA)
   - Electronics enclosure cooling (ECAD + CAD + CFD + Python)
   - Parametric manufacturing (Grasshopper + additive/3MF + slicing + static CAM)
5. Review preflight. Tier 1 should show deterministic local fixture capabilities, no external dependency, and no physical actuation.
6. Review the generated workflow bindings using the existing Rivet review flow, run it, and inspect the engineering report.

Expected result: every scenario calls two or more independent fixture MCP servers through Wright, artifacts show exact provenance and units, assertions pass, and cleanup reports `clean`.

## Negative validation

Select a test fixture fault profile such as `unit_mismatch`, `non_converged`, `invalid_artifact`, `unsafe_cam`, `slow_cancel`, or `cleanup_residue`. The report must identify the exact node/capability/artifact and stable violated invariant. Missing/denied/stale bindings must stop before the child receives a call.

## Tier 2 clean-container validation

Tier 2 is never part of normal validation. Select only a confirmed, platform-compatible catalog entry and follow `docs/mcp-catalog/mcp-server-testing-process.md`. Run in a disposable clean container, record install/discovery/gateway/result/cleanup evidence, and classify unavailable credentials/applications as blocked rather than failure. Do not install MCP-specific host software or keep downloaded source/build output in the repository.

## Focused Loop 070 gate

Run formatting/lint for affected Python and web files, the Loop 070 contract/unit/integration/API/UI tests, catalog/package-resource tests, and `git diff --check`. The authoritative `scripts/check-dev-merge.sh` is deliberately run once after Loop 073 on the complete integration branch.
