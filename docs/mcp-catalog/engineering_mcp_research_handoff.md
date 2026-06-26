# Engineering MCP Server Research Handoff

Generated: 2026-06-26
Audience: Hermes / OpenClaw coding agent
Purpose: Build a plugin-managed registry for discovering, installing, configuring, launching, testing, and safely using engineering-focused Model Context Protocol (MCP) servers.

> This is a corrected research handoff, not a claim that every row is a verified installable MCP server. Rows are explicitly marked as verified, user/catalog-reported, wrapper candidates, capability aliases, UI/standard infrastructure, watchlist, or excluded. Unknown platform support is intentionally recorded as `unknown`, not silently treated as supported.

---

## 1. Executive Summary

The previous shortlist missed visible engineering MCP entries and collapsed too many categories into one bucket. The correct product artifact is a **statused engineering MCP registry** with source URLs, install confidence, platform compatibility, risk level, and verification status.

Important corrections:

1. **OpenSCAD MCP entries must be seeded manually.** OpenSCAD Geometry, OpenSCAD Linter, Web OpenSCAD, and WebMCP-OpenSCAD should be catalog entries even if their public MCP URLs still need verification. OpenSCAD is highly valuable for deterministic, script-first CAD workflows.
2. **Autodesk Product Help MCP should be treated as a documentation/help MCP.** It should not be mixed with Fusion/Revit/Inventor automation servers.
3. **Zoo.dev Cloud CAD MCP is a verified official MCP and should be included.** It has official docs and an install path using `uvx zoo-mcp` with `ZOO_API_TOKEN`.
4. **FreeCAD has multiple MCP variants.** Some entries in prior catalogs are probably capability groups under a FreeCAD backend rather than separate MCP servers.
5. **Wrapper candidates are not MCP servers.** APIs such as Autodesk APS, Onshape, PTC ThingWorx, CREOSON, SolidWorks API/Document Manager, etc. are valuable, but should not be marked installable MCPs until wrapped or verified.
6. **Platform support must be explicit by architecture.** `Linux` is not enough. Track `windows_11_x64`, `linux_x64`, `linux_arm64`, `macos_x64`, and `macos_arm64` separately.
7. **Machine-control integrations are safety-critical.** Printer, robot, CNC, PLC, OPC UA, Modbus, MTConnect, MQTT, and Snap7 entries must default to disabled or read-only/simulation mode.

Recommended first support tiers:

| Priority | Entries |
|---|---|
| P0 verified/installable | Zoo.dev Cloud CAD MCP, BlenderMCP, FreeCAD MCP variants |
| P0 seed, blocked on URL | OpenSCAD Geometry, OpenSCAD Linter, Autodesk Product Help MCP |
| P1 verified/community | KiCad MCP, ROSBag MCP |
| P1 wrapper candidates | CREOSON / Creo, Onshape API, Autodesk APS, SolidWorks APIs, PTC ThingWorx |
| P2/P3 safety-gated | WinCC, PLC/OPC UA/Modbus/Snap7/MTConnect, printer/slicer/robot integrations |
| Infrastructure, not engineering servers | MCP-UI, WebMCP Standard, React Three Fiber/Web3D-style UI entries |

---

## 2. Verification States

Use these states in the registry:

| State | Meaning | Plugin behavior |
|---|---|---|
| `verified_mcp` | Primary source confirms an MCP server and install/launch path. | Eligible for install manager and health check. |
| `verified_docs_mcp` | Primary source confirms a documentation/help MCP. | Eligible for docs/search integration; read-only by default. |
| `community_mcp` | Community repo appears real and usable, with install docs. | Eligible after safety review and platform probe. |
| `user_reported_url_needed` | Known from user/prior catalog, but exact URL/package not verified here. | Keep in catalog; block automated install until URL is pinned. |
| `verified_api_wrapper_candidate` | Real engineering API/bridge exists, but no verified MCP server. | Use as roadmap/custom wrapper candidate. |
| `capability_alias` | Entry appears to be a capability under another MCP server. | Do not count as separate server unless distinct source URL exists. |
| `ui_or_web_standard` | Useful for Hermes UI/web-agent integration, but not an engineering MCP server. | Track separately from engineering server catalog. |
| `watchlist` | Plausible, unverified, vendor roadmap, or safety-sensitive candidate. | Keep metadata; no default install. |
| `excluded` | No MCP implementation, stale, unsafe, toy-only, unclear, or no engineering value. | Do not expose in UI except debug/audit mode. |

---

## 3. Platform Status Values

Use these values per OS/architecture:

| Value | Meaning |
|---|---|
| `yes` | Verified support from docs or successful test. |
| `likely` | Strong evidence based on runtime/host availability, but not tested. |
| `host-dependent` | Depends primarily on desktop app, CAD license, vendor tenant, or hardware controller. |
| `unknown` | Cannot determine; must be tested. |
| `no` | Known unsupported or impractical. |

Required platform keys:

```json
{
  "windows_11_x64": { "status": "yes | likely | host-dependent | unknown | no", "tested": false, "notes": "" },
  "linux_x64": { "status": "yes | likely | host-dependent | unknown | no", "tested": false, "notes": "" },
  "linux_arm64": { "status": "yes | likely | host-dependent | unknown | no", "tested": false, "notes": "" },
  "macos_x64": { "status": "yes | likely | host-dependent | unknown | no", "tested": false, "notes": "" },
  "macos_arm64": { "status": "yes | likely | host-dependent | unknown | no", "tested": false, "notes": "" }
}
```

Special note for Dell GB10 / non-Intel Linux: even when a README says “Linux,” set `linux_arm64` to `unknown` until tested. Native wheels, host-app binaries, Qt/GUI dependencies, Docker image manifests, and CAD plug-ins often fail on ARM64.

---

## 4. Corrected Seed Catalog

### 4.1 High-priority verified or strongly seeded entries

| Canonical ID | Display name | Verification state | Source / install URL | Install / launch notes | Deployment mode | Windows 11 x64 | Linux x64 | Linux ARM64 | Risk | Plugin action |
|---|---|---:|---|---|---|---:|---:|---:|---:|---|
| `zoo_cloud_cad_mcp` | Zoo.dev Cloud CAD MCP | `verified_mcp` | https://zoo.dev/docs/developer-tools/mcp | `uvx zoo-mcp`; requires `ZOO_API_TOKEN`. | cloud API via local MCP | likely | likely | unknown | medium | Include P0/P1; require token vault. |
| `blender_mcp_ahujasid` | BlenderMCP | `community_mcp` | https://github.com/ahujasid/blender-mcp | `uvx blender-mcp`; requires Blender add-on, Blender 3.0+, Python 3.10+, uv. | local bridge to desktop app | yes | yes | unknown | high | Include P0/P1; disabled by default due Python execution. |
| `freecad_mcp_neka_nat` | FreeCAD Engineering MCP | `community_mcp` | https://github.com/neka-nat/freecad-mcp | Install FreeCAD add-on, start RPC server, configure MCP with `uvx freecad-mcp`. | local bridge to desktop app | yes | yes | unknown | high | Include P1; disabled by default due Python execution/model writes. |
| `freecad_mcp_contextform` | FreeCAD Copilot / FreeCAD MCP | `community_mcp` | https://github.com/contextform/freecad-mcp | `npm install -g freecad-mcp-setup@latest`; `npx freecad-mcp-setup setup`. | local bridge to desktop app | yes | yes | unknown | high | Include P1; alternative FreeCAD backend. |
| `openscad_geometry_mcp` | OpenSCAD Geometry | `user_reported_url_needed` | MCP URL: TBD. OpenSCAD host: https://openscad.org/downloads.html | Host install examples: Windows `winget install OpenSCAD.OpenSCAD`; Debian/Ubuntu `apt install openscad`; AppImage/Docker available. MCP install unknown. | likely local-only or local bridge | host yes; MCP unknown | host yes; MCP unknown | host likely; MCP unknown | medium | Seed P0; block install until MCP URL verified. |
| `openscad_linter_mcp` | OpenSCAD Linter | `user_reported_url_needed` | MCP URL: TBD. OpenSCAD docs: https://openscad.org/documentation.html | Exact MCP install unknown. | likely local-only/docs+analysis | host yes; MCP unknown | host yes; MCP unknown | host likely; MCP unknown | low/medium | Seed P0/P1; block install until URL verified. |
| `autodesk_product_help_mcp` | Autodesk Product Help MCP | `user_reported_url_needed` | MCP URL: TBD. Autodesk Help: https://help.autodesk.com/ | Treat as documentation/help MCP, not desktop automation. | docs-only / remote likely | likely | likely | likely | read-only | Seed P0; verify primary Autodesk URL. |
| `kicad_mcp_lamaalrajih` | KiCad MCP | `community_mcp` | https://github.com/lamaalrajih/kicad-mcp | Clone, `make install`, configure Python venv / `main.py`; requires KiCad 9.0+, Python 3.10+, uv. | local bridge / local project analyzer | yes | yes | unknown | medium | Include P1; read-only mode preferred. |
| `rosbag_mcp_binabik` | ROSBag MCP | `community_mcp` | https://github.com/binabik-ai/mcp-rosbags | Clone, create Python venv, install requirements; optional ROS 2 extras. | local file analyzer | maybe | yes | unknown | low/medium | Include P1 for offline robotics data. |
| `siemens_xcelerator_developer_portal_mcp` | Siemens Xcelerator Developer Portal MCP | `verified_docs_mcp` | https://developer.siemens.com/ | Siemens site advertises an MCP server for developer-portal documentation, product/API discovery, and resource retrieval. Exact client config URL should be captured from “Learn more.” | docs-only / remote likely | likely | likely | likely | read-only | Include P0/P1 docs integration once config URL pinned. |

### 4.2 User-provided catalog reconciliation

| Entry from previous research | Canonical ID | Reconciliation | Best source / install URL found | Windows 11 x64 | Linux x64 | Linux ARM64 | Risk | Plugin action |
|---|---|---:|---|---:|---:|---:|---:|---|
| OpenSCAD Geometry | `openscad_geometry_mcp` | `user_reported_url_needed` | MCP TBD; host: https://openscad.org/downloads.html | host yes; MCP unknown | host yes; MCP unknown | host likely; MCP unknown | medium | Seed P0; verify MCP URL. |
| OpenSCAD Linter | `openscad_linter_mcp` | `user_reported_url_needed` | MCP TBD; docs: https://openscad.org/documentation.html | host yes; MCP unknown | host yes; MCP unknown | host likely; MCP unknown | low/medium | Seed P0/P1; verify MCP URL. |
| FreeCAD Engineering | `freecad_mcp_neka_nat` / `freecad_mcp_contextform` | `community_mcp` or alias | https://github.com/neka-nat/freecad-mcp ; https://github.com/contextform/freecad-mcp | yes | yes | unknown | high | Include; normalize variants. |
| FreeCAD Copilot | `freecad_mcp_contextform` | `community_mcp` | https://github.com/contextform/freecad-mcp | yes | yes | unknown | high | Include P1. |
| FreeCAD Robust | `freecad_robust_mcp` | `user_reported_url_needed` | TBD | unknown | unknown | unknown | high | Seed only until URL exists. |
| FreeCAD Core | capability under FreeCAD backend | `capability_alias` | https://github.com/neka-nat/freecad-mcp | yes | yes | unknown | high | Do not count separately unless distinct URL. |
| FreeCAD Booleans | capability under FreeCAD backend | `capability_alias` | https://github.com/contextform/freecad-mcp | yes | yes | unknown | high | Do not count separately unless distinct URL. |
| CAiD OpenCASCADE | `caid_opencascade_mcp` | `user_reported_url_needed` / wrapper candidate | TBD | unknown | unknown | unknown | medium/high | Seed P2/P3; verify source. |
| Zoo.dev Cloud CAD | `zoo_cloud_cad_mcp` | `verified_mcp` | https://zoo.dev/docs/developer-tools/mcp | likely | likely | unknown | medium | Include P0/P1. |
| Onshape MCP | `onshape_mcp` | `user_reported_url_needed`; API verified | MCP TBD; API: https://onshape-public.github.io/docs/api-intro/ | likely if API-based | likely if API-based | unknown | medium | Seed; wrapper candidate until MCP URL supplied. |
| CalculiX Simulation | FreeCAD FEM capability or standalone TBD | `capability_alias` / wrapper candidate | FreeCAD FEM via https://github.com/neka-nat/freecad-mcp | host-dependent | host-dependent | unknown | medium/high | Model as FreeCAD capability unless separate MCP exists. |
| Autodesk Platform Services | `autodesk_aps_api_wrapper` | `verified_api_wrapper_candidate` | https://aps.autodesk.com/ | likely API | likely API | likely API | medium | P1 custom wrapper candidate. |
| Autodesk APS Community | `autodesk_aps_community_mcp` | `user_reported_url_needed` | TBD | unknown | unknown | unknown | medium | Seed only. |
| Siemens Element Design System | `siemens_element_design_system` | `ui_or_web_standard`, not engineering MCP | https://developer.siemens.com/resources/design-systems/overview.html | likely | likely | likely | read-only | Do not count as engineering MCP; useful UI/docs asset. |
| Siemens WinCC Unified | `siemens_wincc_unified_mcp` | `user_reported_url_needed` / industrial wrapper candidate | TBD | host-dependent | host-dependent | unknown | safety-critical | Watchlist; default disabled. |
| PTC ThingWorx IoT | `ptc_thingworx_wrapper` | `verified_api_wrapper_candidate` | https://www.ptc.com/en/products/thingworx | tenant-dependent | tenant-dependent | tenant-dependent | high/safety-critical | P2 custom wrapper candidate. |
| Autodesk Fusion 360 | `autodesk_fusion_mcp` | `user_reported_url_needed` / host bridge candidate | MCP TBD; product/docs: https://www.autodesk.com/products/fusion-360/overview | host yes Windows/macOS; MCP unknown | no native desktop; browser/API possible | unknown | high | Seed P1/P2; verify source. |
| SolidWorks MCP (Python) | `solidworks_mcp_python` | `user_reported_url_needed` | TBD | host-dependent likely Windows | no/unknown | no/unknown | high | Seed only. |
| SolidWorks MCP (TypeScript) | `solidworks_mcp_typescript` | `user_reported_url_needed` | TBD | host-dependent likely Windows | no/unknown | no/unknown | high | Seed only. |
| SolidWorks API Docs | `solidworks_api_docs` | docs/API candidate; MCP not verified | https://help.solidworks.com/ | likely docs | likely docs | likely docs | read-only | Include as docs candidate only if MCP wrapper exists. |
| PTC Creo Parametric | `ptc_creo_creoson_wrapper` | wrapper candidate via CREOSON; MCP not verified | https://github.com/SimplifiedLogic/creoson | host-dependent likely Windows | unknown/no practical desktop | unknown/no practical desktop | high | P1 custom wrapper candidate. |
| Rhino 3D (McNeel) | `rhino3d_mcp` | `user_reported_url_needed` | TBD | host-dependent | host-dependent | unknown | medium/high | Seed only. |
| Blender 3D | `blender_mcp_ahujasid` | `community_mcp` | https://github.com/ahujasid/blender-mcp | yes | yes | unknown | high | Include P0/P1. |
| SketchUp 3D | `sketchup_mcp` | `user_reported_url_needed` | TBD | host-dependent | unknown/browser possible | unknown | medium/high | Seed only. |
| Autodesk Revit BIM | `autodesk_revit_mcp` | `user_reported_url_needed` / host bridge candidate | MCP TBD; product/docs: https://www.autodesk.com/products/revit/overview | host yes | no native desktop | no native desktop | high | Seed P2; Windows-only host assumption until proven otherwise. |
| AutoCAD MCP | `autocad_mcp` | `user_reported_url_needed` | MCP TBD; product/docs: https://www.autodesk.com/products/autocad/overview | host yes | no native desktop | no native desktop | high | Seed only. |
| Easy-MCP-AutoCAD | `easy_mcp_autocad` | `user_reported_url_needed` | TBD | unknown | unknown | unknown | high | Seed only; verify repo. |
| MultiCAD MCP | `multicad_mcp` | `user_reported_url_needed` | TBD | unknown | unknown | unknown | high | Seed only; verify repo. |
| CAD-MCP Universal | `cad_mcp_universal` | `user_reported_url_needed` | TBD | unknown | unknown | unknown | high | Seed only; verify repo. |
| WebMCP Standard | `webmcp_standard` | `ui_or_web_standard`, not conventional engineering MCP | https://arxiv.org/abs/2508.09171 | browser/web | browser/web | browser/web | low/medium | Track as web-agent standard, not engineering server. |
| MCP-UI (Shopify) | `mcp_ui` | `ui_or_web_standard`, not engineering MCP | https://github.com/idosal/mcp-ui | likely | likely | likely | low | Use for Hermes/OpenClaw UI resources, not CAD server. |
| Web3D MCP (React Three Fiber) | `web3d_react_three_fiber_mcp` | `user_reported_url_needed` / UI candidate | TBD; R3F ecosystem: https://github.com/pmndrs/react-three-fiber | likely browser/web | likely browser/web | likely browser/web | low/medium | Track separately from CAD action servers. |
| WebMCP-OpenSCAD | `webmcp_openscad` | `user_reported_url_needed` | MCP TBD; OpenSCAD WebAssembly note: https://openscad.org/downloads.html | browser/web likely | browser/web likely | browser/web likely | medium | Seed; verify source. |
| CREOSON Middleware | `creoson_creo_json_bridge` | `verified_api_wrapper_candidate`, non-MCP | https://github.com/SimplifiedLogic/creoson | host-dependent likely Windows | unknown/no practical desktop | unknown/no practical desktop | high | Strong wrapper candidate; not MCP until wrapped. |
| Jarvis OnShape MCP | `jarvis_onshape_mcp` | `user_reported_url_needed` | MCP TBD; Onshape API: https://onshape-public.github.io/docs/api-intro/ | likely if API-based | likely if API-based | unknown | medium | Seed only until source URL supplied. |

### 4.3 Hermes YAML catalog variants

| YAML entry | Reconciliation | Recommended registry treatment |
|---|---|---|
| Fusion 360 Python API Bridge | Host bridge candidate, not verified as public MCP in this pass. | `user_reported_url_needed`; verify repo/package and Fusion host requirements. |
| SolidWorks Document Manager | Strong wrapper candidate, but not verified as MCP. | `verified_api_wrapper_candidate` if API docs/license pinned; likely Windows/licensed/API-key dependent. |
| Zoo.dev Cloud CAD API | Verified official API and verified official MCP. | Alias of `zoo_cloud_cad_mcp`. |
| Web OpenSCAD | Host capability exists; MCP URL not verified. | Alias/variant of OpenSCAD seed entries. |
| React Three Fiber Web3D | Visualization/UI candidate; MCP URL not verified. | Track as UI/web integration, not CAD automation server. |
| Hermes YAML Catalog | Not a server. | Treat as registry input source. |

---

## 5. Verified Source Notes

### Zoo.dev Cloud CAD MCP

- Source: https://zoo.dev/docs/developer-tools/mcp
- Install pattern: `uvx zoo-mcp`
- Credential: `ZOO_API_TOKEN`
- Deployment: local MCP server using cloud CAD/API services
- Risk: medium; can create/modify cloud CAD data and files depending on exposed tools
- Platform: likely cross-platform wherever Python/uvx works; Linux ARM64 must be tested

Example Claude-style config:

```json
{
  "mcpServers": {
    "zoo": {
      "command": "uvx",
      "args": ["zoo-mcp"],
      "env": {
        "ZOO_API_TOKEN": "${ZOO_API_TOKEN}"
      }
    }
  }
}
```

Health check:

```bash
uvx zoo-mcp --help
# Then perform MCP initialize + tools/list through the Hermes MCP runner.
```

### BlenderMCP

- Source: https://github.com/ahujasid/blender-mcp
- Install pattern: `uvx blender-mcp`
- Requires Blender add-on and Blender desktop app
- Risk: high; Blender Python execution and scene/file modification
- Platform: README documents Windows/macOS/Linux; Linux ARM64 must be tested

Example config:

```json
{
  "mcpServers": {
    "blender": {
      "command": "uvx",
      "args": ["blender-mcp"]
    }
  }
}
```

Health check:

```bash
uvx blender-mcp --help
# Open Blender, enable add-on, then run MCP initialize + tools/list.
# Use read-only scene info as first test.
```

### FreeCAD MCP — neka-nat

- Source: https://github.com/neka-nat/freecad-mcp
- Install pattern: FreeCAD add-on + `uvx freecad-mcp`
- Capabilities include CAD object/document operations, Python execution, and FEM/CalculiX-related workflows
- Risk: high; arbitrary Python and CAD model writes
- Platform: Windows/macOS/Linux documented; Linux ARM64 must be tested

Example config:

```json
{
  "mcpServers": {
    "freecad": {
      "command": "uvx",
      "args": ["freecad-mcp"]
    }
  }
}
```

Health check:

```bash
uvx freecad-mcp --help
# Open FreeCAD, start/enable the bridge, then MCP initialize + tools/list.
# First tool call should be read-only document/session info.
```

### FreeCAD MCP / Copilot — contextform

- Source: https://github.com/contextform/freecad-mcp
- Install pattern: `npm install -g freecad-mcp-setup@latest`; `npx freecad-mcp-setup setup`
- Capabilities include PartDesign, booleans, transforms, view operations, and Python execution
- Risk: high; arbitrary Python and model writes
- Platform: cross-platform claimed; Linux ARM64 must be tested

Health check:

```bash
npx freecad-mcp-setup --help
# Then run setup, open FreeCAD, initialize MCP, list tools.
```

### KiCad MCP

- Source: https://github.com/lamaalrajih/kicad-mcp
- Install pattern: clone + `make install`; configure Python venv and `main.py`
- Requires KiCad 9.0+, Python 3.10+, uv
- Risk: medium; electronics project files, exports, DRC/BOM operations, possible project writes
- Platform: repo claims macOS/Windows/Linux; Linux ARM64 must be tested

Health check:

```bash
git clone https://github.com/lamaalrajih/kicad-mcp
cd kicad-mcp
make install
# Then run MCP initialize + tools/list.
```

### ROSBag MCP

- Source: https://github.com/binabik-ai/mcp-rosbags
- Install pattern: clone + Python virtualenv + requirements
- Use case: offline robotics log/bag analysis
- Risk: low/medium; reads local bag files, potentially large binary data
- Platform: likely best on Linux; Windows uncertain; Linux ARM64 depends on ROS/Python dependencies

Health check:

```bash
git clone https://github.com/binabik-ai/mcp-rosbags
cd mcp-rosbags
python -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
# Then run server entrypoint and MCP tools/list.
```

### Siemens Xcelerator Developer Portal MCP

- Source: https://developer.siemens.com/
- The Siemens Developer Portal homepage advertises a “Siemens Xcelerator Developer Portal MCP Server” for searching documentation, discovering products/APIs, and retrieving resources.
- Exact “Learn more” URL and client configuration should be pinned before automated install.
- Risk: read-only unless future server exposes write/API actions
- Platform: likely remote/docs-only and cross-platform

Health check:

```text
Open the Siemens MCP documentation page, capture remote endpoint/client config, then perform MCP initialize + tools/list.
```

### OpenSCAD host / OpenSCAD MCP seeds

- OpenSCAD downloads: https://openscad.org/downloads.html
- OpenSCAD docs: https://openscad.org/documentation.html
- OpenSCAD GitHub: https://github.com/openscad/openscad
- MCP URLs for OpenSCAD Geometry, OpenSCAD Linter, Web OpenSCAD, and WebMCP-OpenSCAD still need to be pinned.
- OpenSCAD itself is unusually attractive for Linux ARM64 because host distribution options include AppImage/Docker paths, but MCP package support is unknown until tested.

Host install examples:

```bash
# Windows
winget install OpenSCAD.OpenSCAD

# Debian/Ubuntu
sudo apt install openscad

# Docker or AppImage options: see https://openscad.org/downloads.html
```

Registry policy:

```text
Do not remove OpenSCAD MCP entries merely because source URL is TBD.
Mark them user_reported_url_needed and expose as blocked/pending verification.
```

### Autodesk Platform Services / APS

- Source: https://aps.autodesk.com/
- Status: verified engineering API platform, not verified MCP server in this pass
- Use case: model derivative/viewing, design automation, data management, ACC/BIM-related workflows depending API entitlement
- Platform: cloud/API; client can be cross-platform
- Risk: medium/high depending write/export/cloud permissions
- Action: custom wrapper candidate or verify community APS MCP source if supplied

### CREOSON / PTC Creo

- Source: https://github.com/SimplifiedLogic/creoson
- Status: verified JSON bridge/middleware for Creo Parametric, not verified MCP server
- Use case: automate Creo via JSON calls; strong candidate for a Hermes/OpenClaw MCP wrapper
- Platform: host-dependent; likely Windows-centric in practical Creo deployments
- Risk: high; can modify CAD models and automate host app

### Onshape API / Jarvis OnShape MCP seed

- API source: https://onshape-public.github.io/docs/api-intro/
- Jarvis OnShape MCP URL: TBD
- Status: API verified, MCP not verified
- Platform: cloud/API; likely cross-platform if MCP exists
- Risk: medium/high depending document write access

### PTC ThingWorx

- Source: https://www.ptc.com/en/products/thingworx
- Status: industrial IoT platform/API candidate, not verified MCP server here
- Risk: high/safety-critical if connected to live assets or control loops
- Platform: tenant/cloud/enterprise dependent

### MCP-UI

- Source: https://github.com/idosal/mcp-ui
- Status: UI SDK/infrastructure, not engineering MCP server
- Use case: render interactive UI resources in Hermes/OpenClaw for server preview, approval, logs, inspectors, CAD thumbnails, etc.

### WebMCP Standard

- Source: https://arxiv.org/abs/2508.09171
- Status: web-agent standard/research concept, not conventional engineering MCP server
- Use case: possible future browser/web CAD integration strategy

---

## 6. Machine-readable Seed Manifest

This JSON block is intentionally conservative. Entries with unknown URLs are kept because they appeared in prior research/user catalog, but automated install must be blocked until `source_url` and `install_methods` are verified.

```json
{
  "generated_at": "2026-06-26",
  "schema_version": "engineering-mcp-registry-seed-v0.2",
  "platform_keys": [
    "windows_11_x64",
    "linux_x64",
    "linux_arm64",
    "macos_x64",
    "macos_arm64"
  ],
  "servers": [
    {
      "server_id": "zoo_cloud_cad_mcp",
      "display_name": "Zoo.dev Cloud CAD MCP",
      "aliases": ["Zoo.dev Cloud CAD", "Zoo.dev Cloud CAD API"],
      "verification_state": "verified_mcp",
      "source_url": "https://zoo.dev/docs/developer-tools/mcp",
      "install_methods": [
        { "type": "uvx", "command": "uvx", "args": ["zoo-mcp"] }
      ],
      "credentials_required": ["ZOO_API_TOKEN"],
      "deployment_mode": "cloud-saas",
      "transport": ["stdio", "unknown_exact"],
      "domains": ["cloud CAD", "geometry", "file conversion", "CAD API"],
      "risk_level": "medium",
      "platform_support": {
        "windows_11_x64": { "status": "likely", "tested": false, "notes": "uvx/Python expected; verify locally" },
        "linux_x64": { "status": "likely", "tested": false, "notes": "uvx/Python expected; verify locally" },
        "linux_arm64": { "status": "unknown", "tested": false, "notes": "must test Python package/dependencies on ARM64" },
        "macos_x64": { "status": "likely", "tested": false, "notes": "uvx/Python expected" },
        "macos_arm64": { "status": "likely", "tested": false, "notes": "uvx/Python expected" }
      },
      "include_in_plugin": "yes",
      "integration_priority": "P0",
      "default_enabled": false,
      "health_check": "uvx zoo-mcp --help; MCP initialize; tools/list"
    },
    {
      "server_id": "blender_mcp_ahujasid",
      "display_name": "BlenderMCP",
      "aliases": ["Blender 3D"],
      "verification_state": "community_mcp",
      "source_url": "https://github.com/ahujasid/blender-mcp",
      "install_methods": [
        { "type": "uvx", "command": "uvx", "args": ["blender-mcp"] },
        { "type": "host_app_addon", "host": "Blender" }
      ],
      "host_software_required": ["Blender >= 3.0", "Python >= 3.10", "uv"],
      "deployment_mode": "local-bridge",
      "domains": ["3D modeling", "visualization", "geometry scripting"],
      "risk_level": "high",
      "security_notes": ["Can execute Python inside Blender", "Can modify scenes/files", "Can fetch assets depending tool use"],
      "platform_support": {
        "windows_11_x64": { "status": "yes", "tested": false, "notes": "repo documents Windows" },
        "linux_x64": { "status": "yes", "tested": false, "notes": "repo documents Linux" },
        "linux_arm64": { "status": "unknown", "tested": false, "notes": "test Blender + uv dependencies on ARM64" },
        "macos_x64": { "status": "yes", "tested": false, "notes": "repo documents macOS" },
        "macos_arm64": { "status": "likely", "tested": false, "notes": "macOS supported; arch-specific test needed" }
      },
      "include_in_plugin": "yes",
      "integration_priority": "P0",
      "default_enabled": false,
      "health_check": "uvx blender-mcp --help; open Blender; enable add-on; MCP initialize; tools/list"
    },
    {
      "server_id": "freecad_mcp_neka_nat",
      "display_name": "FreeCAD Engineering MCP",
      "aliases": ["FreeCAD Engineering", "FreeCAD Core", "CalculiX Simulation"],
      "verification_state": "community_mcp",
      "source_url": "https://github.com/neka-nat/freecad-mcp",
      "install_methods": [
        { "type": "uvx", "command": "uvx", "args": ["freecad-mcp"] },
        { "type": "host_app_addon", "host": "FreeCAD" }
      ],
      "host_software_required": ["FreeCAD", "Python", "uv"],
      "deployment_mode": "local-bridge",
      "domains": ["CAD", "geometry", "FEM", "CalculiX"],
      "risk_level": "high",
      "security_notes": ["Can execute arbitrary Python in FreeCAD", "Can modify CAD documents"],
      "platform_support": {
        "windows_11_x64": { "status": "yes", "tested": false, "notes": "repo documents Windows" },
        "linux_x64": { "status": "yes", "tested": false, "notes": "repo documents Linux" },
        "linux_arm64": { "status": "unknown", "tested": false, "notes": "test FreeCAD + dependencies on ARM64" },
        "macos_x64": { "status": "yes", "tested": false, "notes": "repo documents macOS" },
        "macos_arm64": { "status": "likely", "tested": false, "notes": "test FreeCAD + dependencies" }
      },
      "include_in_plugin": "yes",
      "integration_priority": "P1",
      "default_enabled": false,
      "health_check": "uvx freecad-mcp --help; open FreeCAD bridge; MCP initialize; tools/list"
    },
    {
      "server_id": "freecad_mcp_contextform",
      "display_name": "FreeCAD MCP / Copilot",
      "aliases": ["FreeCAD Copilot", "FreeCAD Booleans", "FreeCAD Robust"],
      "verification_state": "community_mcp",
      "source_url": "https://github.com/contextform/freecad-mcp",
      "install_methods": [
        { "type": "npm", "command": "npm", "args": ["install", "-g", "freecad-mcp-setup@latest"] },
        { "type": "npx", "command": "npx", "args": ["freecad-mcp-setup", "setup"] }
      ],
      "host_software_required": ["FreeCAD", "Node.js", "Python"],
      "deployment_mode": "local-bridge",
      "domains": ["CAD", "booleans", "part design", "geometry scripting"],
      "risk_level": "high",
      "security_notes": ["Can execute Python in FreeCAD", "Can modify CAD documents"],
      "platform_support": {
        "windows_11_x64": { "status": "yes", "tested": false, "notes": "repo claims cross-platform" },
        "linux_x64": { "status": "yes", "tested": false, "notes": "repo claims cross-platform" },
        "linux_arm64": { "status": "unknown", "tested": false, "notes": "test Node/Python/FreeCAD on ARM64" },
        "macos_x64": { "status": "yes", "tested": false, "notes": "repo claims cross-platform" },
        "macos_arm64": { "status": "likely", "tested": false, "notes": "test host stack" }
      },
      "include_in_plugin": "yes",
      "integration_priority": "P1",
      "default_enabled": false,
      "health_check": "npx freecad-mcp-setup --help; setup; MCP initialize; tools/list"
    },
    {
      "server_id": "openscad_geometry_mcp",
      "display_name": "OpenSCAD Geometry MCP",
      "aliases": ["OpenSCAD Geometry", "Web OpenSCAD"],
      "verification_state": "user_reported_url_needed",
      "source_url": null,
      "host_reference_urls": ["https://openscad.org/downloads.html", "https://github.com/openscad/openscad"],
      "install_methods": [],
      "host_software_required": ["OpenSCAD"],
      "deployment_mode": "unknown",
      "domains": ["script CAD", "CSG", "3D printing", "geometry generation"],
      "risk_level": "medium",
      "platform_support": {
        "windows_11_x64": { "status": "unknown", "tested": false, "notes": "OpenSCAD host works; MCP package unknown" },
        "linux_x64": { "status": "unknown", "tested": false, "notes": "OpenSCAD host works; MCP package unknown" },
        "linux_arm64": { "status": "unknown", "tested": false, "notes": "OpenSCAD host likely; MCP package unknown" },
        "macos_x64": { "status": "unknown", "tested": false, "notes": "OpenSCAD host works; MCP package unknown" },
        "macos_arm64": { "status": "unknown", "tested": false, "notes": "OpenSCAD host likely; MCP package unknown" }
      },
      "include_in_plugin": "maybe",
      "integration_priority": "P0",
      "default_enabled": false,
      "health_check": "blocked until source_url/install command verified"
    },
    {
      "server_id": "openscad_linter_mcp",
      "display_name": "OpenSCAD Linter MCP",
      "aliases": ["OpenSCAD Linter"],
      "verification_state": "user_reported_url_needed",
      "source_url": null,
      "host_reference_urls": ["https://openscad.org/documentation.html"],
      "install_methods": [],
      "deployment_mode": "unknown",
      "domains": ["script CAD", "linting", "documentation"],
      "risk_level": "low",
      "platform_support": {
        "windows_11_x64": { "status": "unknown", "tested": false, "notes": "MCP package unknown" },
        "linux_x64": { "status": "unknown", "tested": false, "notes": "MCP package unknown" },
        "linux_arm64": { "status": "unknown", "tested": false, "notes": "MCP package unknown" },
        "macos_x64": { "status": "unknown", "tested": false, "notes": "MCP package unknown" },
        "macos_arm64": { "status": "unknown", "tested": false, "notes": "MCP package unknown" }
      },
      "include_in_plugin": "maybe",
      "integration_priority": "P0",
      "default_enabled": false,
      "health_check": "blocked until source_url/install command verified"
    },
    {
      "server_id": "autodesk_product_help_mcp",
      "display_name": "Autodesk Product Help MCP",
      "aliases": ["Autodesk Help MCP", "Autodesk Product Help"],
      "verification_state": "user_reported_url_needed",
      "source_url": null,
      "host_reference_urls": ["https://help.autodesk.com/"],
      "install_methods": [],
      "deployment_mode": "docs-only",
      "domains": ["documentation", "CAD help", "Autodesk docs"],
      "risk_level": "read-only",
      "platform_support": {
        "windows_11_x64": { "status": "likely", "tested": false, "notes": "docs/remote MCP expected if URL verified" },
        "linux_x64": { "status": "likely", "tested": false, "notes": "docs/remote MCP expected if URL verified" },
        "linux_arm64": { "status": "likely", "tested": false, "notes": "docs/remote MCP expected if URL verified" },
        "macos_x64": { "status": "likely", "tested": false, "notes": "docs/remote MCP expected if URL verified" },
        "macos_arm64": { "status": "likely", "tested": false, "notes": "docs/remote MCP expected if URL verified" }
      },
      "include_in_plugin": "maybe",
      "integration_priority": "P0",
      "default_enabled": true,
      "health_check": "blocked until official MCP endpoint/client config verified"
    }
  ],
  "registry_policy": {
    "do_not_auto_install_states": ["user_reported_url_needed", "verified_api_wrapper_candidate", "ui_or_web_standard", "watchlist"],
    "default_disabled_risk_levels": ["medium", "high", "safety-critical"],
    "require_approval_for": ["file writes", "CAD model mutation", "arbitrary code execution", "cloud upload", "machine control", "printer/robot/PLC/CNC actions"]
  }
}
```

---

## 7. Plugin Architecture Guidance

### 7.1 Components

```text
Hermes/OpenClaw MCP Plugin Manager
├── Registry Loader
│   ├── built-in seed catalog
│   ├── user-provided YAML catalog
│   ├── official MCP registry importer
│   ├── GitHub/npm/PyPI/Docker discovery probes
│   └── vendor docs / llms.txt / docs-MCP discovery
├── Verifier
│   ├── source URL resolver
│   ├── package metadata extractor
│   ├── license detector
│   ├── platform/architecture probe
│   ├── install dry-run probe
│   └── MCP protocol smoke tester
├── Installer
│   ├── uv/uvx isolated install backend
│   ├── npm/npx isolated install backend
│   ├── Docker backend
│   ├── host-app add-on backend
│   └── remote MCP connector backend
├── Runtime Supervisor
│   ├── stdio process manager
│   ├── streamable HTTP/SSE connector
│   ├── log capture/redaction
│   ├── restart/backoff
│   └── port/security policy
├── Safety Gateway
│   ├── read-only mode enforcement
│   ├── workspace sandboxing
│   ├── approval prompts
│   ├── machine-control interlocks
│   └── secret redaction
└── UI Layer
    ├── server list
    ├── platform compatibility matrix
    ├── install/config wizard
    ├── logs
    ├── tool discovery view
    ├── enable/disable toggles
    └── approval queue
```

### 7.2 Registry schema additions

Minimum recommended schema:

```json
{
  "server_id": "",
  "display_name": "",
  "aliases": [],
  "verification_state": "verified_mcp | verified_docs_mcp | community_mcp | user_reported_url_needed | verified_api_wrapper_candidate | capability_alias | ui_or_web_standard | watchlist | excluded",
  "source_url": "",
  "install_url": "",
  "domains": [],
  "lifecycle_stage": [],
  "description": "",
  "capabilities": [],
  "deployment_mode": "local-only | local-bridge | local-plus-network | cloud-saas | remote-mcp | docs-only | unknown",
  "transport": ["stdio | sse | streamable-http | websocket | rest-bridge | custom-rpc | unknown"],
  "platform_support": {
    "windows_11_x64": { "status": "", "tested": false, "notes": "" },
    "linux_x64": { "status": "", "tested": false, "notes": "" },
    "linux_arm64": { "status": "", "tested": false, "notes": "" },
    "macos_x64": { "status": "", "tested": false, "notes": "" },
    "macos_arm64": { "status": "", "tested": false, "notes": "" }
  },
  "host_software_required": [],
  "requires_gui": false,
  "headless_ok": "yes | likely | unknown | no",
  "credentials_required": [],
  "license_requirements": [],
  "install_methods": [],
  "example_mcp_config": {},
  "health_check": "",
  "data_touched": [],
  "risk_level": "read-only | low | medium | high | safety-critical",
  "security_notes": [],
  "default_enabled": false,
  "approval_gates": [],
  "maturity": "official production | official preview | vendor demo/prototype | community active | community experimental | stale/exclude | unknown",
  "maintenance_evidence": {
    "last_commit": "",
    "latest_release": "",
    "package_version": "",
    "issue_activity": "",
    "evidence_urls": []
  },
  "software_license": "",
  "include_in_plugin": "yes | maybe | no",
  "integration_priority": "P0 | P1 | P2 | P3",
  "score": 0,
  "rationale": ""
}
```

### 7.3 Install strategy

Use isolated installs by default.

Python/uv servers:

```text
~/.hermes/mcp/<server_id>/venv
uvx --from <package> <command>
# or uv tool install with pinned version once verified
```

Node servers:

```text
~/.hermes/mcp/<server_id>/node_modules
npm install <package>@<pinned_version>
npx <package> --help
```

Docker servers:

```text
image digest pinned
architecture manifest checked before pull
network disabled unless required
workspace mounted read-only by default
```

Host-app bridges:

```text
1. Detect host app path and version.
2. Install MCP package in isolated environment.
3. Install host-app add-on/extension separately.
4. Require the user to open the host app.
5. Perform local bridge handshake.
6. Run read-only health check.
```

Remote/docs MCPs:

```text
1. Store endpoint URL.
2. Validate transport and auth.
3. Run MCP initialize and tools/list.
4. Mark all tools read-only unless write tools are explicitly documented.
```

### 7.4 Launch strategy

Stdio MCP:

```text
spawn process
capture stdout/stderr separately
redact secrets in logs
send MCP initialize
call tools/list
cache tool schema with source/version hash
```

HTTP/SSE/streamable HTTP MCP:

```text
bind localhost only for local servers
use random high port unless server requires fixed port
reject 0.0.0.0 binding by default
validate Origin where applicable
perform MCP initialize
```

Host bridge:

```text
start MCP server
ensure host app is running
verify add-on loaded
call read-only session info
block write tools until approval
```

Machine-control bridge:

```text
simulation mode required by default
read-only status allowed after endpoint allowlist
write/motion/heat/print/spindle/deploy tools hidden until approval
hardware interlock confirmation required
```

### 7.5 Secret handling

Rules:

```text
- Never store secrets in plain JSON/YAML.
- Use OS keychain/credential manager where possible.
- Support environment variable indirection: ${ZOO_API_TOKEN}, ${AUTODESK_CLIENT_SECRET}, etc.
- Redact secrets from logs, crash reports, telemetry, and tool traces.
- Record which tools require credentials before exposing them to the model.
- Separate read-only tokens from write-capable tokens where vendor supports scopes.
```

### 7.6 Safety policy

Default allowlist:

```text
- docs-only MCPs
- read-only local file analyzers
- ROSBag offline analysis
- KiCad read-only project inspection
- OpenSCAD lint/read/export only after workspace approval
```

Default disabled:

```text
- BlenderMCP Python execution
- FreeCAD Python execution
- CAD model mutation tools
- cloud upload/export tools
- PLM/PDM write tools
- slicer/printer action tools
- robot/PLC/CNC/industrial protocol tools
- any server that can move axes, heat tools, start spindles, start prints, deploy code, or write to production systems
```

Approval gates:

| Gate | Required for |
|---|---|
| `workspace_write_approval` | Creating/modifying CAD, mesh, PCB, CAM, or config files. |
| `execute_code_approval` | Python, JS, scripts, macros, host-app command execution. |
| `cloud_upload_approval` | Sending files/designs to SaaS APIs. |
| `machine_control_approval` | Printer, CNC, robot, PLC, actuator, heater, spindle, feeder, conveyor actions. |
| `enterprise_write_approval` | PLM/PDM/requirements/MBSE item creation or modification. |
| `secrets_approval` | Supplying API keys, OAuth tokens, vendor credentials. |

---

## 8. Automated Tests

### 8.1 Universal server tests

```text
test_registry_entry_has_stable_id()
test_source_url_resolves_or_state_is_url_needed()
test_platform_constraints_match_current_host()
test_install_dry_run_or_blocked_state()
test_process_starts_or_remote_endpoint_connects()
test_mcp_initialize()
test_tools_list()
test_tool_schema_cached_with_version()
test_logs_redact_secrets()
test_default_disabled_for_high_risk_servers()
```

### 8.2 CAD/file generator tests

```text
create temporary workspace
launch server with workspace-only access
run read-only info/list command
run approved sample generation if low risk
verify outputs remain inside workspace
verify no writes outside workspace
verify cleanup works
```

### 8.3 Host-app bridge tests

```text
detect host app path
detect host app version
verify add-on/plugin installed
verify local bridge handshake
run read-only session/document info
block write/model mutation tools before approval
```

### 8.4 Platform tests

```text
windows_11_x64:
  verify command path, host app detection, process launch, MCP initialize

linux_x64:
  verify package install, shared libraries, GUI/headless constraints, MCP initialize

linux_arm64:
  verify CPU architecture compatibility, Python wheels, Node native modules, Docker manifests, host-app availability

macos_x64 / macos_arm64:
  verify codesigning/quarantine issues, host app paths, Python/Node package support
```

### 8.5 Machine-control tests

```text
simulation mode must be true by default
read-only status command only before approval
network endpoint must be allowlisted
write/motion/heat/print/deploy tools hidden before approval
approval event must include exact command, target, parameters, and rollback/stop guidance
```

---

## 9. Discovery Pipeline

The registry builder should not depend on one search source.

```text
1. Load human seed catalog.
2. Load Hermes YAML catalog.
3. Query official MCP registry.
4. Search GitHub by exact terms and domain terms.
5. Search npm/PyPI for package names.
6. Search Docker Hub/container manifests for server images.
7. Search vendor docs, marketplaces, AI registry pages, llms.txt, and docs MCP pages.
8. Normalize aliases.
9. Deduplicate by source URL/package/command.
10. Assign verification state.
11. Probe platform support.
12. Run MCP smoke tests for verified entries.
13. Generate registry JSON and UI catalog.
```

Search terms to preserve:

```text
mcp server CAD
mcp server FreeCAD
mcp server Fusion
mcp server Autodesk
mcp server Siemens Teamcenter
mcp server NX
mcp server SolidWorks
mcp server CATIA
mcp server Creo Windchill
mcp server Blender
mcp server KiCad
mcp server 3D printer
mcp server Gmsh
mcp server OpenFOAM
mcp server FEA
mcp server CFD
mcp server BIM IFC
mcp server ROS
mcp server PLC
mcp snap7
mcp OPC UA
OpenSCAD MCP
OpenSCAD Geometry MCP
OpenSCAD Linter MCP
WebMCP OpenSCAD
AutoCAD MCP
Easy-MCP-AutoCAD
Jarvis OnShape MCP
SolidWorks MCP Python
SolidWorks MCP TypeScript
CREOSON MCP
```

---

## 10. Immediate Coding-Agent Tasks

1. Add `verification_state` and architecture-specific `platform_support` to the Hermes registry schema.
2. Import the current Hermes YAML catalog as `user_reported_url_needed` unless source/install evidence already exists.
3. Add verified entries for Zoo.dev, BlenderMCP, FreeCAD MCP variants, KiCad MCP, ROSBag MCP, and Siemens Developer Portal MCP/docs entry.
4. Add blocked seed entries for OpenSCAD Geometry, OpenSCAD Linter, Autodesk Product Help MCP, WebMCP-OpenSCAD, Jarvis OnShape MCP, AutoCAD/Fusion/SolidWorks/Rhino/SketchUp variants.
5. Add wrapper-candidate entries for Autodesk APS, Onshape API, CREOSON, PTC ThingWorx, SolidWorks APIs, and industrial protocol adapters.
6. Implement installer backends for `uvx`, `npm/npx`, `Docker`, `host_app_addon`, and `remote_mcp`.
7. Implement platform probe for Windows 11 x64, Linux x64, Linux ARM64, macOS x64, macOS ARM64.
8. Implement safety gates and default-disabled policy for high-risk and safety-critical servers.
9. Build a UI table that shows: installable, blocked URL-needed, platform support, required host software, credentials, risk, and health-check status.
10. Add a “report missing MCP” workflow so user-reported servers become seed entries instead of disappearing.

---

## 11. Product Recommendation

Treat the engineering MCP ecosystem as a living registry with evidence levels, not a static list. The key design principle is:

> A server can be valuable enough to track even before it is safe or verified enough to install.

For Hermes/OpenClaw, this means OpenSCAD MCP, Autodesk Product Help MCP, and prior-catalog variants should stay visible as blocked/pending entries until primary URLs are pinned. Conversely, strong APIs such as CREOSON, Onshape, Autodesk APS, and ThingWorx should be visible as wrapper candidates, not mislabeled as installable MCP servers.

The default user experience should be:

```text
Show me what exists.
Show me what is installable on my current machine.
Show me what is blocked and why.
Show me what is dangerous before I enable it.
Never hide uncertainty.
```
