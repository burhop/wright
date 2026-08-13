# Rivet workflow testing

Wright's normal Rivet suite is deterministic and local. It uses supervised fixture processes and fake MCP children; it does not require credentials, proprietary applications, paid services, network access, GPUs, or hardware.

## MCP gateway layers

- Contract tests cover canonical bindings, memory-only run authority, protocol-v2 validation, exact-call approval, redaction, and migration preservation.
- Integration tests run the pinned Node worker through Wright's gateway to two local MCP fixtures.
- Browser tests cover binding, review, approval, progress, cancellation, residue, and recovery with stable test IDs and accessibility scans.
- System tests start local FastAPI, the pinned worker, and two stdio fixture children.

The normal feature acceptance can be run without credentials or network access:

```text
uv run pytest packages/core/tests/test_rivet_mcp_contracts.py packages/data_vault/tests/test_rivet_mcp_persistence.py packages/workspace_service/tests/test_rivet_mcp_performance.py tests/security/test_rivet_mcp_secret_boundary.py tests/e2e/test_rivet_mcp_compatibility.py tests/e2e/test_rivet_mcp_gateway.py
npm --prefix integrations/rivet/runner test
npx playwright test tests/ui-integration/rivet-mcp-gateway.spec.ts --project=chromium
```

Distribution coverage builds the standalone wheel and sdist and checks the protocol-v2 manifest, pinned runner, JSON contracts, and migration/repository modules:

```text
uv run pytest tests/packaging/test_rivet_mcp_distribution.py
```

The performance suite measures 500-tool discovery, authority issuance, bridge p95, first progress, and cancellation delivery against the published local thresholds. It is deterministic evidence, not a substitute for the deferred five-engineer usability study.

## Optional live applications

Live probes never run by default:

- BREP requires `WRIGHT_RIVET_LIVE_BREP=1`, an already installed/current validated BREP server, and explicit workspace enablement.
- Solid Edge or another host bridge requires `WRIGHT_RIVET_LIVE_HOST=1`, a compatible host with its separately installed/current validated server, and explicit workspace enablement.

Do not install an application, accept a license, add credentials, contact a paid service, or mutate a proprietary host merely to make a probe pass. Live evidence must record the host, server revision, validation identity, operations attempted, cleanup status, and limitations. Physical actuation remains prohibited.

Engineering MCP catalog validation follows the clean-container process in `docs/mcp-catalog/mcp-server-testing-process.md`. Do not add MCP-specific host software to Wright's base image to make a catalog entry pass. Catalog clean-container probes validate candidate servers; they do not replace the Rivet-to-Gateway system smoke.

See [Rivet MCP gateway](mcp-gateway.md) for operator setup, security boundaries, troubleshooting, evidence, and rollback.
