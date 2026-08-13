# Dynamic Engineering MCP Catalog

Wright's engineering MCP list is a statused registry, not a hard-coded Docker
shopping list. The bundled recovery source lives in the package at:

`packages/tool_registry/src/tool_registry/catalog/engineering-catalog.yaml`

Consumers load the packaged catalog with
`tool_registry.canonical_catalog.load_canonical_entries()`. Network refreshes
use only an administrator-configured HTTPS channel and a Wright-pinned Ed25519
public key. Wright verifies the canonical signed envelope, content digest,
signer identity, expiry, increasing sequence, schema, identity rules, and
evidence rules before it offers an exact diff. Direct arbitrary-URL catalog
loading is disabled.

Activation stores immutable candidate, active, and previous snapshots and
reconciles catalog-owned metadata in one database transaction. It never
installs, starts, authenticates, or enables an MCP. Rollback selects the prior
verified snapshot while preserving custom entries, credential references,
explicit disablement, install/process state, and workspace grants. The bundled
catalog remains the final offline recovery root.

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

## Onshape Labs FeatureScript MCP evidence

The bundled catalog includes `onshape-labs-featurescript-mcp` as
`official_preview`, separately from the two community Onshape MCPs. The
classification is supported by Onshape's vendor-authored announcement:

- https://www.onshape.com/en/blog/featurescript-mcp-server-enables-text-code-cad

The announcement identifies the Onshape Labs FeatureScript MCP and the remote
streamable-HTTP endpoint `https://fs-mcp.labs.onshape.app/mcp`. The catalog
therefore records official publisher authority, but it does not claim
production maturity or successful Wright validation. Use requires the user to
complete any Onshape account, App Store subscription, license, and terms steps
independently. Catalog discovery, update activation, import, and machine
compatibility checks do not contact that endpoint.

Current external-validation status is deferred. Wright has not subscribed,
accepted terms, supplied credentials, initialized the remote server, listed
its tools, or run FeatureScript. A future credentialed validation must record
protocol evidence and a catalog-approved read-only probe through the Wright
gateway before the catalog validation status can advance. The community
`onshape-mcp-hedless` and `jarvis-onshape-mcp` records keep their independent
identities, credential names, source evidence, and validation histories.

### Signed update, rollback, import, and compatibility operations

For an administrator-managed update:

1. Configure an approved channel and matching public trust root in Wright's
   deployment configuration.
2. In **Capability Library**, choose **Check for updates** and review the signer,
   expiry, sequence, exact added/removed/changed fields, provenance, and risk
   counts.
3. Activate only the reviewed preview. Restart and confirm the same active
   snapshot id and user-owned state.
4. Use **Roll back** if the new metadata is unsuitable. Rollback changes the
   active catalog projection only.

Claude `mcpServers`, VS Code `servers`/`inputs`, and plain single-server JSON
can also be pasted into the add wizard. Import produces a redacted normalized
preview and discards the source; it does not execute a command or register a
server. Current-machine compatibility is a bounded local observation. Network
access, executable launches, credentials, and host changes require later,
explicit plan and validation steps.

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
