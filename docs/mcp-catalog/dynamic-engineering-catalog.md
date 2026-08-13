# Dynamic Engineering MCP Catalog

Wright's engineering MCP list is a statused registry, not a hard-coded Docker
shopping list. The canonical source lives in GitHub at:

`packages/tool_registry/src/tool_registry/catalog/engineering-catalog.yaml`

Consumers can load the packaged catalog with
`tool_registry.canonical_catalog.load_canonical_entries()` or a GitHub-hosted
copy with `load_canonical_entries_from_url(url)`. Use the raw file URL for the
branch or release channel that the appliance should follow, then fall back to
the packaged catalog if the network is unavailable.

## Required Metadata

Each server records:

- identity, provider, domain tags, transport, command, locality, and weight
- repository, package, container, license, auth model, install method, and
  maturity
- capability summary and primary-source records with observation dates
- runtime requirements, including CPU, GPU, memory, and Docker support
- platform support for `windows_11_x64`, `linux_x64`, `linux_arm64`,
  `macos_x64`, and `macos_arm64`
- validation status and the clean-container environment where a pass occurred

Do not infer ARM64 support from generic Linux support. GB10 uses
`linux_arm64`, and an MCP stays a candidate until a GB10 or equivalent clean
Linux ARM64 validation run records evidence.

## Platform Selection

`tool_registry.catalog_platforms` defines Wright's current managed image
targets:

| Target | Platform key | Docker platform | Bundle |
|---|---|---|---|
| `linux-amd64` | `linux_x64` | `linux/amd64` | `docker/mcp-bundle.yaml` |
| `gb10-linux-arm64` | `linux_arm64` | `linux/arm64` | `docker/mcp-bundle.linux-arm64.yaml` |
| `windows-amd64` | `windows_11_x64` | `windows/amd64` | `docker/mcp-bundle.windows-amd64.yaml` |

Selection modes:

- `strict`: only platform status `yes`
- `candidate`: `yes` or `likely`
- `host`: `yes`, `likely`, or `host-dependent`

Docker image bundles set `catalog_policy.require_docker: true`, so a locally
installed server must also declare runtime Docker support as `yes` or
`partial`. Windows desktop bridges can use `host` mode when the image ships the
MCP launcher but the CAD application/license remains external.

## Bundle Contract

Every `local_enabled` MCP server in a Docker bundle must include a
`catalog_id`. `docker/mcp/verify-bundle.py` resolves that entry from the
canonical catalog and rejects the bundle when the server is not compatible with
the bundle's `target_platform`.

This keeps the image manifests explicit while still letting Wright grow the
GitHub-backed registry quickly. The installer only installs servers present in
the selected bundle; the verifier prevents accidental inclusion of MCPs that
are blocked, architecture-unknown, non-Docker, or desktop-only for the target.

## Refresh Workflow

Use this loop for new CAD, CAM, FEA, CFD, meshing, manufacturing, and
engineering-data MCPs:

1. Record only primary sources: vendor docs, official repositories, package
   metadata, container images, or validation evidence.
2. Add or update the catalog entry with source records, platform support, and
   runtime requirements.
3. Mark untested GB10/Linux ARM64 support as `unknown` unless there is strong
   runtime evidence; use `likely` only when the Docker/runtime pieces are
   architecture-neutral or have an ARM64 artifact.
4. Add setup notes or follow-up records when a server needs proprietary CAD,
   license servers, GPUs, tenants, or machine-control hardware.
5. Run the schema, catalog, and bundle tests.
6. For installable candidates, follow
   `docs/mcp-catalog/mcp-server-testing-process.md` in a clean container and
   attach the evidence before marking validation `passed`.

The scheduled `MCP catalog validation` GitHub workflow runs weekly and on
catalog/bundle changes. It validates schema resources, packaged distribution
resources, Docker bundle manifests, and target-platform compatibility. It does
not install proprietary CAD/CAM/CAE software or broaden the base image; live
host-software validation remains a separate evidence-producing task.

## Current Research Additions

Recent primary-source additions include official Autodesk Product Help, Fusion
desktop/data MCPs, official MathWorks MATLAB and Simulink MCP tooling,
OpenFOAM, multiple FreeCAD variants, Rhino, Blender, BREP, SolidEdgeMCP,
Microsoft Playwright MCP for browser-driven Wright/CAD UI testing, Rescale's
hosted simulation MCP, Ansys/PyFluent MCP tooling, COMSOL community MCPs,
NVIDIA Omniverse MCP servers, and high-priority API/watchlist candidates such
as Backflip, SimScale, and Flexcompute Flow360.

Primary-source ledger for the latest sweep:

- Autodesk MCP docs: https://help.autodesk.com/view/ADSKMCP/ENU
- MATLAB MCP server: https://github.com/matlab/matlab-mcp-server
- Simulink Agentic Toolkit: https://github.com/matlab/simulink-agentic-toolkit
- OpenFOAM MCP server: https://github.com/webworn/openfoam-mcp-server
- FreeCAD full-module MCP: https://github.com/sergiudanstan/freecad-mcp
- FreeCAD Docker/headless MCP: https://github.com/proximile/FreeCAD-MCP
- Rhino MCP: https://github.com/easehee/rhino-mcp
- Blender MCP: https://github.com/harveyxiacn/blender-mcp
- BREP CAD package source: https://github.com/andymai/brepjs
- Playwright MCP: https://github.com/microsoft/playwright-mcp
- Zoo.dev MCP docs: https://zoo.dev/docs/developer-tools/mcp
- Rescale MCP docs: https://rescale.com/documentation/mcp-server-getting-started/
- Ansys PyFluent MCP: https://github.com/ansys/pyfluent-mcp
- PyFluent-MCP docs: https://fluent-mcp.docs.pyansys.com/
- Community Ansys MCP package: https://pypi.org/project/ansys-mcp-server/
- COMSOL community MCP: https://github.com/wjc9011/COMSOL_Multiphysics_MCP
- COMSOL Desktop/RAG MCP: https://github.com/Suzy-Sa/COMSOL-Multiphysics-MCP
- NVIDIA Omniverse Kit USD Agents MCPs: https://github.com/NVIDIA-Omniverse/kit-usd-agents
- NVIDIA Omniverse Kit-CAE skills: https://github.com/NVIDIA-Omniverse/kit-cae
- NVIDIA CUDA Docs MCP registry entry: https://registry.modelcontextprotocol.io/v0.1/servers?search=nvidia&version=latest
- Backflip AI product/downloads: https://www.backflip.ai/
- SimScale API and SDK docs: https://www.simscale.com/docs/platform/api-and-sdk-documentation/
- Flexcompute Flow360 Python API: https://github.com/flexcompute/Flow360

Recommended next validations:

- GB10 clean-container validation for OpenSCAD, FreeCAD, BREP, and Playwright
- Linux x64 clean-container validation for OpenFOAM and the newer FreeCAD/Rhino
  community servers
- Remote credentialed probes for Rescale and NVIDIA CUDA Docs MCPs
- Docker startup and read-only tool probes for NVIDIA Omniverse Kit/USD/OmniUI/
  Isaac Sim MCPs. GB10 local preflight has already built the USD Code wheels,
  but `NVIDIA_API_KEY` and Docker/MCP startup evidence are still needed.
- Gateway validation for NVIDIA Elements MCP. Clean Wright ARM64 validation
  initialized the npm MCP, listed 18 tools, and called `skills_list`.
- Gateway validation plus licensed-host validation for Ansys PyFluent MCP. Clean
  Wright ARM64 validation initialized the package, listed 25 tools, and returned
  a clean disconnected `session_status`.
- Upstream fixes before retesting `ansys-mcp-server-community` and
  `comsol-multiphysics-mcp-suzysa`; both currently fail before MCP
  initialization against the resolved MCP SDK.
- Slim-install and license/content review before validating
  `comsol-multiphysics-mcp-wjc9011`; its source checkout includes COMSOL PDFs
  and models, and its dependency graph pulls a large PyTorch/CUDA stack.
- Windows host validation for SolidEdgeMCP and SolidWorks MCPs, with CAD
  licenses kept outside the redistributed image
- Credential-limited remote probes for Autodesk Fusion Data, APS, Zoo.dev, and
  other cloud CAD APIs
- Wrapper design decisions for Backflip, SimScale, and Flexcompute Flow360 if
  no public MCP appears
