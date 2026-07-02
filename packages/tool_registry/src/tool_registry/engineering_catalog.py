from __future__ import annotations

import json

from .catalog_loader import (
    catalog_entry_to_mcp_seed,
    normalize_mcp_seed_entry,
)
from .mcp_catalog import (
    platform_support,
    tier_sort_key,
    validation_summary,
)

# -----------------------------------------------------------------------------
# Engineering MCP Catalog  (sourced from docs/Engineering MCP Tools Discovery.md)
# -----------------------------------------------------------------------------
# Each entry uses a stable deterministic server_id so INSERT OR IGNORE is idempotent.
# Fields: (server_id, name, type, command, is_active, is_installed, status,
#          category, image_url, description, source_url, installed_version)

ENGINEERING_CATALOG = [
    # CAD - Open Source / Linux-Installable
    {
        "server_id": "openscad-mcp-server",
        "name": "OpenSCAD Geometry",
        "type": "stdio",
        "command": json.dumps(
            [
                "uv",
                "run",
                "--with",
                "git+https://github.com/quellant/openscad-mcp.git",
                "openscad-mcp",
            ]
        ),
        "category": "cad",
        "image_url": "https://avatars.githubusercontent.com/u/37583508?s=64",
        "description": "Renders and validates OpenSCAD models. Generates high-fidelity PNG previews and animations from .scad scripts, closing the AI design loop without a GUI.",
        "source_url": "https://github.com/quellant/openscad-mcp",
        "instructions": (
            "1. Deliverables & Final Assets: When creating, modifying, or exporting final files requested by the user "
            "(such as .scad OpenSCAD source files, .stl/.3mf 3D print exports, or final .png/.jpg rendering images), "
            "always place them directly in the main workspace root directory (which is the current working directory, e.g. './'), "
            "or inside user-visible folders there (e.g. './models/', './exports/', or './renders/').\n"
            "   - For OpenSCAD model tools (create_model, update_model etc.), specify the workspace parameter pointing "
            "to the workspace root directory (the current working directory '.' or the absolute path).\n"
            "   - For OpenSCAD export tools (export_model), specify the output_path parameter pointing to the workspace "
            "root or a subfolder (e.g. './cube.stl') so they do not default to temporary directories.\n"
            "   - For any image render output files, write/save them directly to a user-accessible path in the workspace root or './renders/' instead of storing them in the tmp/ directory.\n"
            "2. Intermediate & Working Files: Only use the tmp/ folder (which maps to the workspace's local tmp/ folder) "
            "for transient internal renders, scratch files, build outputs, cache files, and logs. Do NOT put final files, exports, or requested images in tmp/."
        ),
    },
    {
        "server_id": "openscad-linter-trikos529",
        "name": "OpenSCAD Linter",
        "type": "stdio",
        "command": json.dumps(["uvx", "openscad-linter-mcp"]),
        "category": "cad",
        "image_url": "https://avatars.githubusercontent.com/u/37583508?s=64",
        "description": "Validates and lints AI-generated OpenSCAD code against best practices, forcing parametric variables over hard-coded dimensions.",
        "source_url": "https://github.com/topics/cad-3d",
    },
    {
        "server_id": "freecad-engineering-sandraschi",
        "name": "FreeCAD Engineering",
        "type": "stdio",
        "command": json.dumps(
            [
                "uv",
                "run",
                "--with",
                "git+https://github.com/sandraschi/freecad-mcp.git",
                "python",
                "-m",
                "freecad_mcp.server",
                "--mode",
                "stdio",
            ]
        ),
        "category": "cad",
        "image_url": "https://avatars.githubusercontent.com/u/1413352?s=64",
        "description": "End-to-end engineering pipeline: FreeCAD geometric kernel connected to OpenFOAM CFD, CalculiX FEA, and PrusaSlicer for automated 3D-print G-code generation.",
        "source_url": "https://github.com/sandraschi/freecad-mcp",
        "env_vars": json.dumps(
            [
                {
                    "name": "FREECAD_PATH",
                    "label": "FreeCADCmd path",
                    "description": "Path to the selected FreeCAD headless executable, for example an extracted AppImage `usr/bin/freecadcmd`.",
                    "required": True,
                    "secret": False,
                }
            ]
        ),
        "instructions": (
            "1. Output Delivery: The FreeCAD MCP server automatically runs inside the workspace and saves all "
            "created geometric primitives, converted mesh STL files, and slice G-code to its local outputs directory: "
            "`./freecad_mcp_work/output/`.\n"
            "2. User Visibility / Moving Files: Because this outputs directory is not displayed in the files explorer, "
            "files saved there are NOT immediately visible in the user's files list or layout view. Whenever you invoke "
            "a shape creation/conversion tool (such as create_shape, step_to_stl, or slice_stl), you MUST immediately "
            "copy or move the resulting file from the outputs folder (e.g. `./freecad_mcp_work/output/{output_name}`) "
            "directly into the main workspace root directory (e.g. `./{output_name}`) using standard file-system operations "
            "or terminal commands. This ensures the file is exposed to the user-facing files explorer tree and 3D preview tabs."
        ),
    },
    {
        "server_id": "freecad-copilot-contextform",
        "name": "FreeCAD Copilot",
        "type": "stdio",
        "command": json.dumps(["python3", "~/.freecad-mcp/working_bridge.py"]),
        "category": "cad",
        "image_url": "https://avatars.githubusercontent.com/u/1413352?s=64",
        "description": "AI copilot workbench embedded in FreeCAD. 13 PartDesign + 18 Part operations, cross-platform automated installation, and screenshot verification.",
        "source_url": "https://github.com/contextform/freecad-mcp",
    },
    {
        "server_id": "freecad-robust-spkane",
        "name": "FreeCAD Robust",
        "type": "stdio",
        "command": json.dumps(
            ["uv", "tool", "run", "--from", "freecad-robust-mcp", "freecad-mcp"]
        ),
        "category": "cad",
        "image_url": "https://avatars.githubusercontent.com/u/1413352?s=64",
        "description": "Broad FreeCAD control for object management, arbitrary Python execution, macro development, and headless CI workflows. Supports XML-RPC, JSON-RPC socket, and embedded Linux modes.",
        "source_url": "https://github.com/spkane/freecad-addon-robust-mcp-server",
    },
    {
        "server_id": "freecad-core-nekanat",
        "name": "FreeCAD Core",
        "type": "stdio",
        "command": json.dumps(["uvx", "freecad-mcp", "--only-text-feedback"]),
        "category": "cad",
        "image_url": "https://avatars.githubusercontent.com/u/1413352?s=64",
        "description": "Lightweight FreeCAD MCP integration focused on core parametric modeling operations via the native Python API.",
        "source_url": "https://github.com/neka-nat/freecad-mcp",
    },
    {
        "server_id": "freecad-booleans-lucygoodchild",
        "name": "FreeCAD Booleans",
        "type": "stdio",
        "command": json.dumps(["node", "build/index.js"]),
        "category": "cad",
        "image_url": "https://avatars.githubusercontent.com/u/1413352?s=64",
        "description": "FreeCAD server specializing in primitive generation and complex Boolean logic operations for solid modeling.",
        "source_url": "https://github.com/lucygoodchild/freecad-mcp-server",
    },
    {
        "server_id": "caid-opencascade-dreliq9",
        "name": "CAiD OpenCASCADE",
        "type": "stdio",
        "command": json.dumps(["python", "server.py"]),
        "category": "cad",
        "image_url": "https://avatars.githubusercontent.com/u/159555580?s=64",
        "description": "Direct OpenCASCADE (OCCT) kernel interface via CAiD. Strict ForgeResult validation layer tracks volume, surface area, and manifold diagnostics.",
        "source_url": "https://github.com/dreliq9/caid-mcp",
    },
    #  CAD  Cloud / Network Services
    {
        "server_id": "zoo-dev-cloud-cad",
        "name": "Zoo.dev Cloud CAD",
        "type": "stdio",
        "command": json.dumps(["uvx", "zoo-mcp"]),
        "category": "cad",
        "image_url": "https://avatars.githubusercontent.com/u/80992670?s=64",
        "description": "Cloud CAD engine by Zoo.dev (formerly KittyCAD). Offloads heavy geometric computation to scalable cloud infrastructure with per-second billing.",
        "source_url": "https://github.com/KittyCAD/zoo-mcp",
        "env_vars": json.dumps(
            [
                {
                    "name": "ZOO_API_TOKEN",
                    "label": "Zoo API token",
                    "description": "Zoo.dev API token required for cloud CAD compute and conversion tools.",
                    "required": True,
                    "secret": True,
                },
            ]
        ),
    },
    {
        "server_id": "onshape-mcp-hedless",
        "name": "Onshape MCP",
        "type": "stdio",
        "command": json.dumps(["python", "-m", "onshape_mcp.server"]),
        "category": "cad",
        "image_url": "https://avatars.githubusercontent.com/u/6536550?s=64",
        "description": "Cloud-native Onshape REST API access. Navigate workspaces, manage Part Studios, create parametric sketches, and read/write variable tables.",
        "source_url": "https://github.com/hedless/onshape-mcp",
        "env_vars": json.dumps(
            [
                {
                    "name": "ONSHAPE_ACCESS_KEY",
                    "label": "Onshape access key",
                    "description": "Access key from the Onshape Developer Portal.",
                    "required": True,
                    "secret": False,
                },
                {
                    "name": "ONSHAPE_SECRET_KEY",
                    "label": "Onshape secret key",
                    "description": "Secret key from the Onshape Developer Portal.",
                    "required": True,
                    "secret": True,
                },
            ]
        ),
    },
    #  Simulation / FEA
    {
        "server_id": "oasis-open-fem-agent",
        "name": "OASiS Open FEM Agent",
        "type": "stdio",
        "command": json.dumps(["python", "-m", "server"]),
        "category": "simulation",
        "image_url": "https://avatars.githubusercontent.com/u/139527664?s=64",
        "description": "Open-source finite element MCP server connecting AI agents to multiple FEM solver backends including scikit-fem, FEniCSx, NGSolve, deal.II, Kratos, DUNE-fem, 4C, and FEBio.",
        "source_url": "https://github.com/Hereon-InstituteMS/OASiS",
        "env_vars": json.dumps(
            [
                {
                    "name": "PYVISTA_OFF_SCREEN",
                    "label": "PyVista off-screen mode",
                    "description": "Set to `true` for headless Linux/container validation and rendering.",
                    "required": False,
                    "secret": False,
                },
                {
                    "name": "FENICS_PYTHON",
                    "label": "FEniCSx Python path",
                    "description": "Optional Python executable for a FEniCSx/dolfinx environment when that backend is selected.",
                    "required": False,
                    "secret": False,
                },
                {
                    "name": "FEBIO_BINARY",
                    "label": "FEBio binary path",
                    "description": "Optional FEBio executable path when that backend is selected.",
                    "required": False,
                    "secret": False,
                },
            ]
        ),
        "instructions": (
            "Clone `https://github.com/Hereon-InstituteMS/OASiS`, create a virtual environment, run `pip install -e .`, "
            "then install only the selected solver backend. The Linux x64 validation used `pip install scikit-fem` and "
            "`PYVISTA_OFF_SCREEN=true` before launching `python -m server`. Other backends such as FEniCSx, NGSolve, "
            "deal.II, Kratos, DUNE-fem, 4C, and FEBio are optional and should be installed only when the user selects "
            "that backend."
        ),
    },
    {
        "server_id": "calculix-simulation",
        "name": "CalculiX Simulation",
        "type": "stdio",
        "command": json.dumps(["uv", "run", "calculix-mcp"]),
        "category": "simulation",
        "image_url": "https://avatars.githubusercontent.com/u/38575799?s=64",
        "description": "Open-source finite element analysis (FEA) solver. Performs structural stress, strain, and thermal analysis on 3D meshes via the CalculiX MCP bridge.",
        "source_url": "https://github.com/calculix/calculix-mcp",
    },
    #  PLM / Enterprise Cloud APIs
    {
        "server_id": "autodesk-aps-official",
        "name": "Autodesk Platform Services",
        "type": "stdio",
        "command": json.dumps(["node", "server.js"]),
        "category": "plm",
        "image_url": "https://avatars.githubusercontent.com/u/1478570?s=64",
        "description": "Official Autodesk APS integration. Secure data management, model derivatives, webhooks, and AEC data modeling with SSA-based authentication.",
        "source_url": "https://github.com/autodesk-platform-services/aps-mcp-server-nodejs",
        "env_vars": json.dumps(
            [
                {
                    "name": "APS_CLIENT_ID",
                    "label": "APS client ID",
                    "description": "Autodesk Platform Services application client ID.",
                    "required": True,
                    "secret": False,
                },
                {
                    "name": "APS_CLIENT_SECRET",
                    "label": "APS client secret",
                    "description": "Autodesk Platform Services application client secret.",
                    "required": True,
                    "secret": True,
                },
                {
                    "name": "SSA_ID",
                    "label": "Secure service account ID",
                    "description": "Autodesk Secure Service Account ID.",
                    "required": True,
                    "secret": False,
                },
                {
                    "name": "SSA_KEY_ID",
                    "label": "SSA key ID",
                    "description": "Autodesk Secure Service Account private key ID.",
                    "required": True,
                    "secret": False,
                },
                {
                    "name": "SSA_KEY_PATH",
                    "label": "SSA private key path",
                    "description": "Path to the downloaded Secure Service Account PEM private key.",
                    "required": True,
                    "secret": False,
                },
            ]
        ),
    },
    {
        "server_id": "autodesk-aps-petrbroz",
        "name": "Autodesk APS (Community)",
        "type": "stdio",
        "command": json.dumps(["node", "build/server.js"]),
        "category": "plm",
        "image_url": "https://avatars.githubusercontent.com/u/1478570?s=64",
        "description": "Superseded community Autodesk Platform Services MCP server for Autodesk Construction Cloud data. The upstream README now redirects users to the official Autodesk APS MCP server.",
        "source_url": "https://github.com/petrbroz/aps-mcp-server",
    },
    {
        "server_id": "siemens-element-mcp",
        "name": "Siemens Element Design System",
        "type": "stdio",
        "command": json.dumps(["npx", "@siemens/element-mcp"]),
        "category": "plm",
        "image_url": "https://avatars.githubusercontent.com/u/4006395?s=64",
        "description": "Siemens Element design system via RAG. Provides AI agents with component APIs, UX writing guidelines, and front-end best practices with version matching.",
        "source_url": "https://element.siemens.io/get-started/element-mcp/",
        "env_vars": json.dumps(
            [
                {
                    "name": "SDL_MCP_TOKEN_ENV",
                    "label": "Use environment token",
                    "description": "Set to true in container/WSL/headless environments so the MCP reads the Siemens LLM token from environment variables instead of a system keychain.",
                    "required": False,
                    "secret": False,
                },
                {
                    "name": "OPENAI_API_KEY",
                    "label": "Siemens LLM API token",
                    "description": "Token from my.siemens.com with llm scope; upstream uses this variable name for the Siemens embeddings API.",
                    "required": True,
                    "secret": True,
                },
            ]
        ),
        "instructions": (
            "Install in the user's project with `npm install --save-dev --save-exact "
            "@siemens/element-mcp@49.12.0-v.1.11.1`, configure a Siemens LLM token with "
            "`element-mcp setup-token` or `SDL_MCP_TOKEN_ENV=true OPENAI_API_KEY=...`, then run "
            "`npx @siemens/element-mcp`."
        ),
    },
    {
        "server_id": "siemens-wincc-unified",
        "name": "Siemens WinCC Unified",
        "type": "stdio",
        "command": json.dumps(["wincc-unified-mcp.exe"]),
        "category": "plm",
        "image_url": "https://avatars.githubusercontent.com/u/4006395?s=64",
        "description": "Official Siemens WinCC Unified PC Runtime MCP candidate. Access real-time data tags, UDTs, alarms, and runtime operations after installing the Siemens Support artifact on a Windows WinCC host.",
        "source_url": "https://support.industry.siemens.com/cs/document/110002407",
    },
    {
        "server_id": "ptc-thingworx-mcp",
        "name": "PTC ThingWorx IoT",
        "type": "sse",
        "command": "${THINGWORX_BASE_URL}/mcp",
        "category": "plm",
        "image_url": "https://avatars.githubusercontent.com/u/1690598?s=64",
        "description": "PTC ThingWorx 10.1+ product-hosted MCP endpoint. Tools for machine KPIs, resources for sensor data, prompts for interaction templates, and MCPServices configuration.",
        "source_url": "https://support.ptc.com/help/thingworx/platform/r10.1/",
        "env_vars": json.dumps(
            [
                {
                    "name": "THINGWORX_BASE_URL",
                    "label": "ThingWorx server URL",
                    "description": "Base URL for a ThingWorx 10.1+ server with MCP enabled; the MCP endpoint is `${THINGWORX_BASE_URL}/mcp`.",
                    "required": True,
                    "secret": False,
                },
                {
                    "name": "THINGWORX_APP_KEY",
                    "label": "Application Key",
                    "description": "ThingWorx application key when the deployment uses AppKey authentication.",
                    "required": False,
                    "secret": True,
                },
                {
                    "name": "THINGWORX_OAUTH_TOKEN",
                    "label": "OAuth token",
                    "description": "OAuth bearer token for ThingWorx deployments using RFC 9728-protected MCP metadata.",
                    "required": False,
                    "secret": True,
                },
            ]
        ),
        "instructions": "Configure the MCP client to `${THINGWORX_BASE_URL}/mcp` for a ThingWorx 10.1+ server with MCP enabled, then provide the deployment's AppKey or OAuth credential.",
    },
    #  CAD  Desktop / Windows Required
    {
        "server_id": "fusion360-mcp-faust",
        "name": "Autodesk Fusion 360",
        "type": "stdio",
        "command": json.dumps(
            [
                "uv",
                "run",
                "--with",
                "fusion360-mcp-server",
                "fusion360-mcp-server",
                "--mode",
                "socket",
            ]
        ),
        "category": "cad",
        "image_url": "https://avatars.githubusercontent.com/u/1478570?s=64",
        "description": "85-tool Fusion 360 bridge for parametric sketching, sheet metal, Boolean operations, export, and CAM. Requires the Fusion360MCP add-in running inside Fusion 360 on a supported desktop host.",
        "source_url": "https://github.com/faust-machines/fusion360-mcp-server",
    },
    {
        "server_id": "autodesk-fusion-mcp-python",
        "name": "Fusion 360 Python API Bridge",
        "type": "stdio",
        "command": json.dumps(["python", "fusion_mcp.py"]),
        "category": "cad",
        "image_url": "https://avatars.githubusercontent.com/u/1478570?s=64",
        "description": "Small Fusion 360/Autodesk Platform Services MCP exposing a generate_cube Design Automation tool plus a separate LiveCube Fusion add-in bridge. Current upstream auth helper is broken with current httpx.",
        "source_url": "https://github.com/sockcymbal/autodesk-fusion-mcp-python",
        "env_vars": json.dumps(
            [
                {
                    "name": "APS_CLIENT_ID",
                    "label": "APS client ID",
                    "description": "Autodesk Platform Services client ID.",
                    "required": True,
                    "secret": False,
                },
                {
                    "name": "APS_CLIENT_SECRET",
                    "label": "APS client secret",
                    "description": "Autodesk Platform Services client secret.",
                    "required": True,
                    "secret": True,
                },
                {
                    "name": "FUSION_ACTIVITY_ID",
                    "label": "Fusion activity ID",
                    "description": "Registered APS Design Automation activity ID, for example nick.GenerateCube+prod.",
                    "required": True,
                    "secret": False,
                },
            ]
        ),
    },
    {
        "server_id": "solidworks-mcp-python",
        "name": "SolidWorks MCP (Python)",
        "type": "stdio",
        "command": json.dumps(["python", "-m", "solidworks_mcp.server"]),
        "category": "cad",
        "image_url": "https://avatars.githubusercontent.com/u/6536550?s=64",
        "description": "Python SolidWorks COM automation MCP. Current source installs on Ubuntu but fails before MCP startup due to a pydantic-ai API mismatch; live CAD use also requires Windows 10/11 + SolidWorks.",
        "source_url": "https://github.com/andrewbartels1/SolidworksMCP-python",
    },
    {
        "server_id": "solidworks-mcp-ts",
        "name": "SolidWorks MCP (TypeScript)",
        "type": "stdio",
        "command": json.dumps(["node", "dist/index.js"]),
        "category": "cad",
        "image_url": "https://avatars.githubusercontent.com/u/6536550?s=64",
        "description": "TypeScript SolidWorks integration via winax COM. Installs, builds, tests, and tool-lists on Ubuntu; live CAD tools require Windows + SolidWorks + working winax.",
        "source_url": "https://github.com/vespo92/SolidworksMCP-TS",
    },
    {
        "server_id": "solidworks-mcp-alisamsam",
        "name": "SolidWorks MCP (alisamsam)",
        "type": "stdio",
        "command": json.dumps(["python", "solidworks_mcp_server.py"]),
        "category": "cad",
        "image_url": "https://avatars.githubusercontent.com/u/6536550?s=64",
        "description": "Python SolidWorks MCP candidate with 22 advertised tools. Current requirements fail before MCP startup due to an unavailable asyncio-compat package and Windows-only pywin32 import.",
        "source_url": "https://github.com/alisamsam/solidworks-mcp",
    },
    {
        "server_id": "solidworks-api-docs",
        "name": "SolidWorks API Docs",
        "type": "stdio",
        "command": json.dumps(["bun", "run", "start"]),
        "category": "cad",
        "image_url": "https://avatars.githubusercontent.com/u/6536550?s=64",
        "description": "Full-text and keyword search over the SolidWorks API documentation corpus. Look up interface members and enums during code generation.",
        "source_url": "https://github.com/kilwizac/solidworks-api-mcp",
        "env_vars": json.dumps(
            [
                {
                    "name": "SW_API_DATA_ROOT",
                    "label": "SolidWorks API data root",
                    "description": "Optional path to the local SolidWorks API documentation corpus. Defaults to the cloned repository's `solidworks-api` directory.",
                    "required": False,
                    "secret": False,
                }
            ]
        ),
        "instructions": (
            "Clone `https://github.com/kilwizac/solidworks-api-mcp`, install Bun, run `bun install`, "
            "and launch from the clone with `bun run start`. This is a documentation/search MCP and does not require "
            "SolidWorks desktop software."
        ),
    },
    {
        "server_id": "creo-parametric-mcp",
        "name": "Creo/CadQuery MCP",
        "type": "stdio",
        "command": json.dumps(
            [
                "uvx",
                "creo-mcp",
                "--authorization",
                "${VOLCENGINE_AUTHORIZATION}",
                "--service-resource-id",
                "${VOLCENGINE_SERVICE_RESOURCE_ID}",
            ]
        ),
        "category": "cad",
        "image_url": "https://avatars.githubusercontent.com/u/1690598?s=64",
        "description": "CadQuery code-execution MCP that can export STEP files locally, query a Volcengine knowledge base, and open STEP files in Creo through a local CREOSON bridge.",
        "source_url": "https://github.com/yangkunyi/creo-mcp",
        "env_vars": json.dumps(
            [
                {
                    "name": "VOLCENGINE_AUTHORIZATION",
                    "label": "Volcengine authorization token",
                    "description": "Authorization token used by the optional Volcengine knowledge-base tool.",
                    "required": True,
                    "secret": True,
                },
                {
                    "name": "VOLCENGINE_SERVICE_RESOURCE_ID",
                    "label": "Volcengine service resource ID",
                    "description": "Service resource ID used by the optional Volcengine knowledge-base tool.",
                    "required": True,
                    "secret": False,
                },
            ]
        ),
    },
    {
        "server_id": "rhino-mcp-mcneel",
        "name": "Rhino 3D (McNeel)",
        "type": "stdio",
        "command": json.dumps(["uvx", "rhinomcp"]),
        "category": "cad",
        "image_url": "https://avatars.githubusercontent.com/u/1220980?s=64",
        "description": "NURBS surface modeling via Rhino 3D. Precise primitive generation, layer filtering, and experimental RhinoCommon C# script execution.  Requires Rhino 3D.",
        "source_url": "https://github.com/jingcheng-chen/rhinomcp",
    },
    {
        "server_id": "blender-mcp-ahujasid",
        "name": "Blender 3D",
        "type": "stdio",
        "command": json.dumps(["uvx", "--python", "3.11", "blender-mcp"]),
        "category": "cad",
        "image_url": "https://avatars.githubusercontent.com/u/52924985?s=64",
        "description": "Control Blender via a BlenderMCP add-on socket: scene inspection, viewport screenshots, Python code execution, lighting, procedural textures, Poly Haven/Sketchfab assets, and optional 3D generation integrations.",
        "source_url": "https://github.com/ahujasid/blender-mcp",
    },
    {
        "server_id": "sketchup-mcp-mhyrr",
        "name": "SketchUp 3D",
        "type": "stdio",
        "command": json.dumps(["uvx", "sketchup-mcp"]),
        "category": "cad",
        "image_url": "https://avatars.githubusercontent.com/u/458134?s=64",
        "description": "Ruby-based TCP server in SketchUp. Component manipulation, material application, and Ruby code evaluation.  Requires SketchUp desktop.",
        "source_url": "https://github.com/mhyrr/sketchup-mcp",
    },
    {
        "server_id": "revit-mcp-servers",
        "name": "Autodesk Revit BIM",
        "type": "stdio",
        "command": json.dumps(["node", "build/index.js"]),
        "category": "cad",
        "image_url": "https://avatars.githubusercontent.com/u/1478570?s=64",
        "description": "BIM automation bridge for Revit. Exposes model query, element creation, tagging, room export, and C# code execution tools through a Revit plugin socket.",
        "source_url": "https://github.com/mcp-servers-for-revit/revit-mcp",
    },
    #  2D CAD / Drafting
    {
        "server_id": "autocad-mcp-hvkshetry",
        "name": "AutoCAD MCP",
        "type": "stdio",
        "command": json.dumps(
            [
                "uv",
                "run",
                "--with",
                "git+https://github.com/hvkshetry/autocad-mcp.git",
                "python",
                "-m",
                "autocad_mcp",
            ]
        ),
        "category": "cad",
        "image_url": "https://avatars.githubusercontent.com/u/1478570?s=64",
        "description": "AutoCAD/LT automation bridge with a Linux-safe ezdxf backend for headless DXF generation plus a Windows AutoCAD File IPC backend for desktop automation.",
        "source_url": "https://github.com/hvkshetry/autocad-mcp",
        "env_vars": json.dumps(
            [
                {
                    "name": "AUTOCAD_MCP_BACKEND",
                    "label": "AutoCAD MCP backend",
                    "description": "Use `ezdxf` for Linux headless DXF generation, `file_ipc` for Windows AutoCAD IPC, or `auto` for upstream auto-selection.",
                    "required": False,
                    "secret": False,
                }
            ]
        ),
    },
    {
        "server_id": "easy-mcp-autocad",
        "name": "Easy-MCP-AutoCAD",
        "type": "stdio",
        "command": json.dumps(["python", "server.py"]),
        "category": "cad",
        "image_url": "https://avatars.githubusercontent.com/u/1478570?s=64",
        "description": "AutoCAD integration with SQLite data persistence. Extracts elemental data into queryable databases for BOM extraction and spatial analysis.  Requires AutoCAD.",
        "source_url": "https://github.com/zh19980811/Easy-MCP-AutoCad",
    },
    {
        "server_id": "multicad-mcp-ancode666",
        "name": "MultiCAD MCP",
        "type": "stdio",
        "command": json.dumps(["python", "src/server.py"]),
        "category": "cad",
        "image_url": None,
        "description": "Cross-platform 2D CAD control for ZWCAD 2020+, GstarCAD 2020+, and BricsCAD 21+ via Windows COM. Execute drawing commands via natural language.  Windows only.",
        "source_url": "https://github.com/AnCode666/multiCAD-mcp",
    },
    {
        "server_id": "cad-mcp-daobataotie",
        "name": "CAD-MCP Universal",
        "type": "stdio",
        "command": json.dumps(["python", "src/server.py"]),
        "category": "cad",
        "image_url": None,
        "description": "Universal 2D CAD automation via COM. Compatible with AutoCAD-like APIs. Draw, plot, and manipulate 2D geometry.  Requires Windows + CAD software.",
        "source_url": "https://github.com/daobataotie/CAD-MCP",
    },
    #  Web / Experimental
    {
        "server_id": "webmcp-standard",
        "name": "WebMCP Standard",
        "type": "webmcp",
        "command": "https://webmcp.io",
        "category": "utilities",
        "image_url": None,
        "description": "Open standard for browser-based AI interaction. Exposes webpage functionality as MCP tools directly to agents  eliminates brittle DOM actuation.",
        "source_url": "https://github.com/anthropics/anthropic-cookbook",
    },
    {
        "server_id": "mcp-ui-shopify",
        "name": "MCP-UI (Shopify)",
        "type": "webmcp",
        "command": "https://mcp-ui.dev",
        "category": "utilities",
        "image_url": "https://avatars.githubusercontent.com/u/8085?s=64",
        "description": "Renders interactive UI components (3D viewers, charts, sliders) inside chat interfaces. Eliminates the 'text wall' problem in LLM conversations.",
        "source_url": "https://github.com/anthropics/anthropic-cookbook",
    },
    {
        "server_id": "web3d-mcp-r3f",
        "name": "Web3D MCP (React Three Fiber)",
        "type": "stdio",
        "command": json.dumps(["node", "dist/server.js"]),
        "category": "utilities",
        "image_url": None,
        "description": "Generate, animate, and export 3D scenes using React Three Fiber (R3F). Programmatic 3D creation via modern web infrastructure.",
        "source_url": "https://github.com/dev261004/web3d-mcp-server",
    },
    {
        "server_id": "webmcp-openscad-jherr",
        "name": "WebMCP-OpenSCAD",
        "type": "webmcp",
        "command": "https://webmcp-openscad.dev",
        "category": "utilities",
        "image_url": "https://avatars.githubusercontent.com/u/37583508?s=64",
        "description": "Web-based 3D modeling interface built with TanStack Start. Integrates AI support directly into browser-based OpenSCAD workflows.",
        "source_url": "https://github.com/jherr/webmcp-openscad",
    },
    #  Manufacturing / CAM
    {
        "server_id": "creopyson-creoson",
        "name": "CREOSON Middleware",
        "type": "stdio",
        "command": json.dumps(
            [
                "java",
                "-classpath",
                "*.jar",
                "com.simplifiedlogic.nitro.jshell.MainServer",
            ]
        ),
        "category": "manufacturing",
        "image_url": "https://avatars.githubusercontent.com/u/1690598?s=64",
        "description": "CREOSON JSON-RPC middleware for Creo Parametric. This is a Java/JLINK bridge dependency for Creo workflows, not an MCP protocol server by itself.",
        "source_url": "https://github.com/SimplifiedLogic/creoson",
    },
    #  CAD  Cloud / Credential-Requiring
    {
        "server_id": "jarvis-onshape-mcp",
        "name": "Jarvis OnShape MCP",
        "type": "stdio",
        "command": json.dumps(
            [
                "uv",
                "run",
                "--with",
                "git+https://github.com/ReshefElisha/jarvis-onshape-mcp.git",
                "onshape-mcp",
            ]
        ),
        "category": "cad",
        "image_url": "https://avatars.githubusercontent.com/u/6536550?s=64",
        "description": "AI copilot for Onshape CAD. 60+ tools: parametric sketches, extrudes, fillets, assemblies, Variable Studios, FeatureScript, and multi-view rendering with vision feedback.",
        "source_url": "https://github.com/ReshefElisha/jarvis-onshape-mcp",
        "env_vars": json.dumps(
            [
                {
                    "name": "ONSHAPE_API_KEY",
                    "label": "Access Key",
                    "description": "Onshape API access key from dev-portal.onshape.com",
                    "required": True,
                    "secret": False,
                },
                {
                    "name": "ONSHAPE_API_SECRET",
                    "label": "Secret Key",
                    "description": "Onshape API secret key (shown once at creation)",
                    "required": True,
                    "secret": True,
                },
            ]
        ),
    },
    {
        "server_id": "kicad-mcp-lamaalrajih",
        "name": "KiCad MCP",
        "type": "stdio",
        "command": json.dumps(
            [
                "uv",
                "tool",
                "run",
                "--from",
                "git+https://github.com/lamaalrajih/kicad-mcp.git",
                "kicad-mcp",
            ]
        ),
        "category": "cad",
        "image_url": "https://avatars.githubusercontent.com/u/3374914?s=64",
        "description": "Community KiCad MCP for electronics project inspection and local bridge workflows. Requires KiCad 9.0+ for host-backed operations.",
        "source_url": "https://github.com/lamaalrajih/kicad-mcp",
    },
    {
        "server_id": "rosbag-mcp-binabik",
        "name": "ROSBag MCP",
        "type": "stdio",
        "command": json.dumps(["python", "src/server.py"]),
        "category": "analysis",
        "image_url": "https://avatars.githubusercontent.com/u/3979232?s=64",
        "description": "Community MCP for offline ROS bag file inspection and robotics data analysis. Optional ROS 2 extras may be needed for some workflows.",
        "source_url": "https://github.com/binabik-ai/mcp-rosbags",
    },
    {
        "server_id": "siemens-xcelerator-developer-portal-mcp",
        "name": "Siemens Xcelerator Developer Portal MCP",
        "type": "sse",
        "command": "https://developer.siemens.com/",
        "category": "plm",
        "image_url": "https://avatars.githubusercontent.com/u/4006395?s=64",
        "description": "Documentation/help MCP candidate for Siemens developer-portal product, API, and resource discovery. Treat as read-only docs until the exact client config URL is pinned.",
        "source_url": "https://developer.siemens.com/",
    },
    {
        "server_id": "autodesk-product-help-mcp",
        "name": "Autodesk Product Help MCP",
        "type": "sse",
        "command": "https://developer.api.autodesk.com/knowledge/public/v1/mcp",
        "category": "utilities",
        "image_url": "https://avatars.githubusercontent.com/u/1478570?s=64",
        "description": "Official remote Autodesk Product Help MCP for read-only access to Autodesk Help content across 110+ products.",
        "source_url": "https://help.autodesk.com/view/ADSKMCP/ENU/?guid=ADSKMCP_KnowledgeMcp_autodesk_product_help_mcp_server_html",
    },
]


HIGH_RISK_GATES = ["workspace_write_approval", "execute_code_approval"]
CLOUD_GATES = ["secrets_approval", "cloud_upload_approval"]
MACHINE_CONTROL_GATES = ["machine_control_approval"]


def _with_meta(entry, **metadata):
    return normalize_mcp_seed_entry(entry, metadata)


def _catalog_entry_to_seed(entry):
    return catalog_entry_to_mcp_seed(entry)


def _hosted(notes):
    return platform_support(
        {
            "windows_11_x64": {
                "status": "host-dependent",
                "tested": False,
                "notes": notes,
            },
            "linux_x64": {"status": "host-dependent", "tested": False, "notes": notes},
            "linux_arm64": {
                "status": "unknown",
                "tested": False,
                "notes": "host stack not tested on ARM64",
            },
            "macos_x64": {"status": "host-dependent", "tested": False, "notes": notes},
            "macos_arm64": {
                "status": "host-dependent",
                "tested": False,
                "notes": notes,
            },
        }
    )


CATALOG_METADATA = {
    "openscad-mcp-server": {
        "verification_state": "community_mcp",
        "installability_tier": "tested",
        "risk_level": "medium",
        "deployment_mode": "local-bridge",
        "host_software_required": ["OpenSCAD"],
        "platform_support": platform_support(
            {
                "windows_11_x64": {
                    "status": "likely",
                    "tested": False,
                    "notes": "OpenSCAD host available on Windows",
                },
                "linux_x64": {
                    "status": "yes",
                    "tested": True,
                    "notes": "clean Intel Ubuntu container: per-MCP OpenSCAD install, direct MCP probe, and Wright gateway export probe passed",
                },
                "macos_x64": {
                    "status": "likely",
                    "tested": False,
                    "notes": "OpenSCAD host available on macOS",
                },
                "macos_arm64": {
                    "status": "likely",
                    "tested": False,
                    "notes": "OpenSCAD host available on macOS ARM64",
                },
            }
        ),
        "approval_gates": ["workspace_write_approval"],
        "validation_result": validation_summary(
            "passed",
            "Clean Intel Ubuntu validation passed: installed OpenSCAD/Xvfb only for this MCP, initialized openscad-mcp, listed tools, check_openscad passed, exported a 1449-byte cube STL, and verified the Wright/Hermes gateway exposes and calls the prefixed tools.",
            "ubuntu-linux-x64-container",
        ),
    },
    "caid-opencascade-dreliq9": {
        "verification_state": "community_mcp",
        "installability_tier": "tested",
        "risk_level": "medium",
        "deployment_mode": "local-only",
        "host_software_required": ["CAiD", "OCP/OpenCASCADE", "libGL"],
        "platform_support": platform_support(
            {
                "windows_11_x64": {
                    "status": "likely",
                    "tested": False,
                    "notes": "Python/OCP stack expected but not tested on Windows",
                },
                "linux_x64": {
                    "status": "yes",
                    "tested": True,
                    "notes": "clean Intel Ubuntu validation installed libGL, CAiD from GitHub source, and caid-mcp; tests passed and `create_box` returned validated geometry",
                },
                "linux_arm64": {
                    "status": "unknown",
                    "tested": False,
                    "notes": "not tested; OCP/OpenCASCADE wheels must be checked",
                },
                "macos_x64": {
                    "status": "likely",
                    "tested": False,
                    "notes": "Python/OCP stack expected but not tested on macOS",
                },
                "macos_arm64": {
                    "status": "unknown",
                    "tested": False,
                    "notes": "not tested; OCP/OpenCASCADE wheels must be checked",
                },
            }
        ),
        "approval_gates": ["workspace_write_approval"],
        "validation_result": validation_summary(
            "passed",
            "Clean Intel Ubuntu validation passed: installed `libgl1`, CAiD from GitHub commit 840d9ece24499dca4d1cc6b7a7aef2b88a203f14, and caid-mcp from commit bb863e9fe64f951fac9d59daed26254544682bc3; upstream MCP tests passed 72/72, MCP initialized, listed 107 tools, `create_box` returned ok with volume 480 mm^3, and scene query reported the 10 x 8 x 6 mm box.",
            "ubuntu-linux-x64-container",
        ),
    },
    "openscad-linter-trikos529": {
        "verification_state": "user_reported_url_needed",
        "installability_tier": "non_working",
        "risk_level": "low",
        "deployment_mode": "unknown",
        "host_software_required": ["OpenSCAD"],
        "platform_support": platform_support(
            {
                "windows_11_x64": {
                    "status": "unknown",
                    "tested": False,
                    "notes": "exact MCP source/package is not verified",
                },
                "linux_x64": {
                    "status": "no",
                    "tested": True,
                    "notes": "clean Intel Ubuntu validation could not resolve `openscad-linter-mcp` from the configured command",
                },
                "linux_arm64": {
                    "status": "unknown",
                    "tested": False,
                    "notes": "not tested; blocked until source/package is verified",
                },
                "macos_x64": {
                    "status": "unknown",
                    "tested": False,
                    "notes": "exact MCP source/package is not verified",
                },
                "macos_arm64": {
                    "status": "unknown",
                    "tested": False,
                    "notes": "exact MCP source/package is not verified",
                },
            }
        ),
        "validation_result": validation_summary(
            "failed",
            "Clean Intel Ubuntu validation failed before MCP startup: `uv tool run openscad-linter-mcp --help` reported that `openscad-linter-mcp` was not found in the package registry, and the configured source URL is only a GitHub topic page.",
            "ubuntu-linux-x64-container",
        ),
        "follow_up_url": "docs/mcp-catalog/followups/openscad-linter-trikos529.md",
        "install_blocked_reason": "Exact MCP source URL/package is not verified; current URL is only a topic/reference page and the configured package name does not resolve.",
    },
    "zoo-dev-cloud-cad": {
        "verification_state": "verified_mcp",
        "installability_tier": "might_work",
        "risk_level": "medium",
        "deployment_mode": "cloud-saas",
        "credentials_required": ["ZOO_API_TOKEN"],
        "platform_support": platform_support(
            {
                "windows_11_x64": {
                    "status": "likely",
                    "tested": False,
                    "notes": "Python/uv stdio MCP expected; not tested on Windows",
                },
                "linux_x64": {
                    "status": "yes",
                    "tested": True,
                    "notes": "clean Intel Ubuntu validation installed from source, initialized MCP, listed tools, and verified local docs search; full CAD compute requires ZOO_API_TOKEN",
                },
                "linux_arm64": {
                    "status": "unknown",
                    "tested": False,
                    "notes": "not tested; Python wheels must be checked",
                },
                "macos_x64": {
                    "status": "likely",
                    "tested": False,
                    "notes": "Python/uv stdio MCP expected; not tested on macOS",
                },
                "macos_arm64": {
                    "status": "likely",
                    "tested": False,
                    "notes": "Python/uv stdio MCP expected; not tested on macOS ARM64",
                },
            }
        ),
        "approval_gates": CLOUD_GATES,
        "validation_result": validation_summary(
            "dependency_missing",
            "Clean Intel Ubuntu validation installed KittyCAD/zoo-mcp at 0868cac70443f1151226a2a33663730765ad038b, confirmed missing credentials fail before MCP initialization with `No API token provided`, and with a dummy `ZOO_API_TOKEN` initialized serverInfo `Zoo MCP Server` 1.27.1, listed 30 tools, and `search_kcl_docs` returned KCL documentation results. A backend CAD call `calculate_volume` reached the Zoo API and returned a clear bad-authentication diagnostic. Upstream non-live tests with a dummy token passed 120 tests, skipped 2, deselected 6, and failed 33 cloud/KCL-engine tests due invalid credentials.",
            "ubuntu-linux-x64-container",
            ["ZOO_API_TOKEN"],
        ),
        "headless_ok": "yes",
    },
    "webmcp-openscad-jherr": {
        "verification_state": "community_mcp",
        "installability_tier": "might_work",
        "risk_level": "medium",
        "deployment_mode": "browser-bridge",
        "host_software_required": [
            "browser with WebMCP page",
            "MCP-B extension or @mcp-b/webmcp-local-relay",
        ],
        "platform_support": platform_support(
            {
                "windows_11_x64": {
                    "status": "host-dependent",
                    "tested": False,
                    "notes": "requires Node, a browser tab running the WebMCP OpenSCAD app, and MCP-B or native WebMCP bridge",
                },
                "linux_x64": {
                    "status": "host-dependent",
                    "tested": True,
                    "notes": "clean Intel Ubuntu validation installed Node 22 and pnpm, built the app, initialized the local relay MCP, and confirmed page tools require a connected browser source",
                },
                "linux_arm64": {
                    "status": "unknown",
                    "tested": False,
                    "notes": "not tested; browser/WebMCP bridge and OpenSCAD WASM package support must be checked",
                },
                "macos_x64": {
                    "status": "host-dependent",
                    "tested": False,
                    "notes": "requires Node, a browser tab running the WebMCP OpenSCAD app, and MCP-B or native WebMCP bridge",
                },
                "macos_arm64": {
                    "status": "host-dependent",
                    "tested": False,
                    "notes": "requires Node, a browser tab running the WebMCP OpenSCAD app, and MCP-B or native WebMCP bridge",
                },
            }
        ),
        "approval_gates": ["workspace_write_approval"],
        "validation_result": validation_summary(
            "dependency_missing",
            "Clean Intel Ubuntu validation cloned jherr/webmcp-openscad at commit a3acb68578701001f0251459c75716a55aadfa10. Ubuntu's default Node 18 could not run pnpm 11.9.0, so validation installed Node 22.23.1 with `n` after adding curl. `pnpm install --frozen-lockfile` succeeded with pnpm 11.9.0. `pnpm test` did not find any test files and exited 1, with additional Vitest/Vite shutdown noise `ReferenceError: module is not defined`; this repo does not currently provide a usable upstream test suite. `pnpm build` succeeded for the TanStack/Nitro app. Serving `node .output/server/index.mjs` produced a 7156-byte HTML page titled `scad-webmcp  agent-driven parametric CAD` that embeds `@mcp-b/webmcp-local-relay@latest/dist/browser/embed.js`. MCP stdio probing `npx -y @mcp-b/webmcp-local-relay@latest` initialized serverInfo `webmcp-local-relay` version 0.0.0, listed 4 relay tools, and calls to `webmcp_list_sources` and `webmcp_list_tools` returned zero sources/tools because no browser page was connected. Full validation of the advertised 16 OpenSCAD browser tools requires a browser tab connected through MCP-B or native WebMCP.",
            "ubuntu-linux-x64-container",
            [
                "browser tab running scad-webmcp",
                "MCP-B extension or native WebMCP bridge",
            ],
        ),
        "headless_ok": "no",
    },
    "web3d-mcp-r3f": {
        "verification_state": "community_mcp",
        "installability_tier": "tested",
        "risk_level": "medium",
        "deployment_mode": "local-only",
        "platform_support": platform_support(
            {
                "windows_11_x64": {
                    "status": "likely",
                    "tested": False,
                    "notes": "Node 22+ stdio server expected; not tested on Windows",
                },
                "linux_x64": {
                    "status": "yes",
                    "tested": True,
                    "notes": "clean Intel Ubuntu validation installed from GitHub source with Node 22, passed tests, initialized MCP, and generated validated R3F code",
                },
                "linux_arm64": {
                    "status": "unknown",
                    "tested": False,
                    "notes": "not tested; Node dependency support must be checked",
                },
                "macos_x64": {
                    "status": "likely",
                    "tested": False,
                    "notes": "Node 22+ stdio server expected; not tested on macOS",
                },
                "macos_arm64": {
                    "status": "likely",
                    "tested": False,
                    "notes": "Node 22+ stdio server expected; not tested on macOS ARM64",
                },
            }
        ),
        "approval_gates": ["workspace_write_approval"],
        "validation_result": validation_summary(
            "passed",
            "Clean Intel Ubuntu validation found the seeded `npx web3d-mcp` package and `https://web3d-mcp.dev` URL invalid: npm returned 404 for `web3d-mcp` and `web3d-mcp-server`, and DNS could not resolve `web3d-mcp.dev`. Web search and the Reddit source identified the real source as dev261004/web3d-mcp-server. Validation cloned commit b6e3cb59ba243ab53be2e1b1a674e5199bfc0c6a. With Ubuntu's Node 18.19.1, `npm install`, `npm run build`, and health checks passed but direct MCP startup failed with `ReferenceError: File is not defined` from undici; after installing Node 22.23.1 with `n`, MCP stdio started successfully. Full upstream `npm test -- --runInBand` passed 10 suites and 65 tests; the build precheck also passed 7 health suites and 54 tests. MCP initialized as serverInfo `3d-scene-mcp` version 1.0.0 using newline-delimited JSON framing and listed 12 tools. Tool calls generated a cube scene via `generate_scene`, `validate_scene` returned `is_valid:true` with all 13 checks passed, `preview` returned SVG wireframe data, and `generate_r3f_code` returned `SUCCESS` with 948 bytes of Vite/TypeScript React Three Fiber code. npm audit reported 33 vulnerabilities in installed dependencies, and upstream README still says Node 18+ even though runtime startup required Node 22 in this container.",
            "ubuntu-linux-x64-container",
        ),
        "headless_ok": "yes",
    },
    "rhino-mcp-mcneel": {
        "verification_state": "community_mcp",
        "installability_tier": "might_work",
        "risk_level": "high",
        "deployment_mode": "local-bridge",
        "host_software_required": [
            "Rhino 8",
            "RhinoMCP plugin",
            "mcpstart bridge on 127.0.0.1:1999",
        ],
        "platform_support": platform_support(
            {
                "windows_11_x64": {
                    "status": "host-dependent",
                    "tested": False,
                    "notes": "README targets Rhino 8 on Windows and macOS; Windows host must install the RhinoMCP plugin and run `mcpstart`",
                },
                "linux_x64": {
                    "status": "host-dependent",
                    "tested": True,
                    "notes": "clean Intel Ubuntu validation installed and started the Python stdio MCP, listed tools, and reached the expected missing Rhino bridge diagnostic",
                },
                "linux_arm64": {
                    "status": "host-dependent",
                    "tested": False,
                    "notes": "Python stdio client may run, but a Rhino 8 bridge host is still required; not tested on ARM64",
                },
                "macos_x64": {
                    "status": "host-dependent",
                    "tested": False,
                    "notes": "README targets Rhino 8 on macOS; install plugin and run `mcpstart`",
                },
                "macos_arm64": {
                    "status": "host-dependent",
                    "tested": False,
                    "notes": "README targets Rhino 8 on macOS; install plugin and run `mcpstart`",
                },
            }
        ),
        "approval_gates": HIGH_RISK_GATES,
        "validation_result": validation_summary(
            "dependency_missing",
            "Clean Intel Ubuntu validation cloned jingcheng-chen/rhinomcp at commit b56338a9da733d17555744ab895facdc84a80542. The current Python MCP package is `rhinomcp` version 0.3.1 with console command `rhinomcp`; upstream Python/contract tests passed 192/192 with 12 pytest return-value warnings. MCP stdio initialized from source as serverInfo `RhinoMCP` version 1.26.0 and listed 66 tools. `get_commands`, `get_document_summary`, and backend-touching `create_object` all returned the expected missing-bridge diagnostic: `Could not connect to Rhino at 127.0.0.1:1999. Please start Rhino, run the Rhino command `mcpstart`, then retry the MCP request.` Full validation requires Rhino 8 with the RhinoMCP plugin installed and `mcpstart` running.",
            "ubuntu-linux-x64-container",
            ["Rhino 8", "RhinoMCP plugin", "mcpstart bridge on 127.0.0.1:1999"],
        ),
        "headless_ok": "no",
    },
    "sketchup-mcp-mhyrr": {
        "verification_state": "community_mcp",
        "installability_tier": "might_work",
        "risk_level": "high",
        "deployment_mode": "local-bridge",
        "host_software_required": [
            "SketchUp",
            "SketchupMCP extension",
            "extension server on port 9876",
        ],
        "platform_support": platform_support(
            {
                "windows_11_x64": {
                    "status": "host-dependent",
                    "tested": False,
                    "notes": "requires SketchUp desktop plus the SketchupMCP extension server on port 9876; not tested on Windows",
                },
                "linux_x64": {
                    "status": "host-dependent",
                    "tested": True,
                    "notes": "clean Intel Ubuntu validation installed and started the Python stdio MCP, listed tools, and reached the expected missing SketchUp extension diagnostic",
                },
                "linux_arm64": {
                    "status": "host-dependent",
                    "tested": False,
                    "notes": "Python stdio client may run, but a SketchUp extension host is still required; not tested on ARM64",
                },
                "macos_x64": {
                    "status": "host-dependent",
                    "tested": False,
                    "notes": "requires SketchUp desktop plus the SketchupMCP extension server; not tested on macOS",
                },
                "macos_arm64": {
                    "status": "host-dependent",
                    "tested": False,
                    "notes": "requires SketchUp desktop plus the SketchupMCP extension server; not tested on macOS ARM64",
                },
            }
        ),
        "approval_gates": HIGH_RISK_GATES,
        "validation_result": validation_summary(
            "dependency_missing",
            "Clean Intel Ubuntu validation cloned mhyrr/sketchup-mcp at commit aa096f04d3d7b22a70860368f2b576343feac405. The current MCP package is `sketchup-mcp` version 0.1.17 with console command `sketchup-mcp`; the README user command is `uvx sketchup-mcp`. The repo has no real pytest suite: `test_eval_ruby.py` is a script and pytest reports no tests, while `examples/simple_test.py` fails to collect because it imports removed `mcp.client.Client`. `uv tool run --from /tmp/sketchup-src sketchup-mcp --help` built the source package but started the server rather than printing CLI help. MCP stdio initialized as serverInfo `SketchupMCP` version 1.28.1 and listed 10 tools. README-advertised `get_scene_info` is not in `tools/list`; actual read/status `get_selection` returned `Could not connect to Sketchup. Make sure the Sketchup extension is running.` Backend-touching `eval_ruby` returned JSON `success: false` with the same missing-extension diagnostic. Full validation requires SketchUp desktop with the SketchupMCP extension server running.",
            "ubuntu-linux-x64-container",
            ["SketchUp", "SketchupMCP extension server on port 9876"],
        ),
        "headless_ok": "no",
    },
    "blender-mcp-ahujasid": {
        "verification_state": "community_mcp",
        "installability_tier": "tested",
        "risk_level": "high",
        "deployment_mode": "local-bridge",
        "host_software_required": ["Blender"],
        "platform_support": platform_support(
            {
                "windows_11_x64": {
                    "status": "host-dependent",
                    "tested": False,
                    "notes": "requires Blender desktop app and add-on; not tested on Windows",
                },
                "linux_x64": {
                    "status": "yes",
                    "tested": True,
                    "notes": "clean Intel Ubuntu validation installed Blender 4.0.2, python3-requests, and Xvfb; add-on socket started and MCP executed read/write Blender operations",
                },
                "linux_arm64": {
                    "status": "unknown",
                    "tested": False,
                    "notes": "not tested; Blender package and Python wheels must be checked",
                },
                "macos_x64": {
                    "status": "host-dependent",
                    "tested": False,
                    "notes": "requires Blender desktop app and add-on; not tested on macOS",
                },
                "macos_arm64": {
                    "status": "host-dependent",
                    "tested": False,
                    "notes": "requires Blender desktop app and add-on; not tested on macOS",
                },
            }
        ),
        "approval_gates": HIGH_RISK_GATES,
        "validation_result": validation_summary(
            "passed",
            "Clean Intel Ubuntu validation cloned blender-mcp at commit 6e99eb5a442b83766a5796975ec7bb5bfc791341, found no upstream tests, installed Blender 4.0.2, python3-requests, Xvfb, and uvx 0.11.25 only for this MCP, and launched the add-on under Xvfb. Without the add-on socket, MCP initialized as `BlenderMCP` 1.28.1, listed 22 tools, and `get_scene_info`/`execute_blender_code` returned the expected diagnostic that the Blender add-on is not running. With the add-on socket live, MCP initialized as `BlenderMCP` 1.28.1, listed 22 tools, `get_scene_info` returned the default Cube/Light/Camera scene, `execute_blender_code` created `WrightValidationCube` at (1.0, 2.0, 3.0), and `get_object_info` verified the cube mesh with 8 vertices, 12 edges, and 6 polygons.",
            "ubuntu-linux-x64-container",
        ),
    },
    "freecad-engineering-sandraschi": {
        "verification_state": "community_mcp",
        "installability_tier": "non_working",
        "risk_level": "high",
        "deployment_mode": "local-bridge",
        "host_software_required": ["FreeCAD", "CalculiX", "OpenFOAM", "PrusaSlicer"],
        "platform_support": platform_support(
            {
                "windows_11_x64": {
                    "status": "host-dependent",
                    "tested": False,
                    "notes": "requires FreeCAD and optional simulation/slicer hosts; not tested on Windows",
                },
                "linux_x64": {
                    "status": "no",
                    "tested": True,
                    "notes": "FreeCAD 1.1.1 AppImage installed and direct FreeCAD STL export worked, but MCP `freecad_status` stayed false and `create_shape` returned success while FreeCAD reported a mesh failure",
                },
                "linux_arm64": {
                    "status": "unknown",
                    "tested": False,
                    "notes": "not tested; host stack and wheels must be checked",
                },
                "macos_x64": {
                    "status": "host-dependent",
                    "tested": False,
                    "notes": "requires FreeCAD and optional simulation/slicer hosts",
                },
                "macos_arm64": {
                    "status": "host-dependent",
                    "tested": False,
                    "notes": "requires FreeCAD and optional simulation/slicer hosts",
                },
            }
        ),
        "approval_gates": HIGH_RISK_GATES,
        "validation_result": validation_summary(
            "failed",
            "Clean Intel Ubuntu validation cloned freecad-mcp at a71f60a71987ac23a65a3bdeda5f71c8f1579efb, installed dependencies with `uv sync --extra dev`, and upstream tests passed 94 with 2 integration tests deselected. MCP initialized as `FreeCAD MCP` 3.4.2, listed 47 tools, and `freecad_status` returned `success:false`/`freecad_ok:false`. FreeCAD 1.1.1 AppImage direct CLI exported `/tmp/direct_freecad_box.stl` at 684 bytes. The advertised `--freecad-path /tmp/freecadcmd` option did not affect the subprocess path: `create_shape` returned `FreeCADCmd not found`. With `FREECAD_PATH=/tmp/freecadcmd`, `create_shape` ran FreeCAD but returned `success:true` while stderr reported `Cannot create a mesh out of a 'Part.Solid'` and no STL output was produced.",
            "ubuntu-linux-x64-container",
        ),
        "follow_up_url": "docs/mcp-catalog/followups/freecad-engineering-sandraschi.md",
        "install_blocked_reason": "Clean Intel Ubuntu validation found incorrect success reporting and failed STL creation through the MCP server; see follow-up record.",
    },
    "freecad-copilot-contextform": {
        "verification_state": "community_mcp",
        "installability_tier": "non_working",
        "risk_level": "high",
        "deployment_mode": "local-bridge",
        "host_software_required": [
            "FreeCAD GUI",
            "AICopilot workbench",
            "Python",
            "Node.js",
        ],
        "platform_support": platform_support(
            {
                "windows_11_x64": {
                    "status": "host-dependent",
                    "tested": False,
                    "notes": "requires FreeCAD desktop with AI Copilot workbench",
                },
                "linux_x64": {
                    "status": "no",
                    "tested": True,
                    "notes": "clean Intel Ubuntu validation installed FreeCAD 1.1.1, Xvfb, and the workbench; MCP listed socket-backed tools, but `part_operations` hung and FreeCAD logged Qt thread errors",
                },
                "linux_arm64": {
                    "status": "unknown",
                    "tested": False,
                    "notes": "not tested; GUI/AppImage/workbench support must be checked",
                },
                "macos_x64": {
                    "status": "host-dependent",
                    "tested": False,
                    "notes": "requires FreeCAD desktop with AI Copilot workbench",
                },
                "macos_arm64": {
                    "status": "host-dependent",
                    "tested": False,
                    "notes": "requires FreeCAD desktop with AI Copilot workbench",
                },
            }
        ),
        "approval_gates": HIGH_RISK_GATES,
        "validation_result": validation_summary(
            "failed",
            "Clean Intel Ubuntu validation cloned contextform/freecad-mcp at commit de4fed2a7a4352fcb0de60d2b784063c54eeb812. The seeded `npx freecad-mcp` command is incorrect: the npm package is `freecad-mcp-setup` version 1.0.8 and the actual MCP bridge is `working_bridge.py`. `npm install` and `npm test` passed for the installer. `npx freecad-mcp setup` installed the workbench and warned that FreeCAD and Claude Code were not detected. Ubuntu apt had no `freecad` package candidate, so validation installed FreeCAD 1.1.1 revision 20260414 from the Linux x86_64 AppImage plus Xvfb, installed `mcp` for Python, and copied AICopilot to `~/.local/share/FreeCAD/v1-1/Mod/AICopilot`. FreeCAD launched under Xvfb and `/tmp/freecad_mcp.sock` appeared after 6 seconds. MCP stdio initialized as serverInfo `freecad` version 2.0.0, listed 7 tools, `check_freecad_connection` returned `FreeCAD running with AI Copilot workbench`, and `test_echo` returned `Bridge received: wright validation`. The first backend modeling call, `part_operations` with `operation=box`, `length=10`, `width=8`, `height=6`, and `name=WrightBox`, timed out after 30 seconds. FreeCAD logged `Event observer error: No module named 'PySide2'`, `QObject: Cannot create children for a parent that is in a different thread`, and `QObject::startTimer: Timers cannot be started from another thread`.",
            "ubuntu-linux-x64-container",
        ),
        "follow_up_url": "docs/mcp-catalog/followups/freecad-copilot-contextform.md",
        "install_blocked_reason": "Linux container validation reached the FreeCAD workbench socket, but the first safe Part operation hung; see follow-up record.",
    },
    "autocad-mcp-hvkshetry": {
        "verification_state": "community_mcp",
        "installability_tier": "tested",
        "risk_level": "medium",
        "deployment_mode": "local-only",
        "host_software_required": [],
        "platform_support": platform_support(
            {
                "windows_11_x64": {
                    "status": "host-dependent",
                    "tested": False,
                    "notes": "Windows AutoCAD File IPC backend requires AutoCAD LT 2024+ and was not tested in the Linux container",
                },
                "linux_x64": {
                    "status": "yes",
                    "tested": True,
                    "notes": "clean Intel Ubuntu validation passed with `AUTOCAD_MCP_BACKEND=ezdxf`: repo tests passed, MCP listed 8 tools, created a line, and saved a DXF",
                },
                "linux_arm64": {
                    "status": "unknown",
                    "tested": False,
                    "notes": "not tested; Python wheels and matplotlib/ezdxf stack must be checked",
                },
                "macos_x64": {
                    "status": "likely",
                    "tested": False,
                    "notes": "ezdxf backend should be host-independent but was not tested on macOS",
                },
                "macos_arm64": {
                    "status": "likely",
                    "tested": False,
                    "notes": "ezdxf backend should be host-independent but was not tested on macOS ARM64",
                },
            }
        ),
        "approval_gates": ["workspace_write_approval"],
        "validation_result": validation_summary(
            "passed",
            "Clean Intel Ubuntu validation passed with `AUTOCAD_MCP_BACKEND=ezdxf`: cloned commit 95476a33a1c246308326eb4709d6379ef2efdbc1, 123 upstream tests passed, the git-based user command initialized MCP serverInfo `autocad-mcp` 1.26.0, listed 8 tools, `system` reported ezdxf 1.4.3, a drawing and line were created, and `/tmp/wright-autocad-validation.dxf` was saved at 15561 bytes. Windows AutoCAD File IPC remains host-dependent and untested in the Linux container.",
            "ubuntu-linux-x64-container",
        ),
    },
    "multicad-mcp-ancode666": {
        "verification_state": "community_mcp",
        "installability_tier": "might_work",
        "risk_level": "high",
        "deployment_mode": "local-bridge",
        "host_software_required": [
            "Windows",
            "Windows COM",
            "pywin32",
            "AutoCAD 2018+",
            "ZWCAD 2020+",
            "GstarCAD 2020+",
            "BricsCAD 21+",
        ],
        "platform_support": platform_support(
            {
                "windows_11_x64": {
                    "status": "host-dependent",
                    "tested": False,
                    "notes": "README requires Windows, Python 3.10+, pywin32, and one supported CAD application with COM support",
                },
                "linux_x64": {
                    "status": "no",
                    "tested": True,
                    "notes": "clean Intel Ubuntu validation cloned source and confirmed Linux cannot install pywin32 or start the COM adapter",
                },
                "linux_arm64": {
                    "status": "no",
                    "tested": False,
                    "notes": "Windows COM and pywin32 are not available on Linux ARM64",
                },
                "macos_x64": {
                    "status": "no",
                    "tested": False,
                    "notes": "Windows COM and pywin32 are not available on macOS",
                },
                "macos_arm64": {
                    "status": "no",
                    "tested": False,
                    "notes": "Windows COM and pywin32 are not available on macOS ARM64",
                },
            }
        ),
        "approval_gates": HIGH_RISK_GATES,
        "validation_result": validation_summary(
            "dependency_missing",
            "Clean Intel Ubuntu validation cloned AnCode666/multiCAD-mcp at commit 360ec77c970ec95a962bd4d0a3238715ee78dd7c; package `multiCAD-mcp` version 0.2.0 documents Windows OS, Python 3.10+, and a COM-capable CAD application. Exact `pip install -e '.[dev]'` failed because `pywin32>=300` has no Linux distribution. Installing the source with `--no-deps` plus non-Windows dependencies succeeded, but upstream unit collection failed with `ImportError: AutoCAD adapter requires Windows OS with COM support`. `python src/server.py --help` and direct startup both exited before MCP initialization with the same diagnostic, so no MCP `initialize` or `tools/list` calls were possible in Linux. This is an expected host dependency boundary for Windows COM plus AutoCAD/ZWCAD/GstarCAD/BricsCAD, not a source availability failure.",
            "ubuntu-linux-x64-container",
            [
                "Windows",
                "Windows COM",
                "pywin32",
                "AutoCAD 2018+ or ZWCAD 2020+ or GstarCAD 2020+ or BricsCAD 21+",
            ],
        ),
        "headless_ok": "no",
    },
    "autodesk-aps-official": {
        "verification_state": "verified_mcp",
        "installability_tier": "might_work",
        "risk_level": "medium",
        "deployment_mode": "cloud-saas",
        "credentials_required": [
            "APS_CLIENT_ID",
            "APS_CLIENT_SECRET",
            "SSA_ID",
            "SSA_KEY_ID",
            "SSA_KEY_PATH",
        ],
        "platform_support": platform_support(
            {
                "windows_11_x64": {
                    "status": "likely",
                    "tested": False,
                    "notes": "Node stdio server; requires Autodesk APS/ACC credentials",
                },
                "linux_x64": {
                    "status": "host-dependent",
                    "tested": True,
                    "notes": "clean Intel Ubuntu validation installed npm dependencies and confirmed the expected missing-credential diagnostic",
                },
                "linux_arm64": {
                    "status": "unknown",
                    "tested": False,
                    "notes": "not tested; Node dependencies must be checked",
                },
                "macos_x64": {
                    "status": "likely",
                    "tested": False,
                    "notes": "Node stdio server; requires Autodesk APS/ACC credentials",
                },
                "macos_arm64": {
                    "status": "likely",
                    "tested": False,
                    "notes": "Node stdio server; requires Autodesk APS/ACC credentials",
                },
            }
        ),
        "approval_gates": CLOUD_GATES,
        "validation_result": validation_summary(
            "dependency_missing",
            "Clean Intel Ubuntu validation cloned aps-mcp-server-nodejs at 722591abb08c42000e9aedcabc746bbd7f413739, ran `npm install` successfully, found no npm test script, and confirmed no-credential startup exits with the expected diagnostic: missing APS_CLIENT_ID, APS_CLIENT_SECRET, SSA_ID, SSA_KEY_ID, and SSA_KEY_PATH. With dummy APS variables and a generated dummy RSA key, MCP initialized as `aps-mcp-server-nodejs` 0.0.1, listed 4 tools, and `getProjectsTool` reached APS auth and returned AUTH-001 for the dummy client.",
            "ubuntu-linux-x64-container",
            [
                "APS_CLIENT_ID",
                "APS_CLIENT_SECRET",
                "SSA_ID",
                "SSA_KEY_ID",
                "SSA_KEY_PATH",
            ],
        ),
    },
    "autodesk-aps-petrbroz": {
        "verification_state": "community_mcp",
        "installability_tier": "blocked",
        "risk_level": "medium",
        "deployment_mode": "cloud-saas",
        "credentials_required": [
            "APS_CLIENT_ID",
            "APS_CLIENT_SECRET",
            "APS_SA_ID",
            "APS_SA_EMAIL",
            "APS_SA_KEY_ID",
            "APS_SA_PRIVATE_KEY",
        ],
        "platform_support": platform_support(
            {
                "windows_11_x64": {
                    "status": "likely",
                    "tested": False,
                    "notes": "superseded by official Autodesk repo",
                },
                "linux_x64": {
                    "status": "host-dependent",
                    "tested": True,
                    "notes": "build succeeded and missing-credential diagnostic was clear, but README says project moved to official repo",
                },
                "linux_arm64": {
                    "status": "unknown",
                    "tested": False,
                    "notes": "not tested; use official Autodesk repo instead",
                },
                "macos_x64": {
                    "status": "likely",
                    "tested": False,
                    "notes": "superseded by official Autodesk repo",
                },
                "macos_arm64": {
                    "status": "likely",
                    "tested": False,
                    "notes": "superseded by official Autodesk repo",
                },
            }
        ),
        "approval_gates": CLOUD_GATES,
        "validation_result": validation_summary(
            "blocked",
            "Clean Intel Ubuntu validation cloned commit 557556235e806a5d74265fcf556b9dae4206abdd, installed yarn 1.22.22, ran `yarn install --frozen-lockfile` and `yarn run build` successfully, and confirmed there is no `yarn test` script. Without credentials, `node build/server.js` exits with the expected missing-variable diagnostic for APS_CLIENT_ID, APS_CLIENT_SECRET, APS_SA_ID, APS_SA_EMAIL, APS_SA_KEY_ID, and APS_SA_PRIVATE_KEY. With dummy APS variables and a generated base64 RSA private key, MCP initialized as `autodesk-platform-services` 0.0.1, listed 8 tools, and `get-accounts` reached Autodesk auth and returned AUTH-001 for the dummy client. The repository README states the project moved to the official Autodesk APS MCP server, so use `autodesk-aps-official` instead.",
            "ubuntu-linux-x64-container",
            [
                "APS_CLIENT_ID",
                "APS_CLIENT_SECRET",
                "APS_SA_ID",
                "APS_SA_EMAIL",
                "APS_SA_KEY_ID",
                "APS_SA_PRIVATE_KEY",
            ],
        ),
        "install_blocked_reason": "Repository README says this project moved to https://github.com/autodesk-platform-services/aps-mcp-server-nodejs.",
    },
    "fusion360-mcp-faust": {
        "verification_state": "community_mcp",
        "installability_tier": "might_work",
        "risk_level": "high",
        "deployment_mode": "local-bridge",
        "host_software_required": ["Fusion 360 desktop", "Fusion360MCP add-in"],
        "platform_support": platform_support(
            {
                "windows_11_x64": {
                    "status": "host-dependent",
                    "tested": False,
                    "notes": "requires Fusion 360 desktop and the Fusion360MCP add-in",
                },
                "linux_x64": {
                    "status": "no",
                    "tested": True,
                    "notes": "clean Intel Ubuntu validation passed package tests/mock MCP, but socket mode correctly reported Fusion add-in unavailable",
                },
                "linux_arm64": {
                    "status": "no",
                    "tested": False,
                    "notes": "Fusion 360 desktop is not available for Linux ARM64",
                },
                "macos_x64": {
                    "status": "host-dependent",
                    "tested": False,
                    "notes": "requires Fusion 360 desktop and the Fusion360MCP add-in",
                },
                "macos_arm64": {
                    "status": "host-dependent",
                    "tested": False,
                    "notes": "requires Fusion 360 desktop and the Fusion360MCP add-in",
                },
            }
        ),
        "approval_gates": HIGH_RISK_GATES,
        "validation_result": validation_summary(
            "dependency_missing",
            "Clean Intel Ubuntu validation cloned fusion360-mcp-server at b44b667e440da070081795cfcbfaf75de2a44251 and passed 282 upstream tests. MCP mock mode initialized as `fusion360-mcp-server` 1.26.0, listed 85 tools, `ping` returned mock pong, and `create_box` with length/width/height returned mock deltas. Socket mode initialized and listed 85 tools, then `ping` returned the expected error that Fusion 360/add-in is not running.",
            "ubuntu-linux-x64-container",
            ["Fusion 360 desktop", "Fusion360MCP add-in"],
        ),
    },
    "autodesk-fusion-mcp-python": {
        "verification_state": "community_mcp",
        "installability_tier": "non_working",
        "risk_level": "high",
        "deployment_mode": "cloud-saas",
        "host_software_required": ["Fusion 360", "APS Design Automation activity"],
        "credentials_required": [
            "APS_CLIENT_ID",
            "APS_CLIENT_SECRET",
            "FUSION_ACTIVITY_ID",
        ],
        "platform_support": platform_support(
            {
                "windows_11_x64": {
                    "status": "host-dependent",
                    "tested": False,
                    "notes": "requires Fusion 360 and APS credentials; blocked by MCP auth helper bug before host validation",
                },
                "linux_x64": {
                    "status": "no",
                    "tested": True,
                    "notes": "clean Intel Ubuntu validation installed requirements and initialized MCP with dummy APS env, but generate_cube fails before APS auth due httpx BasicAuth.auth_header bug",
                },
                "linux_arm64": {
                    "status": "unknown",
                    "tested": False,
                    "notes": "not tested; blocked by MCP auth helper bug first",
                },
                "macos_x64": {
                    "status": "host-dependent",
                    "tested": False,
                    "notes": "requires Fusion 360 and APS credentials; blocked by MCP auth helper bug before host validation",
                },
                "macos_arm64": {
                    "status": "host-dependent",
                    "tested": False,
                    "notes": "requires Fusion 360 and APS credentials; blocked by MCP auth helper bug before host validation",
                },
            }
        ),
        "approval_gates": HIGH_RISK_GATES + CLOUD_GATES,
        "validation_result": validation_summary(
            "failed",
            "Clean Intel Ubuntu validation cloned sockcymbal/autodesk-fusion-mcp-python at a3398ac5c76baa252240f301167a4cba2fe6f5b8, found no upstream tests, and installed requirements.txt in a Python 3.12 virtual environment. The catalog command `python main.py` is stale; the actual MCP script is `python fusion_mcp.py`. Without APS env vars, startup exits with `KeyError: 'APS_CLIENT_ID'`. With dummy APS_CLIENT_ID, APS_CLIENT_SECRET, and FUSION_ACTIVITY_ID, MCP initialized as `fusion` 1.28.1 and listed one tool, `generate_cube`, but the tool failed before any APS request with `'BasicAuth' object has no attribute 'auth_header'` from `httpx.BasicAuth(CLIENT_ID, CLIENT_SECRET).auth_header`.",
            "ubuntu-linux-x64-container",
            ["Fusion 360", "APS_CLIENT_ID", "APS_CLIENT_SECRET", "FUSION_ACTIVITY_ID"],
        ),
        "follow_up_url": "docs/mcp-catalog/followups/autodesk-fusion-mcp-python.md",
        "install_blocked_reason": "MCP backend call fails before APS/Fusion validation because the upstream auth helper uses a removed/invalid httpx BasicAuth.auth_header attribute.",
        "headless_ok": "no",
    },
    "revit-mcp-servers": {
        "verification_state": "community_mcp",
        "installability_tier": "might_work",
        "risk_level": "high",
        "deployment_mode": "local-bridge",
        "host_software_required": ["Revit", "revit-mcp-plugin", "Windows"],
        "platform_support": platform_support(
            {
                "windows_11_x64": {
                    "status": "host-dependent",
                    "tested": False,
                    "notes": "requires Revit desktop plus the revit-mcp-plugin socket service",
                },
                "linux_x64": {
                    "status": "no",
                    "tested": True,
                    "notes": "clean Intel Ubuntu validation built the Node MCP server, listed 25 tools, and got the expected Revit plugin connection failure",
                },
                "linux_arm64": {
                    "status": "no",
                    "tested": False,
                    "notes": "Revit desktop is not available for Linux ARM64",
                },
                "macos_x64": {
                    "status": "no",
                    "tested": False,
                    "notes": "Revit desktop is Windows-only",
                },
                "macos_arm64": {
                    "status": "no",
                    "tested": False,
                    "notes": "Revit desktop is Windows-only",
                },
            }
        ),
        "approval_gates": HIGH_RISK_GATES,
        "validation_result": validation_summary(
            "dependency_missing",
            "Clean Intel Ubuntu validation cloned commit c9ef49e4c397298d291304f822b89ba3a102e6bf, installed Node 18/npm plus build-essential after better-sqlite3 required make/native compilation, built the TypeScript server, and found no upstream test script. MCP initialized as revit-mcp 1.0.0, listed 25 tools, and `say_hello` plus `get_current_view_info` both returned the expected backend diagnostic `connect to revit client failed` with ECONNREFUSED ::1:8080 because Revit desktop and the revit-mcp-plugin socket are unavailable in the Linux container.",
            "ubuntu-linux-x64-container",
            ["Revit", "revit-mcp-plugin"],
        ),
    },
    "cad-mcp-daobataotie": {
        "verification_state": "community_mcp",
        "installability_tier": "might_work",
        "risk_level": "high",
        "deployment_mode": "local-bridge",
        "host_software_required": [
            "Windows",
            "pywin32",
            "AutoCAD",
            "GstarCAD",
            "ZWCAD",
        ],
        "platform_support": platform_support(
            {
                "windows_11_x64": {
                    "status": "host-dependent",
                    "tested": False,
                    "notes": "README requires Windows plus AutoCAD, GstarCAD, or ZWCAD through COM",
                },
                "linux_x64": {
                    "status": "no",
                    "tested": True,
                    "notes": "clean Intel Ubuntu validation cloned repo, but `pip install -r requirements.txt` cannot satisfy Windows-only `pywin32` and startup fails importing `win32com`",
                },
                "linux_arm64": {
                    "status": "no",
                    "tested": False,
                    "notes": "Windows COM dependency is not available on Linux ARM64",
                },
                "macos_x64": {
                    "status": "no",
                    "tested": False,
                    "notes": "Windows COM dependency is not available on macOS",
                },
                "macos_arm64": {
                    "status": "no",
                    "tested": False,
                    "notes": "Windows COM dependency is not available on macOS",
                },
            }
        ),
        "approval_gates": HIGH_RISK_GATES,
        "validation_result": validation_summary(
            "dependency_missing",
            "Clean Intel Ubuntu validation cloned CAD-MCP at 352541820a56823568a90993dd773e7014205f44, found no upstream tests, and confirmed the README command is `python src/server.py` with Windows plus AutoCAD/GstarCAD/ZWCAD requirements. Installing `requirements.txt` with Python 3.12 failed because `pywin32>=228` has no Linux distribution. After installing only `mcp`, `pydantic`, and `typing`, `python src/server.py` exited before MCP initialization with `ModuleNotFoundError: No module named 'win32com'` from `src/cad_controller.py`, so full validation requires Windows, pywin32, and a supported CAD COM host.",
            "ubuntu-linux-x64-container",
            ["Windows COM", "pywin32", "AutoCAD/GstarCAD/ZWCAD"],
        ),
        "headless_ok": "no",
    },
    "calculix-simulation": {
        "verification_state": "capability_alias",
        "installability_tier": "blocked",
        "risk_level": "medium",
        "deployment_mode": "unknown",
        "host_software_required": ["CalculiX", "FreeCAD FEM or standalone wrapper TBD"],
        "platform_support": platform_support(
            {
                "windows_11_x64": {
                    "status": "unknown",
                    "tested": False,
                    "notes": "no verified standalone MCP source; may be a FreeCAD FEM capability",
                },
                "linux_x64": {
                    "status": "unknown",
                    "tested": True,
                    "notes": "clean Intel Ubuntu validation could not clone the configured repo and `calculix-mcp` was not found in the package registry",
                },
                "linux_arm64": {
                    "status": "unknown",
                    "tested": False,
                    "notes": "blocked until a verified standalone MCP source exists",
                },
                "macos_x64": {
                    "status": "unknown",
                    "tested": False,
                    "notes": "blocked until a verified standalone MCP source exists",
                },
                "macos_arm64": {
                    "status": "unknown",
                    "tested": False,
                    "notes": "blocked until a verified standalone MCP source exists",
                },
            }
        ),
        "validation_result": validation_summary(
            "blocked",
            "Clean Intel Ubuntu validation found no installable standalone CalculiX MCP: `git clone https://github.com/calculix/calculix-mcp` failed with a credential prompt and `uv tool run calculix-mcp --help` reported the package was not found. The research handoff models this as a FreeCAD FEM capability alias or wrapper candidate until a real MCP source is verified.",
            "ubuntu-linux-x64-container",
        ),
        "install_blocked_reason": "No verified standalone CalculiX MCP source/package; track as a FreeCAD FEM capability alias or wrapper candidate.",
    },
    "easy-mcp-autocad": {
        "verification_state": "community_mcp",
        "installability_tier": "might_work",
        "risk_level": "high",
        "deployment_mode": "local-bridge",
        "host_software_required": [
            "Windows",
            "AutoCAD 2018+",
            "pywin32",
            "COM interface",
        ],
        "platform_support": platform_support(
            {
                "windows_11_x64": {
                    "status": "host-dependent",
                    "tested": False,
                    "notes": "README requires Windows and AutoCAD 2018+ with COM support",
                },
                "linux_x64": {
                    "status": "no",
                    "tested": True,
                    "notes": "clean Intel Ubuntu validation cloned repo, but dependency installation cannot satisfy Windows-only `pywin32`",
                },
                "linux_arm64": {
                    "status": "no",
                    "tested": False,
                    "notes": "Windows COM dependency is not available on Linux ARM64",
                },
                "macos_x64": {
                    "status": "no",
                    "tested": False,
                    "notes": "Windows COM dependency is not available on macOS",
                },
                "macos_arm64": {
                    "status": "no",
                    "tested": False,
                    "notes": "Windows COM dependency is not available on macOS",
                },
            }
        ),
        "approval_gates": HIGH_RISK_GATES,
        "validation_result": validation_summary(
            "dependency_missing",
            "Clean Intel Ubuntu validation cloned Easy-MCP-AutoCAD at 332215b91e976c1738dfd3940e9f9770c0fd5856 and confirmed the README requires Windows plus AutoCAD 2018+ COM support. `pip install -r requirements.txt` failed because `pywin32` has no Linux wheels, `uv pip install -e .` on Python 3.13 failed because `pywin32>=309` only has Windows wheels, and direct `python server.py` after installing non-Windows dependencies failed at module import with `ModuleNotFoundError: No module named 'win32com'`. MCP startup cannot be tested in the Ubuntu container.",
            "ubuntu-linux-x64-container",
            ["Windows COM", "pywin32", "AutoCAD 2018+"],
        ),
        "headless_ok": "no",
    },
    "freecad-booleans-lucygoodchild": {
        "verification_state": "community_mcp",
        "installability_tier": "tested",
        "risk_level": "high",
        "deployment_mode": "local-bridge",
        "host_software_required": ["FreeCAD"],
        "platform_support": platform_support(
            {
                "windows_11_x64": {
                    "status": "host-dependent",
                    "tested": False,
                    "notes": "requires FreeCAD and Node.js; not tested on Windows",
                },
                "linux_x64": {
                    "status": "yes",
                    "tested": True,
                    "notes": "clean Intel Ubuntu validation built the TypeScript MCP server, installed FreeCAD 1.1.1 AppImage, created a box, and listed FreeCAD objects",
                },
                "linux_arm64": {
                    "status": "unknown",
                    "tested": False,
                    "notes": "not tested; FreeCAD backend availability must be checked",
                },
                "macos_x64": {
                    "status": "host-dependent",
                    "tested": False,
                    "notes": "requires FreeCAD and Node.js; not tested on macOS",
                },
                "macos_arm64": {
                    "status": "host-dependent",
                    "tested": False,
                    "notes": "requires FreeCAD and Node.js; not tested on macOS ARM64",
                },
            }
        ),
        "approval_gates": HIGH_RISK_GATES,
        "validation_result": validation_summary(
            "passed",
            "Clean Intel Ubuntu validation passed with caveat: cloned lucygoodchild/freecad-mcp-server at 21636a406f8fd77d99ba1b679282e0995b879202, ran `npm install` and `npm run build`, installed FreeCAD 1.1.1 AppImage as `/usr/bin/freecadcmd`, initialized MCP, listed 7 tools, `create_box` created `WrightBox`, and `list_objects` reported FreeCAD Part boxes. The server also writes operational log lines to stdout during tool calls, which is a stdio protocol risk for strict clients.",
            "ubuntu-linux-x64-container",
        ),
        "headless_ok": "yes",
    },
    "freecad-robust-spkane": {
        "verification_state": "community_mcp",
        "installability_tier": "tested",
        "risk_level": "high",
        "deployment_mode": "local-bridge",
        "host_software_required": ["FreeCAD", "Robust MCP Bridge", "Python", "uv"],
        "platform_support": platform_support(
            {
                "windows_11_x64": {
                    "status": "host-dependent",
                    "tested": False,
                    "notes": "requires FreeCAD desktop plus the Robust MCP Bridge; not tested on Windows",
                },
                "linux_x64": {
                    "status": "yes",
                    "tested": True,
                    "notes": "clean Intel Ubuntu validation installed FreeCAD 1.1.1 AppImage, started the Robust MCP Bridge with freecadcmd, and created/read back a Part::Box through XML-RPC mode",
                },
                "linux_arm64": {
                    "status": "unknown",
                    "tested": False,
                    "notes": "not tested; FreeCAD backend, AppImage, and Python package support must be checked",
                },
                "macos_x64": {
                    "status": "host-dependent",
                    "tested": False,
                    "notes": "requires FreeCAD desktop plus the Robust MCP Bridge; use XML-RPC/socket mode rather than embedded mode",
                },
                "macos_arm64": {
                    "status": "host-dependent",
                    "tested": False,
                    "notes": "requires FreeCAD desktop plus the Robust MCP Bridge; use XML-RPC/socket mode rather than embedded mode",
                },
            }
        ),
        "approval_gates": HIGH_RISK_GATES,
        "validation_result": validation_summary(
            "passed",
            "Clean Intel Ubuntu validation passed: cloned spkane/freecad-addon-robust-mcp-server at d9a37118a8331e8739ad45fd97d027437984296f, installed source package `freecad-robust-mcp` version `0.1.dev1+gd9a37118a`, and upstream unit tests passed with 420 tests. Ubuntu apt had no `freecad` package candidate, so validation installed FreeCAD 1.1.1 revision 20260414 from the Linux x86_64 AppImage. The Robust MCP Bridge started headless under `freecadcmd` on XML-RPC port 9875; `freecad-mcp --check` reported `Connection successful`; MCP serverInfo was `freecad-mcp` version 1.28.1 and listed 152 tools. `get_connection_status` returned connected true; `get_freecad_version` returned FreeCAD 1.1.1 build `20260414 (Git shallow)`; backend operations created `WrightDoc`, created `WrightBox` as `Part::Box` with volume 480.0, and `list_objects` reported `WrightBox`.",
            "ubuntu-linux-x64-container",
        ),
        "headless_ok": "yes",
    },
    "freecad-core-nekanat": {
        "verification_state": "community_mcp",
        "installability_tier": "tested",
        "risk_level": "high",
        "deployment_mode": "local-bridge",
        "host_software_required": ["FreeCAD", "Python", "uv"],
        "platform_support": platform_support(
            {
                "windows_11_x64": {
                    "status": "host-dependent",
                    "tested": False,
                    "notes": "requires FreeCAD desktop plus the FreeCADMCP addon; not tested on Windows",
                },
                "linux_x64": {
                    "status": "yes",
                    "tested": True,
                    "notes": "clean Intel Ubuntu validation installed FreeCAD 1.1.1 AppImage, Xvfb, and the FreeCADMCP addon; MCP created and read back a Part::Box",
                },
                "linux_arm64": {
                    "status": "unknown",
                    "tested": False,
                    "notes": "not tested; FreeCAD backend and Python package support must be checked",
                },
                "macos_x64": {
                    "status": "host-dependent",
                    "tested": False,
                    "notes": "requires FreeCAD desktop plus the FreeCADMCP addon; not tested on macOS",
                },
                "macos_arm64": {
                    "status": "host-dependent",
                    "tested": False,
                    "notes": "requires FreeCAD desktop plus the FreeCADMCP addon; not tested on macOS ARM64",
                },
            }
        ),
        "approval_gates": HIGH_RISK_GATES,
        "validation_result": validation_summary(
            "passed",
            "Clean Intel Ubuntu validation passed: cloned neka-nat/freecad-mcp at 63acb305573194a011641ab13ccfb391fe95769f; package `freecad-mcp` version 0.1.18 exposes console script `freecad-mcp`; no upstream tests were present. `uv tool run --from /tmp/freecad-nekanat-src freecad-mcp --help` built and installed the source package and showed `--only-text-feedback` and `--host`. Ubuntu apt had no `freecad` package candidate, so validation installed FreeCAD 1.1.1 revision 20260414 from the Linux x86_64 AppImage, copied `addon/FreeCADMCP` into FreeCAD user Mod paths, wrote localhost-only `freecad_mcp_settings.json` with `auto_start_rpc: true`, and launched FreeCAD under Xvfb. MCP stdio initialized as serverInfo `FreeCADMCP` version 1.28.1 and listed 14 tools. `list_documents` returned `[]`; backend operations passed: `create_document` created `WrightDoc`, `create_object` created `WrightBox` as `Part::Box`, and `get_objects` reported `WrightBox` with volume 480.0.",
            "ubuntu-linux-x64-container",
        ),
        "headless_ok": "yes",
    },
    "jarvis-onshape-mcp": {
        "verification_state": "community_mcp",
        "installability_tier": "might_work",
        "risk_level": "medium",
        "deployment_mode": "cloud-saas",
        "credentials_required": ["ONSHAPE_API_KEY", "ONSHAPE_API_SECRET"],
        "platform_support": platform_support(
            {
                "windows_11_x64": {
                    "status": "likely",
                    "tested": False,
                    "notes": "Python/uv stdio MCP expected; not tested on Windows",
                },
                "linux_x64": {
                    "status": "yes",
                    "tested": True,
                    "notes": "clean Intel Ubuntu validation installed from source, passed upstream tests, initialized MCP, listed tools, and returned clear Onshape 401 diagnostics with dummy credentials",
                },
                "linux_arm64": {
                    "status": "unknown",
                    "tested": False,
                    "notes": "not tested; Python dependencies and cloud API access must be checked",
                },
                "macos_x64": {
                    "status": "likely",
                    "tested": False,
                    "notes": "Python/uv stdio MCP expected; not tested on macOS",
                },
                "macos_arm64": {
                    "status": "likely",
                    "tested": False,
                    "notes": "Python/uv stdio MCP expected; not tested on macOS ARM64",
                },
            }
        ),
        "approval_gates": CLOUD_GATES,
        "validation_result": validation_summary(
            "dependency_missing",
            "Clean Intel Ubuntu validation cloned Jarvis Onshape MCP at b0e725852280ebcfda5d46a4f2ed2d0b720beace, installed dependencies with `uv sync --extra dev`, and upstream tests passed 698/698 with 3 Pydantic deprecation warnings. MCP initialized as `onshape-mcp` 1.17.0 from package `onshape-mcp` 1.2.0, listed 69 tools, `list_cached_images` returned the expected no-images-cached message, `list_documents` reached `https://cad.onshape.com/api/v6/documents` and returned `API returned 401` with dummy credentials, and `create_document` reached `https://cad.onshape.com/api/v10/documents` and returned `Unauthenticated API request`. Full validation requires real Onshape API credentials.",
            "ubuntu-linux-x64-container",
            ["ONSHAPE_API_KEY", "ONSHAPE_API_SECRET"],
        ),
        "headless_ok": "yes",
    },
    "siemens-element-mcp": {
        "verification_state": "verified_docs_mcp",
        "installability_tier": "might_work",
        "risk_level": "read-only",
        "deployment_mode": "local-cloud",
        "platform_support": platform_support(
            {
                "windows_11_x64": {
                    "status": "likely",
                    "tested": False,
                    "notes": "npm package is cross-platform; Windows still needs a configured Siemens LLM token or keychain setup",
                },
                "linux_x64": {
                    "status": "yes",
                    "tested": True,
                    "notes": "clean Intel Ubuntu validation installed the npm package in a project, started stdio MCP, listed tools, and reached the Siemens embeddings credential boundary",
                },
                "linux_arm64": {
                    "status": "likely",
                    "tested": False,
                    "notes": "package declares Linux ARM64 LanceDB optional dependency; not tested",
                },
                "macos_x64": {
                    "status": "likely",
                    "tested": False,
                    "notes": "package declares macOS x64 LanceDB optional dependency; not tested",
                },
                "macos_arm64": {
                    "status": "likely",
                    "tested": False,
                    "notes": "package declares macOS ARM64 LanceDB optional dependency; not tested",
                },
            }
        ),
        "credentials_required": ["OPENAI_API_KEY"],
        "approval_gates": CLOUD_GATES,
        "validation_result": validation_summary(
            "dependency_missing",
            "Clean Intel Ubuntu validation installed npm package @siemens/element-mcp version 49.12.0-v.1.11.1 from https://registry.npmjs.org/@siemens/element-mcp/-/element-mcp-49.12.0-v.1.11.1.tgz; the package metadata points to https://code.siemens.com/ux/sdl-mcp but no public commit hash is included in the npm artifact. There is no upstream test script in the package. A fresh `npx -y @siemens/element-mcp` failed before local install with `element-mcp: not found`, but the documented project-install flow worked: `npm install --save-dev --save-exact @siemens/element-mcp@49.12.0-v.1.11.1`, then `npx @siemens/element-mcp` or `npx element-mcp`. MCP initialized as @siemens/element-mcp 1.0.0, listed 2 tools (`element-search`, `element-icon-search`), and both tools reached the backend credential boundary with `Embedding API error: 403 Forbidden`; `element-mcp check` also reported `LLM token not found. Run 'element-mcp setup-token'`. Full validation requires a Siemens LLM token with llm scope.",
            "ubuntu-linux-x64-container",
            ["OPENAI_API_KEY"],
        ),
        "headless_ok": "yes",
    },
    "siemens-wincc-unified": {
        "verification_state": "user_reported_url_needed",
        "installability_tier": "blocked",
        "risk_level": "safety-critical",
        "deployment_mode": "local-bridge",
        "host_software_required": [
            "Windows",
            "WinCC Unified PC Runtime",
            "Siemens support package 110002407",
        ],
        "platform_support": platform_support(
            {
                "windows_11_x64": {
                    "status": "host-dependent",
                    "tested": False,
                    "notes": "official artifact appears to require Siemens Support login plus WinCC Unified PC Runtime",
                },
                "linux_x64": {
                    "status": "no",
                    "tested": True,
                    "notes": "clean Intel Ubuntu validation could not access the Siemens support artifact, found no npm/PyPI package, and the configured .exe command is unavailable",
                },
                "linux_arm64": {
                    "status": "no",
                    "tested": False,
                    "notes": "official entry appears Windows/WinCC-host dependent",
                },
                "macos_x64": {
                    "status": "no",
                    "tested": False,
                    "notes": "official entry appears Windows/WinCC-host dependent",
                },
                "macos_arm64": {
                    "status": "no",
                    "tested": False,
                    "notes": "official entry appears Windows/WinCC-host dependent",
                },
            }
        ),
        "approval_gates": CLOUD_GATES
        + MACHINE_CONTROL_GATES
        + ["safety_review_approval"],
        "validation_result": validation_summary(
            "blocked",
            "Clean Intel Ubuntu validation checked Siemens Support Entry ID 110002407. Public search results confirm `Integration of MCP Server with WinCC Unified PC Runtime` and show a login-required `110002407_MCPServerPCRuntime_READMEOSS.zip`; direct curl requests to the support page and PDF attachment returned HTTP 403 from Akamai. `npm view wincc-unified-mcp`, `npm view @siemens/wincc-unified-mcp`, `pip index versions wincc-unified-mcp`, and `pip index versions wincc_unified_mcp` found no package. The configured `wincc-unified-mcp.exe` command was not present in Linux, and guessed Siemens GitHub repository URLs required authentication or did not resolve publicly. No MCP stdio calls could be made until the official support artifact is obtained and installed on a Windows host with WinCC Unified PC Runtime.",
            "ubuntu-linux-x64-container",
            [
                "Windows",
                "WinCC Unified PC Runtime",
                "Siemens Support login",
                "110002407_MCPServerPCRuntime_READMEOSS.zip",
            ],
        ),
        "follow_up_url": "docs/mcp-catalog/followups/wincc-unified-mcp.md",
        "install_blocked_reason": "Official Siemens support artifact for Entry ID 110002407 is login-gated and no public npm/PyPI/GitHub package or Linux command could be verified.",
        "headless_ok": "no",
    },
    "ptc-thingworx-mcp": {
        "verification_state": "verified_mcp",
        "installability_tier": "might_work",
        "risk_level": "safety-critical",
        "deployment_mode": "cloud-saas",
        "host_software_required": ["ThingWorx 10.1+ MCP-enabled server"],
        "credentials_required": [
            "THINGWORX_BASE_URL",
            "THINGWORX_APP_KEY or THINGWORX_OAUTH_TOKEN",
        ],
        "platform_support": platform_support(
            {
                "windows_11_x64": {
                    "status": "host-dependent",
                    "tested": False,
                    "notes": "client-side HTTP/SSE configuration should work once a ThingWorx 10.1+ MCP endpoint and credentials are available",
                },
                "linux_x64": {
                    "status": "host-dependent",
                    "tested": True,
                    "notes": "clean Intel Ubuntu validation confirmed official PTC MCP docs are reachable, but no live ThingWorx endpoint or credentials were available for MCP calls",
                },
                "linux_arm64": {
                    "status": "host-dependent",
                    "tested": False,
                    "notes": "remote HTTP/SSE endpoint should be client-architecture independent; not tested",
                },
                "macos_x64": {
                    "status": "host-dependent",
                    "tested": False,
                    "notes": "remote HTTP/SSE endpoint should be client-architecture independent; not tested",
                },
                "macos_arm64": {
                    "status": "host-dependent",
                    "tested": False,
                    "notes": "remote HTTP/SSE endpoint should be client-architecture independent; not tested",
                },
            }
        ),
        "approval_gates": CLOUD_GATES
        + MACHINE_CONTROL_GATES
        + ["safety_review_approval"],
        "validation_result": validation_summary(
            "dependency_missing",
            "Clean Intel Ubuntu validation confirmed official PTC ThingWorx 10.1 MCP documentation pages returned HTTP 200. PTC docs describe setting an MCP client to HTTP/SSE endpoint `<ThingWorx Server URL>/mcp`, managing tools/resources/prompts with the `MCPServices` resource, and OAuth-protected metadata; therefore the catalog command was corrected from the nonexistent local `ptc-thingworx-mcp` binary to `${THINGWORX_BASE_URL}/mcp`. No standalone npm/PyPI package was found: `npm view ptc-thingworx-mcp`, `npm view thingworx-mcp`, `npm view @ptc/thingworx-mcp`, `pip index versions ptc-thingworx-mcp`, and `pip index versions thingworx-mcp` all failed. The configured `ptc-thingworx-mcp` command was not present in Linux. A separate community repository `https://github.com/doubleSlashde/thingworx-mcp-server` exists at commit 7e22ef9be1af495acf1a46101ebb17380eed86ae, but it is not the official PTC product-hosted MCP entry. No MCP calls could be made without a live ThingWorx 10.1+ MCP endpoint and credentials.",
            "ubuntu-linux-x64-container",
            [
                "ThingWorx 10.1+ MCP-enabled server",
                "THINGWORX_BASE_URL",
                "THINGWORX_APP_KEY or THINGWORX_OAUTH_TOKEN",
            ],
        ),
        "headless_ok": "yes",
    },
    "kicad-mcp-lamaalrajih": {
        "verification_state": "community_mcp",
        "installability_tier": "non_working",
        "risk_level": "medium",
        "deployment_mode": "local-bridge",
        "host_software_required": ["KiCad", "Python", "uv"],
        "platform_support": platform_support(
            {
                "windows_11_x64": {
                    "status": "host-dependent",
                    "tested": False,
                    "notes": "requires KiCad 9.0+; MCP schema issue must be fixed before full validation",
                },
                "linux_x64": {
                    "status": "no",
                    "tested": True,
                    "notes": "clean Intel Ubuntu validation initialized MCP and project discovery worked, but 11 of 16 tools expose required `ctx` arguments and cannot be called by a normal MCP client",
                },
                "linux_arm64": {
                    "status": "unknown",
                    "tested": False,
                    "notes": "not tested; blocked by MCP schema issue before ARM64/backend validation",
                },
                "macos_x64": {
                    "status": "host-dependent",
                    "tested": False,
                    "notes": "requires KiCad 9.0+; MCP schema issue must be fixed before full validation",
                },
                "macos_arm64": {
                    "status": "host-dependent",
                    "tested": False,
                    "notes": "requires KiCad 9.0+; MCP schema issue must be fixed before full validation",
                },
            }
        ),
        "validation_result": validation_summary(
            "failed",
            "Clean Intel Ubuntu validation found the GitHub package command starts MCP and read-only project discovery works, but the README/catalog `python main.py` launch path fails with `ValueError: a coroutine was expected, got None`. MCP initialized as `KiCad` 1.11.0, listed 16 tools, `list_projects` and `get_project_structure` worked against a sample `WrightBoard` project, but 11 of 16 tools expose a required `ctx` input; `run_drc_check` failed before backend execution with `Input validation error: 'ctx' is a required property`. Upstream functional tests passed only with coverage disabled: 37 passed, 2 skipped; the default test command failed its 80% coverage gate at 10.04%. Ubuntu 24.04 default apt only offers KiCad 7.0.11 while upstream requires KiCad 9.0+.",
            "ubuntu-linux-x64-container",
            ["KiCad 9.0+"],
        ),
        "follow_up_url": "docs/mcp-catalog/followups/kicad-mcp-lamaalrajih.md",
        "install_blocked_reason": "Most advertised tools require a `ctx` argument in the MCP input schema and fail normal client validation; see follow-up record.",
    },
    "rosbag-mcp-binabik": {
        "verification_state": "community_mcp",
        "installability_tier": "tested",
        "risk_level": "low",
        "deployment_mode": "local-only",
        "host_software_required": [],
        "platform_support": platform_support(
            {
                "windows_11_x64": {
                    "status": "unknown",
                    "tested": False,
                    "notes": "not tested; Python rosbags stack may work, but path handling must be checked",
                },
                "linux_x64": {
                    "status": "yes",
                    "tested": True,
                    "notes": "clean Intel Ubuntu validation passed with source run and `rosbags==0.10.10`; listed bags, read bag info, and retrieved a message from a generated ROS 2 bag",
                },
                "linux_arm64": {
                    "status": "unknown",
                    "tested": False,
                    "notes": "not tested; Python wheels for rosbags/numpy/plotly stack must be checked",
                },
                "macos_x64": {
                    "status": "likely",
                    "tested": False,
                    "notes": "not tested; Python rosbags stack expected but dependency pin must be applied",
                },
                "macos_arm64": {
                    "status": "likely",
                    "tested": False,
                    "notes": "not tested; Python rosbags stack expected but dependency pin must be applied",
                },
            }
        ),
        "approval_gates": ["workspace_read_approval"],
        "validation_result": validation_summary(
            "passed",
            "Clean Intel Ubuntu validation passed with caveat: cloned binabik-ai/mcp-rosbags at 9b6b3b7a7b10d2ef004c1b50d38395d07e0b47b6, installed `requirements.txt`, then pinned `rosbags==0.10.10` because the current unpinned rosbags release no longer exports `deserialize_cdr`. The source command `python src/server.py` initialized MCP serverInfo `rosbag-memory` 1.28.1, listed 15 tools, discovered generated ROS 2 bag `wright_chatter`, `bag_info` reported `/chatter` with 2 messages over 1 second, and `get_message_at_time` returned `std_msgs/msg/String` data `hello`.",
            "ubuntu-linux-x64-container",
        ),
        "headless_ok": "yes",
    },
    "oasis-open-fem-agent": {
        "verification_state": "community_mcp",
        "installability_tier": "tested",
        "risk_level": "high",
        "deployment_mode": "local-only",
        "host_software_required": [
            "Python",
            "scikit-fem for validated smoke tests",
            "optional FEniCSx/NGSolve/deal.II/Kratos/DUNE-fem/4C/FEBio backends",
        ],
        "platform_support": platform_support(
            {
                "windows_11_x64": {
                    "status": "unknown",
                    "tested": False,
                    "notes": "not tested; Python package should install, but solver backend support must be checked per backend",
                },
                "linux_x64": {
                    "status": "yes",
                    "tested": True,
                    "notes": "clean Intel Ubuntu validation passed with source install plus scikit-fem backend; other solver backends reported clear not-installed diagnostics",
                },
                "linux_arm64": {
                    "status": "unknown",
                    "tested": False,
                    "notes": "not tested; Python wheels and solver backend availability must be checked",
                },
                "macos_x64": {
                    "status": "likely",
                    "tested": False,
                    "notes": "not tested; Python package expected, solver backend support must be checked per backend",
                },
                "macos_arm64": {
                    "status": "unknown",
                    "tested": False,
                    "notes": "not tested; Python wheels and solver backend availability must be checked",
                },
            }
        ),
        "approval_gates": ["workspace_write_approval", "execute_code_approval"],
        "validation_result": validation_summary(
            "passed",
            "Clean Intel Ubuntu validation passed: cloned Hereon-InstituteMS/OASiS at 117c35769c0eb00181db003e8dcdc305546b08b7, installed `pip install -e .`, initialized MCP serverInfo `OASiS` 1.28.1, listed 15 tools, and `discover` returned clear not-installed diagnostics for optional solver backends. After installing only `scikit-fem==12.0.2`, `discover` reported `skfem` available, `prepare_simulation` returned Poisson knowledge/pitfalls, `run_simulation` completed a scikit-fem Poisson solve in 0.46s, wrote `result.vtu`, and upstream `tests/test_mcp_stdio.py` passed 5/5.",
            "ubuntu-linux-x64-container",
        ),
        "headless_ok": "yes",
    },
    "solidworks-api-docs": {
        "verification_state": "community_mcp",
        "installability_tier": "tested",
        "risk_level": "read-only",
        "deployment_mode": "local-only",
        "host_software_required": ["Bun", "local SolidWorks API documentation corpus"],
        "platform_support": platform_support(
            {
                "windows_11_x64": {
                    "status": "likely",
                    "tested": False,
                    "notes": "Bun/TypeScript docs server expected; not tested on Windows",
                },
                "linux_x64": {
                    "status": "yes",
                    "tested": True,
                    "notes": "clean Intel Ubuntu validation passed with Bun 1.3.14 and local documentation corpus; no SolidWorks desktop required",
                },
                "linux_arm64": {
                    "status": "unknown",
                    "tested": False,
                    "notes": "not tested; Bun and corpus access must be checked",
                },
                "macos_x64": {
                    "status": "likely",
                    "tested": False,
                    "notes": "Bun/TypeScript docs server expected; not tested on macOS",
                },
                "macos_arm64": {
                    "status": "likely",
                    "tested": False,
                    "notes": "Bun/TypeScript docs server expected; not tested on macOS ARM64",
                },
            }
        ),
        "approval_gates": ["workspace_read_approval"],
        "validation_result": validation_summary(
            "passed",
            "Clean Intel Ubuntu validation passed: cloned kilwizac/solidworks-api-mcp at f5a0ccf63337187695b3461cb750977be7d860f6, installed Bun 1.3.14 plus `unzip`, ran `bun install`, `bun run typecheck`, and `bun run test` with 40/40 tests passing. MCP initialized as `solidworks-mcp` 0.1.0, listed 6 tools, searched the local SolidWorks API corpus, listed 333 `ISldWorks` members, looked up `ISldWorks.OpenDoc6`, and returned OpenDoc6 examples.",
            "ubuntu-linux-x64-container",
        ),
        "headless_ok": "yes",
    },
    "onshape-mcp-hedless": {
        "verification_state": "community_mcp",
        "installability_tier": "might_work",
        "risk_level": "medium",
        "deployment_mode": "cloud-saas",
        "credentials_required": ["ONSHAPE_ACCESS_KEY", "ONSHAPE_SECRET_KEY"],
        "platform_support": platform_support(
            {
                "windows_11_x64": {
                    "status": "likely",
                    "tested": False,
                    "notes": "Python stdio MCP expected; not tested on Windows",
                },
                "linux_x64": {
                    "status": "yes",
                    "tested": True,
                    "notes": "clean Intel Ubuntu validation installed package, initialized MCP, listed tools, and returned clean missing-credential diagnostics",
                },
                "linux_arm64": {
                    "status": "unknown",
                    "tested": False,
                    "notes": "not tested; Python wheels and cloud API access must be checked",
                },
                "macos_x64": {
                    "status": "likely",
                    "tested": False,
                    "notes": "Python stdio MCP expected; not tested on macOS",
                },
                "macos_arm64": {
                    "status": "likely",
                    "tested": False,
                    "notes": "Python stdio MCP expected; not tested on macOS ARM64",
                },
            }
        ),
        "approval_gates": CLOUD_GATES,
        "validation_result": validation_summary(
            "dependency_missing",
            "Clean Intel Ubuntu validation installed onshape-mcp from commit 54d21ccc4a5376f692cddd01959305be01e40a53, initialized MCP serverInfo `onshape-mcp` 1.28.1, listed 45 tools, and an API-touching `list_documents` call without credentials returned `API returned 401. Please check your API credentials.` Upstream tests passed 497/497 with 86.28% coverage. Full cloud operation still requires Onshape API credentials.",
            "ubuntu-linux-x64-container",
            ["ONSHAPE_ACCESS_KEY", "ONSHAPE_SECRET_KEY"],
        ),
        "headless_ok": "yes",
    },
    "siemens-xcelerator-developer-portal-mcp": {
        "verification_state": "verified_docs_mcp",
        "installability_tier": "blocked",
        "risk_level": "read-only",
        "deployment_mode": "docs-only",
        "platform_support": platform_support(
            {
                key: {
                    "status": "likely",
                    "tested": False,
                    "notes": "docs/remote MCP expected once exact config URL is pinned",
                }
                for key in (
                    "windows_11_x64",
                    "linux_x64",
                    "linux_arm64",
                    "macos_x64",
                    "macos_arm64",
                )
            }
        ),
        "install_blocked_reason": "Exact client configuration URL still needs to be captured from Siemens docs.",
    },
    "autodesk-product-help-mcp": {
        "verification_state": "verified_docs_mcp",
        "installability_tier": "tested",
        "risk_level": "read-only",
        "deployment_mode": "remote-docs",
        "platform_support": platform_support(
            {
                key: {
                    "status": "yes",
                    "tested": key == "linux_x64",
                    "notes": "official Autodesk remote MCP endpoint; Wright Streamable HTTP runner initialized and listed tools",
                }
                for key in (
                    "windows_11_x64",
                    "linux_x64",
                    "linux_arm64",
                    "macos_x64",
                    "macos_arm64",
                )
            }
        ),
        "validation_result": validation_summary(
            "passed",
            "Verified against the official Autodesk Product Help remote MCP endpoint `https://developer.api.autodesk.com/knowledge/public/v1/mcp`; Wright initialized Streamable HTTP and listed `get_available_products` and `search_help_content`.",
            "ubuntu-linux-x64-container",
        ),
    },
    "webmcp-standard": {
        "verification_state": "ui_or_web_standard",
        "installability_tier": "blocked",
        "risk_level": "low",
        "deployment_mode": "unknown",
        "install_blocked_reason": "Tracked as a web-agent standard, not an engineering MCP server.",
    },
    "mcp-ui-shopify": {
        "verification_state": "ui_or_web_standard",
        "installability_tier": "blocked",
        "risk_level": "low",
        "deployment_mode": "unknown",
        "install_blocked_reason": "Tracked as UI infrastructure, not an engineering MCP server.",
    },
    "creo-parametric-mcp": {
        "verification_state": "community_mcp",
        "installability_tier": "might_work",
        "risk_level": "high",
        "deployment_mode": "local-bridge",
        "host_software_required": ["Creo", "CREOSON"],
        "credentials_required": [
            "VOLCENGINE_AUTHORIZATION",
            "VOLCENGINE_SERVICE_RESOURCE_ID",
        ],
        "platform_support": platform_support(
            {
                "windows_11_x64": {
                    "status": "host-dependent",
                    "tested": False,
                    "notes": "requires Creo desktop plus CREOSON for open_file_in_cad; local CadQuery generation should be retested on Windows",
                },
                "linux_x64": {
                    "status": "host-dependent",
                    "tested": True,
                    "notes": "clean Intel Ubuntu validation installed source package plus libgl1, generated a STEP file with CadQuery, and reached clear missing CREOSON/Volcengine boundaries",
                },
                "linux_arm64": {
                    "status": "unknown",
                    "tested": False,
                    "notes": "not tested; CadQuery/OCP wheels and host dependencies must be checked",
                },
                "macos_x64": {
                    "status": "host-dependent",
                    "tested": False,
                    "notes": "requires Creo desktop plus CREOSON for full operation",
                },
                "macos_arm64": {
                    "status": "host-dependent",
                    "tested": False,
                    "notes": "requires Creo desktop plus CREOSON and compatible CadQuery/OCP wheels",
                },
            }
        ),
        "approval_gates": HIGH_RISK_GATES + CLOUD_GATES,
        "validation_result": validation_summary(
            "dependency_missing",
            "Clean Intel Ubuntu validation cloned yangkunyi/creo-mcp at 1a2f164c88c896c0b98a8edec36a7dc4e2eb06ff, found no upstream tests, installed the source package with Python 3.12, and added `libgl1` after the first start failed with `ImportError: libGL.so.1`. MCP then initialized as `python-code-executor` 1.28.1, listed 3 tools, `execute_python_code` used CadQuery to export `/tmp/wright_creo_box.step` at 15418 bytes, `open_file_in_cad` returned the expected CREOSON connection-refused diagnostic for localhost:9056, and `retrieve_from_knowledge_base` with dummy credentials returned HTTP 400 from the Volcengine endpoint. Full validation requires Creo, CREOSON, and real Volcengine credentials.",
            "ubuntu-linux-x64-container",
            [
                "Creo",
                "CREOSON",
                "VOLCENGINE_AUTHORIZATION",
                "VOLCENGINE_SERVICE_RESOURCE_ID",
            ],
        ),
        "headless_ok": "partial",
    },
    "creopyson-creoson": {
        "verification_state": "capability_alias",
        "installability_tier": "blocked",
        "risk_level": "high",
        "deployment_mode": "local-bridge",
        "host_software_required": ["Creo", "JLINK", "pfcasync.jar", "Windows"],
        "platform_support": platform_support(
            {
                "windows_11_x64": {
                    "status": "host-dependent",
                    "tested": False,
                    "notes": "release is a Windows Creo/JLINK JSON bridge; requires Creo, JLINK, setvars.bat, and Windows DLL setup",
                },
                "linux_x64": {
                    "status": "no",
                    "tested": True,
                    "notes": "clean Intel Ubuntu validation downloaded the release and confirmed it is not an MCP server; startup fails without Creo/JLINK classes",
                },
                "linux_arm64": {
                    "status": "no",
                    "tested": False,
                    "notes": "release is Windows/Creo/JLINK host dependent and not an MCP server",
                },
                "macos_x64": {
                    "status": "no",
                    "tested": False,
                    "notes": "release is Windows/Creo/JLINK host dependent and not an MCP server",
                },
                "macos_arm64": {
                    "status": "no",
                    "tested": False,
                    "notes": "release is Windows/Creo/JLINK host dependent and not an MCP server",
                },
            }
        ),
        "approval_gates": HIGH_RISK_GATES,
        "validation_result": validation_summary(
            "blocked",
            "Clean Intel Ubuntu validation cloned SimplifiedLogic/creoson at commit 1939a585a1fcc94b6c05586af92c2da00adebdb0 and downloaded release v3.0.1 asset CreosonServer-3.0.1-win64.zip. The source build requires a Creo installation with JLINK `text/java/pfcasync.jar`, CreosonSetup ZIPs, Commons Codec, and Jackson jars. The release ZIP contains CreosonServer-3.0.0.jar plus dependencies, `creoson_run.bat`, and `jshellnative.dll`; it is a CREOSON JSON/JLINK micro-server, not an MCP protocol server. The catalog's old `java -jar creoson.jar` command is invalid: `java -jar CreosonServer-3.0.0.jar` returns `no main manifest attribute`. Calling the actual main class `com.simplifiedlogic.nitro.jshell.MainServer` with the release jars fails with `NoClassDefFoundError: com/ptc/cipjava/jxthrowable`, the expected missing Creo/JLINK Java class. No MCP initialize/tools/list calls could be made because CREOSON does not implement MCP stdio/SSE; it should remain a dependency for Creo MCPs rather than a runnable MCP server entry.",
            "ubuntu-linux-x64-container",
            ["Creo", "JLINK", "pfcasync.jar", "MCP wrapper"],
        ),
        "follow_up_url": "docs/mcp-catalog/followups/creoson-mcp-bridge.md",
        "install_blocked_reason": "CREOSON is a valid Creo JSON/JLINK bridge but does not implement MCP; it needs an MCP wrapper and a Windows Creo/JLINK host before Wright can expose it as an MCP server.",
        "headless_ok": "no",
    },
    "solidworks-mcp-python": {
        "verification_state": "community_mcp",
        "installability_tier": "non_working",
        "risk_level": "high",
        "deployment_mode": "local-bridge",
        "host_software_required": ["Windows", "SolidWorks", "Windows COM"],
        "platform_support": platform_support(
            {
                "windows_11_x64": {
                    "status": "host-dependent",
                    "tested": False,
                    "notes": "requires Windows 10/11, python.org Python, SolidWorks, and Windows COM after the Python dependency mismatch is fixed",
                },
                "linux_x64": {
                    "status": "no",
                    "tested": True,
                    "notes": "clean Intel Ubuntu validation installed the package but startup fails before MCP initialization because pydantic-ai 2.0.0 no longer provides pydantic_ai.toolsets.fastmcp",
                },
                "linux_arm64": {
                    "status": "no",
                    "tested": False,
                    "notes": "Windows COM and SolidWorks are required; Linux ARM64 not applicable for live CAD automation",
                },
                "macos_x64": {
                    "status": "no",
                    "tested": False,
                    "notes": "Windows COM and SolidWorks are required",
                },
                "macos_arm64": {
                    "status": "no",
                    "tested": False,
                    "notes": "Windows COM and SolidWorks are required",
                },
            }
        ),
        "approval_gates": HIGH_RISK_GATES,
        "validation_result": validation_summary(
            "failed",
            "Clean Intel Ubuntu validation cloned andrewbartels1/SolidworksMCP-python at commit f0858a7b9cf8cb9a7838ddfaa91a706ef6439cab, created a Python 3.12 virtual environment, and installed with `pip install -e \".[test]\"`. The install resolved `solidworks-mcp-python` 1.0.0, `pydantic-ai` 2.0.0, `fastmcp` 3.4.2, and `mcp` 1.28.1; Linux correctly skipped the Windows-only `pywin32`, `pywin32-ctypes`, and `comtypes` dependencies. Upstream focused tests failed during import because `src/solidworks_mcp/server.py` imports `pydantic_ai.toolsets.fastmcp.FastMCPToolset`, which is not present in `pydantic-ai` 2.0.0. `solidworks-mcp --help` and `python -m solidworks_mcp.server` fail with `ModuleNotFoundError: No module named 'pydantic_ai.toolsets.fastmcp'` before MCP initialization, so no `initialize`, `notifications/initialized`, or `tools/list` calls could be made. Full live CAD validation also requires Windows, SolidWorks, and COM after the Python dependency mismatch is fixed.",
            "ubuntu-linux-x64-container",
            ["compatible pydantic-ai API", "Windows", "SolidWorks", "Windows COM"],
        ),
        "follow_up_url": "docs/mcp-catalog/followups/solidworks-mcp-python.md",
        "install_blocked_reason": "Current declared dependency range resolves to pydantic-ai 2.0.0, which breaks server import before MCP startup.",
        "headless_ok": "no",
    },
    "solidworks-mcp-ts": {
        "verification_state": "community_mcp",
        "installability_tier": "might_work",
        "risk_level": "high",
        "deployment_mode": "local-bridge",
        "host_software_required": ["Windows", "SolidWorks", "Windows COM", "winax"],
        "platform_support": platform_support(
            {
                "windows_11_x64": {
                    "status": "host-dependent",
                    "tested": False,
                    "notes": "requires Windows 10/11, Node 20+, SolidWorks, and winax/Windows COM for live CAD operations",
                },
                "linux_x64": {
                    "status": "host-dependent",
                    "tested": True,
                    "notes": "clean Intel Ubuntu validation installed, built, passed mock tests, initialized MCP, and reached clear winax/Windows COM diagnostics on tool calls",
                },
                "linux_arm64": {
                    "status": "no",
                    "tested": False,
                    "notes": "winax and SolidWorks COM are Windows-only",
                },
                "macos_x64": {
                    "status": "no",
                    "tested": False,
                    "notes": "winax and SolidWorks COM are Windows-only",
                },
                "macos_arm64": {
                    "status": "no",
                    "tested": False,
                    "notes": "winax and SolidWorks COM are Windows-only",
                },
            }
        ),
        "approval_gates": HIGH_RISK_GATES,
        "validation_result": validation_summary(
            "dependency_missing",
            "Clean Intel Ubuntu validation cloned vespo92/SolidworksMCP-TS at commit c50ba5867f1d1632a5f6857a2b4aa5ad9b1838b7, installed selected Node 20.20.2 because the package requires Node >=20, ran `npm install`, `npm run build`, and `USE_MOCK_SOLIDWORKS=true npm test`. Upstream tests passed with 52 tests across 4 files. Package version is `solidworks-mcp-server` 3.1.3; `npm ls winax --depth=0` reported `winax` 3.6.2, but the native module cannot self-register on Linux. MCP stdio initialized as serverInfo `solidworks-mcp-server` version 3.1.3 and listed 86 tools. Calls to `generate_vba_script` and `create_part` both returned the expected diagnostic: `The winax native module is not available. SolidWorks COM automation requires it on Windows`, with underlying load error `Module did not self-register: '/tmp/solidworks-mcp-ts/node_modules/winax/build/Release/node_activex.node'`. Full validation requires Windows, SolidWorks, and a working winax build.",
            "ubuntu-linux-x64-container",
            ["Windows", "SolidWorks", "Windows COM", "working winax native module"],
        ),
        "install_blocked_reason": "Ubuntu can install, build, test, initialize, and list tools, but every meaningful tool call requires the Windows-only winax/SolidWorks COM backend.",
        "headless_ok": "no",
    },
    "solidworks-mcp-alisamsam": {
        "verification_state": "community_mcp",
        "installability_tier": "non_working",
        "risk_level": "high",
        "deployment_mode": "local-bridge",
        "host_software_required": ["Windows", "SolidWorks", "Windows COM", "pywin32"],
        "platform_support": platform_support(
            {
                "windows_11_x64": {
                    "status": "host-dependent",
                    "tested": False,
                    "notes": "requires Windows, SolidWorks 2023-2025, and pywin32 after requirements are fixed",
                },
                "linux_x64": {
                    "status": "no",
                    "tested": True,
                    "notes": "clean Intel Ubuntu validation failed exact requirements install because asyncio-compat and pywin32 have no Linux PyPI distributions; minimal start then failed importing win32com",
                },
                "linux_arm64": {
                    "status": "no",
                    "tested": False,
                    "notes": "Windows COM and SolidWorks are required",
                },
                "macos_x64": {
                    "status": "no",
                    "tested": False,
                    "notes": "Windows COM and SolidWorks are required",
                },
                "macos_arm64": {
                    "status": "no",
                    "tested": False,
                    "notes": "Windows COM and SolidWorks are required",
                },
            }
        ),
        "approval_gates": HIGH_RISK_GATES,
        "validation_result": validation_summary(
            "failed",
            "Clean Intel Ubuntu validation cloned alisamsam/solidworks-mcp at commit ee8f42a1a919af5e0fa8d1dcd24270c9983ce027 and followed the documented install path `pip install -r requirements.txt`. The exact install failed because `asyncio-compat>=0.1.0` has no matching PyPI distribution. `pip index versions asyncio-compat` and `pip index versions pywin32` both returned no matching distribution on Linux. After installing only the available runtime dependencies (`mcp` and `python-dotenv`) to continue as far as possible, `python solidworks_mcp_server.py` failed during import with `ModuleNotFoundError: No module named 'win32com'` from `solidworks_mcp/automation/base.py`. No upstream tests were present, and no MCP `initialize`, `notifications/initialized`, or `tools/list` calls could be made because the server cannot start from the declared requirements. Windows/SolidWorks validation should wait until the invalid requirement is removed and Windows-only dependencies are marked appropriately.",
            "ubuntu-linux-x64-container",
            [
                "published asyncio-compat package or removed requirement",
                "pywin32",
                "win32com",
                "Windows",
                "SolidWorks",
            ],
        ),
        "follow_up_url": "docs/mcp-catalog/followups/solidworks-mcp-alisamsam.md",
        "install_blocked_reason": "The documented requirements file references an unavailable package and unconditionally requires Windows-only COM modules.",
        "headless_ok": "no",
    },
}

WINDOWS_DESKTOP_HOSTS = {
    "solidworks-mcp-python": ["SolidWorks", "Windows COM"],
    "solidworks-mcp-ts": ["SolidWorks", "Windows COM"],
    "multicad-mcp-ancode666": ["ZWCAD", "GstarCAD", "BricsCAD", "Windows COM"],
}

for index, entry in enumerate(ENGINEERING_CATALOG):
    metadata = CATALOG_METADATA.get(entry["server_id"], {})
    if (
        entry["server_id"] in WINDOWS_DESKTOP_HOSTS
        and entry["server_id"] not in CATALOG_METADATA
    ):
        metadata = {
            "verification_state": "user_reported_url_needed",
            "installability_tier": "might_work",
            "risk_level": "high",
            "deployment_mode": "local-bridge",
            "host_software_required": WINDOWS_DESKTOP_HOSTS[entry["server_id"]],
            "platform_support": platform_support(
                {
                    "windows_11_x64": {
                        "status": "host-dependent",
                        "tested": False,
                        "notes": "requires Windows desktop host software",
                    },
                    "linux_x64": {
                        "status": "no",
                        "tested": True,
                        "notes": "not runnable in the first Ubuntu container target",
                    },
                    "linux_arm64": {
                        "status": "no",
                        "tested": False,
                        "notes": "not runnable in the first Ubuntu container target",
                    },
                    "macos_x64": {
                        "status": "host-dependent",
                        "tested": False,
                        "notes": "only if host software supports macOS",
                    },
                    "macos_arm64": {
                        "status": "host-dependent",
                        "tested": False,
                        "notes": "only if host software supports macOS ARM64",
                    },
                }
            ),
            "approval_gates": HIGH_RISK_GATES,
        }
    ENGINEERING_CATALOG[index] = _with_meta(entry, **metadata)

ENGINEERING_CATALOG.sort(key=tier_sort_key)
