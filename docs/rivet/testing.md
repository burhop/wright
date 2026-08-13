# Rivet workflow testing

Wright's normal Rivet suite is deterministic and local. It uses supervised fixture processes and fake MCP children; it does not require credentials, proprietary applications, paid services, network access, GPUs, or hardware.

## MCP gateway layers

- Contract tests cover canonical bindings, memory-only run authority, protocol-v2 validation, exact-call approval, redaction, and migration preservation.
- Integration tests run the pinned Node worker through Wright's gateway to two local MCP fixtures.
- Browser tests cover binding, review, approval, progress, cancellation, residue, and recovery with stable test IDs and accessibility scans.
- System tests start local FastAPI, the pinned worker, and two stdio fixture children.

## Optional live applications

Live probes never run by default:

- BREP requires `WRIGHT_RIVET_LIVE_BREP=1`, an already installed/current validated BREP server, and explicit workspace enablement.
- Solid Edge or another host bridge requires `WRIGHT_RIVET_LIVE_HOST=1`, a compatible host with its separately installed/current validated server, and explicit workspace enablement.

Do not install an application, accept a license, add credentials, contact a paid service, or mutate a proprietary host merely to make a probe pass. Live evidence must record the host, server revision, validation identity, operations attempted, cleanup status, and limitations. Physical actuation remains prohibited.
