import os
import sqlite3
import sys
import json
import time

# Ensure api package is importable when run directly
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from api.config import DATABASE_PATH

# ──────────────────────────────────────────────────────────────────────────────
# Engineering MCP Catalog  (sourced from docs/Engineering MCP Tools Discovery.md)
# ──────────────────────────────────────────────────────────────────────────────
# Each entry uses a stable deterministic server_id so INSERT OR IGNORE is idempotent.
# Fields: (server_id, name, type, command, is_active, is_installed, status,
#          category, image_url, description, source_url, installed_version)

ENGINEERING_CATALOG = [
    # ── CAD · Open Source / Linux-Installable ─────────────────────────────────
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
                "--project",
                "/home/burhop/repos/wright/packages/freecad_mcp",
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
        "command": json.dumps(["npx", "freecad-mcp"]),
        "category": "cad",
        "image_url": "https://avatars.githubusercontent.com/u/1413352?s=64",
        "description": "AI copilot workbench embedded in FreeCAD. 13 PartDesign + 18 Part operations, cross-platform automated installation, and screenshot verification.",
        "source_url": "https://github.com/contextform/freecad-mcp",
    },
    {
        "server_id": "freecad-robust-spkane",
        "name": "FreeCAD Robust",
        "type": "stdio",
        "command": json.dumps(["uvx", "freecad-addon-robust-mcp-server"]),
        "category": "cad",
        "image_url": "https://avatars.githubusercontent.com/u/1413352?s=64",
        "description": "150+ tools for deep FreeCAD control: object management, arbitrary Python execution, macro development. Supports XML-RPC, JSON-RPC, and headless CI modes.",
        "source_url": "https://github.com/spkane/freecad-addon-robust-mcp-server",
    },
    {
        "server_id": "freecad-core-nekanat",
        "name": "FreeCAD Core",
        "type": "stdio",
        "command": json.dumps(["uvx", "freecad-mcp"]),
        "category": "cad",
        "image_url": "https://avatars.githubusercontent.com/u/1413352?s=64",
        "description": "Lightweight FreeCAD MCP integration focused on core parametric modeling operations via the native Python API.",
        "source_url": "https://github.com/neka-nat/freecad-mcp",
    },
    {
        "server_id": "freecad-booleans-lucygoodchild",
        "name": "FreeCAD Booleans",
        "type": "stdio",
        "command": json.dumps(["uvx", "freecad-mcp-server"]),
        "category": "cad",
        "image_url": "https://avatars.githubusercontent.com/u/1413352?s=64",
        "description": "FreeCAD server specializing in primitive generation and complex Boolean logic operations for solid modeling.",
        "source_url": "https://github.com/lucygoodchild/freecad-mcp-server",
    },
    {
        "server_id": "caid-opencascade-dreliq9",
        "name": "CAiD OpenCASCADE",
        "type": "stdio",
        "command": json.dumps(["uvx", "caid-mcp"]),
        "category": "cad",
        "image_url": "https://avatars.githubusercontent.com/u/159555580?s=64",
        "description": "Direct OpenCASCADE (OCCT) kernel interface via CAiD. Strict ForgeResult validation layer tracks volume, surface area, and manifold diagnostics.",
        "source_url": "https://github.com/dreliq9/caid-mcp",
    },
    # ── CAD · Cloud / Network Services ────────────────────────────────────────
    {
        "server_id": "zoo-dev-cloud-cad",
        "name": "Zoo.dev Cloud CAD",
        "type": "sse",
        "command": "https://api.zoo.dev/mcp",
        "category": "cad",
        "image_url": "https://avatars.githubusercontent.com/u/80992670?s=64",
        "description": "Cloud CAD engine by Zoo.dev (formerly KittyCAD). Offloads heavy geometric computation to scalable cloud infrastructure with per-second billing.",
        "source_url": "https://github.com/KittyCAD/zoo-mcp",
    },
    {
        "server_id": "onshape-mcp-hedless",
        "name": "Onshape MCP",
        "type": "sse",
        "command": "https://api.onshape.com/mcp",
        "category": "cad",
        "image_url": "https://avatars.githubusercontent.com/u/6536550?s=64",
        "description": "Cloud-native Onshape REST API access. Navigate workspaces, manage Part Studios, create parametric sketches, and read/write variable tables.",
        "source_url": "https://github.com/hedless/onshape-mcp",
    },
    # ── Simulation / FEA ──────────────────────────────────────────────────────
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
    # ── PLM / Enterprise Cloud APIs ───────────────────────────────────────────
    {
        "server_id": "autodesk-aps-official",
        "name": "Autodesk Platform Services",
        "type": "sse",
        "command": "https://developer.api.autodesk.com",
        "category": "plm",
        "image_url": "https://avatars.githubusercontent.com/u/1478570?s=64",
        "description": "Official Autodesk APS integration. Secure data management, model derivatives, webhooks, and AEC data modeling with SSA-based authentication.",
        "source_url": "https://github.com/autodesk-platform-services/aps-mcp-server-nodejs",
    },
    {
        "server_id": "autodesk-aps-petrbroz",
        "name": "Autodesk APS (Community)",
        "type": "sse",
        "command": "https://developer.api.autodesk.com",
        "category": "plm",
        "image_url": "https://avatars.githubusercontent.com/u/1478570?s=64",
        "description": "Community-maintained Autodesk Platform Services MCP server. Alternative implementation supporting Claude Desktop and VS Code integration.",
        "source_url": "https://github.com/petrbroz/aps-mcp-server",
    },
    {
        "server_id": "siemens-element-mcp",
        "name": "Siemens Element Design System",
        "type": "sse",
        "command": "https://element.siemens.io/mcp",
        "category": "plm",
        "image_url": "https://avatars.githubusercontent.com/u/4006395?s=64",
        "description": "Siemens Element design system via RAG. Provides AI agents with component APIs, UX writing guidelines, and front-end best practices with version matching.",
        "source_url": "https://element.siemens.io/get-started/element-mcp/",
    },
    {
        "server_id": "siemens-wincc-unified",
        "name": "Siemens WinCC Unified",
        "type": "sse",
        "command": "https://wincc-unified.siemens.io/mcp",
        "category": "plm",
        "image_url": "https://avatars.githubusercontent.com/u/4006395?s=64",
        "description": "Bridge to WinCC Unified SCADA runtime. Access real-time data tags, UDTs, and alarm systems for factory-floor AI-driven diagnostics.",
        "source_url": "https://support.industry.siemens.com/cs/document/110002407",
    },
    {
        "server_id": "ptc-thingworx-mcp",
        "name": "PTC ThingWorx IoT",
        "type": "sse",
        "command": "https://thingworx.ptc.com/mcp",
        "category": "plm",
        "image_url": "https://avatars.githubusercontent.com/u/1690598?s=64",
        "description": "PTC ThingWorx IoT platform integration. Tools for machine KPIs, resources for sensor data, prompts for interaction templates. OAuth 2.0 secured.",
        "source_url": "https://support.ptc.com/help/thingworx/platform/r10.1/",
    },
    # ── CAD · Desktop / Windows Required ──────────────────────────────────────
    {
        "server_id": "fusion360-mcp-faust",
        "name": "Autodesk Fusion 360",
        "type": "stdio",
        "command": json.dumps(["python", "fusion360_mcp_server.py"]),
        "category": "cad",
        "image_url": "https://avatars.githubusercontent.com/u/1478570?s=64",
        "description": "84 tools for parametric sketching, sheet metal, Boolean ops, and CAM toolpath generation. Requires Fusion 360 desktop application. ⚠️ Windows/macOS only.",
        "source_url": "https://github.com/faust-machines/fusion360-mcp-server",
    },
    {
        "server_id": "solidworks-mcp-python",
        "name": "SolidWorks MCP (Python)",
        "type": "stdio",
        "command": json.dumps(["python", "solidworks_mcp.py"]),
        "category": "cad",
        "image_url": "https://avatars.githubusercontent.com/u/6536550?s=64",
        "description": "109 tools for SolidWorks. Real-time PNG preview sync, SQLite checkpoint workflows, AI-assisted design loop. ⚠️ Requires Windows 10/11 + SolidWorks.",
        "source_url": "https://github.com/andrewbartels1/SolidworksMCP-python",
    },
    {
        "server_id": "solidworks-mcp-ts",
        "name": "SolidWorks MCP (TypeScript)",
        "type": "stdio",
        "command": json.dumps(["npx", "solidworks-mcp-ts"]),
        "category": "cad",
        "image_url": "https://avatars.githubusercontent.com/u/6536550?s=64",
        "description": "TypeScript SolidWorks integration via winax COM. Auto-generates VBA macros for operations exceeding 12-parameter limit. ⚠️ Requires Windows + SolidWorks.",
        "source_url": "https://github.com/vespo92/SolidworksMCP-TS",
    },
    {
        "server_id": "solidworks-api-docs",
        "name": "SolidWorks API Docs",
        "type": "stdio",
        "command": json.dumps(["uvx", "solidworks-api-mcp"]),
        "category": "cad",
        "image_url": "https://avatars.githubusercontent.com/u/6536550?s=64",
        "description": "Full-text and keyword search over the SolidWorks API documentation corpus. Look up interface members and enums during code generation.",
        "source_url": "https://github.com/kilwizac/solidworks-api-mcp",
    },
    {
        "server_id": "creo-parametric-mcp",
        "name": "PTC Creo Parametric",
        "type": "stdio",
        "command": json.dumps(["python", "creo_mcp.py"]),
        "category": "cad",
        "image_url": "https://avatars.githubusercontent.com/u/1690598?s=64",
        "description": "Creo Parametric bridge via CREOSON JSON-RPC. Read sessions, manipulate parameters, regenerate assemblies, extract BOMs. ⚠️ Requires Creo desktop.",
        "source_url": "https://github.com/yangkunyi/creo-mcp",
    },
    {
        "server_id": "rhino-mcp-mcneel",
        "name": "Rhino 3D (McNeel)",
        "type": "stdio",
        "command": json.dumps(["dotnet", "run", "RhinoMCP.dll"]),
        "category": "cad",
        "image_url": "https://avatars.githubusercontent.com/u/1220980?s=64",
        "description": "NURBS surface modeling via Rhino 3D. Precise primitive generation, layer filtering, and experimental RhinoCommon C# script execution. ⚠️ Requires Rhino 3D.",
        "source_url": "https://github.com/jingcheng-chen/rhinomcp",
    },
    {
        "server_id": "blender-mcp-ahujasid",
        "name": "Blender 3D",
        "type": "stdio",
        "command": json.dumps(["uvx", "blender-mcp"]),
        "category": "cad",
        "image_url": "https://avatars.githubusercontent.com/u/52924985?s=64",
        "description": "Control Blender via bpy API: scene lighting, procedural textures, Poly Haven asset imports. Pairs with sequential-thinking for complex architectural workflows.",
        "source_url": "https://github.com/ahujasid/blender-mcp",
    },
    {
        "server_id": "sketchup-mcp-mhyrr",
        "name": "SketchUp 3D",
        "type": "stdio",
        "command": json.dumps(["ruby", "sketchup_mcp.rb"]),
        "category": "cad",
        "image_url": "https://avatars.githubusercontent.com/u/458134?s=64",
        "description": "Ruby-based TCP server in SketchUp. Component manipulation, material application, and Ruby code evaluation. ⚠️ Requires SketchUp desktop.",
        "source_url": "https://github.com/mhyrr/sketchup-mcp",
    },
    {
        "server_id": "revit-mcp-servers",
        "name": "Autodesk Revit BIM",
        "type": "stdio",
        "command": json.dumps(["dotnet", "run", "RevitMCP.dll"]),
        "category": "cad",
        "image_url": "https://avatars.githubusercontent.com/u/1478570?s=64",
        "description": "AI-powered BIM modeling for Autodesk Revit. CRUD operations on architectural elements, structural analysis integration. ⚠️ Requires Revit desktop.",
        "source_url": "https://github.com/mcp-servers-for-revit/revit-mcp",
    },
    # ── 2D CAD / Drafting ─────────────────────────────────────────────────────
    {
        "server_id": "autocad-mcp-hvkshetry",
        "name": "AutoCAD MCP",
        "type": "stdio",
        "command": json.dumps(["python", "autocad_mcp.py"]),
        "category": "cad",
        "image_url": "https://avatars.githubusercontent.com/u/1478570?s=64",
        "description": "AutoCAD LT automation via dynamically generated AutoLISP. Block insertions, connecting lines, P&ID diagram generation. ⚠️ Requires AutoCAD LT 2024/2025.",
        "source_url": "https://github.com/hvkshetry/autocad-mcp",
    },
    {
        "server_id": "easy-mcp-autocad",
        "name": "Easy-MCP-AutoCAD",
        "type": "stdio",
        "command": json.dumps(["python", "easy_mcp_autocad.py"]),
        "category": "cad",
        "image_url": "https://avatars.githubusercontent.com/u/1478570?s=64",
        "description": "AutoCAD integration with SQLite data persistence. Extracts elemental data into queryable databases for BOM extraction and spatial analysis. ⚠️ Requires AutoCAD.",
        "source_url": "https://github.com/zh19980811/Easy-MCP-AutoCad",
    },
    {
        "server_id": "multicad-mcp-ancode666",
        "name": "MultiCAD MCP",
        "type": "stdio",
        "command": json.dumps(["python", "multicad_mcp.py"]),
        "category": "cad",
        "image_url": None,
        "description": "Cross-platform 2D CAD control for ZWCAD 2020+, GstarCAD 2020+, and BricsCAD 21+ via Windows COM. Execute drawing commands via natural language. ⚠️ Windows only.",
        "source_url": "https://github.com/AnCode666/multiCAD-mcp",
    },
    {
        "server_id": "cad-mcp-daobataotie",
        "name": "CAD-MCP Universal",
        "type": "stdio",
        "command": json.dumps(["python", "cad_mcp.py"]),
        "category": "cad",
        "image_url": None,
        "description": "Universal 2D CAD automation via COM. Compatible with AutoCAD-like APIs. Draw, plot, and manipulate 2D geometry. ⚠️ Requires Windows + CAD software.",
        "source_url": "https://github.com/daobataotie/CAD-MCP",
    },
    # ── Web / Experimental ────────────────────────────────────────────────────
    {
        "server_id": "webmcp-standard",
        "name": "WebMCP Standard",
        "type": "webmcp",
        "command": "https://webmcp.io",
        "category": "utilities",
        "image_url": None,
        "description": "Open standard for browser-based AI interaction. Exposes webpage functionality as MCP tools directly to agents — eliminates brittle DOM actuation.",
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
        "type": "webmcp",
        "command": "https://web3d-mcp.dev",
        "category": "utilities",
        "image_url": None,
        "description": "Generate, animate, and export 3D scenes using React Three Fiber (R3F). Programmatic 3D creation via modern web infrastructure.",
        "source_url": "https://www.reddit.com/r/mcp/comments/1tepcxp",
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
    # ── Manufacturing / CAM ───────────────────────────────────────────────────
    {
        "server_id": "creopyson-creoson",
        "name": "CREOSON Middleware",
        "type": "stdio",
        "command": json.dumps(["python", "creopyson_bridge.py"]),
        "category": "manufacturing",
        "image_url": "https://avatars.githubusercontent.com/u/1690598?s=64",
        "description": "CREOSON JSON-RPC middleware for Creo Parametric. Exposes JLINK/Java APIs for assembly regeneration, BOM extraction, and STEP import. ⚠️ Requires Creo.",
        "source_url": "https://github.com/SimplifiedLogic/creoson",
    },
]


def run_migrations():
    print(f"Running database migrations on: {DATABASE_PATH}")
    os.makedirs(os.path.dirname(DATABASE_PATH), exist_ok=True)
    conn = sqlite3.connect(DATABASE_PATH)
    try:
        conn.execute("PRAGMA journal_mode=WAL;")

        # 1. Create mcp_servers table
        conn.execute("""
        CREATE TABLE IF NOT EXISTS mcp_servers (
            server_id TEXT PRIMARY KEY,
            name TEXT NOT NULL UNIQUE,
            type TEXT NOT NULL CHECK(type IN ('stdio', 'sse', 'webmcp')),
            command TEXT,
            is_active INTEGER NOT NULL DEFAULT 0 CHECK(is_active IN (0, 1)),
            is_installed INTEGER NOT NULL DEFAULT 0 CHECK(is_installed IN (0, 1)),
            status TEXT NOT NULL DEFAULT 'inactive' CHECK(status IN ('active', 'inactive', 'error')),
            error_message TEXT,
            category TEXT NOT NULL DEFAULT 'utilities',
            created_at INTEGER NOT NULL,
            updated_at INTEGER NOT NULL,
            image_url TEXT,
            description TEXT,
            source_url TEXT,
            installed_version TEXT,
            env_vars TEXT,
            instructions TEXT
        );
        """)

        # 2. Create mcp_tools table
        conn.execute("""
        CREATE TABLE IF NOT EXISTS mcp_tools (
            tool_id TEXT PRIMARY KEY,
            server_id TEXT NOT NULL,
            name TEXT NOT NULL,
            description TEXT,
            input_schema TEXT NOT NULL,
            is_enabled INTEGER NOT NULL DEFAULT 1 CHECK(is_enabled IN (0, 1)),
            created_at INTEGER NOT NULL,
            FOREIGN KEY (server_id) REFERENCES mcp_servers(server_id) ON DELETE CASCADE
        );
        """)

        # 3. ── One-time cleanup: remove junk / test entries ──────────────────
        conn.execute("DELETE FROM mcp_servers WHERE name LIKE 'Playwright Test%'")
        conn.execute("DELETE FROM mcp_servers WHERE name = 'Calcul mesh'")
        conn.execute("DELETE FROM mcp_servers WHERE name = 'Custom SSE Link'")

        # 4. ── Fix false is_installed flags ──────────────────────────────────
        #    Reset servers that are marked installed+error but aren't actually
        #    running.  Keep OpenSCAD Geometry (the only truly installed server).
        #    Only reset catalog servers, not custom user-added servers.
        catalog_ids = [entry["server_id"] for entry in ENGINEERING_CATALOG]
        placeholders = ",".join("?" for _ in catalog_ids)
        conn.execute(
            f"""
        UPDATE mcp_servers
        SET is_installed = 0,
            status = 'inactive',
            error_message = NULL,
            installed_version = NULL
        WHERE is_installed = 1
          AND status = 'error'
          AND server_id IN ({placeholders})
          AND server_id != 'openscad-mcp-server'
        """,
            tuple(catalog_ids),
        )

        # 5. Seed the full engineering catalog
        now = int(time.time())
        for entry in ENGINEERING_CATALOG:
            conn.execute(
                """
            INSERT OR IGNORE INTO mcp_servers 
                (server_id, name, type, command, is_active, is_installed, status,
                 category, created_at, updated_at, image_url, description,
                 source_url, instructions, installed_version)
            VALUES (?, ?, ?, ?, 0, 0, 'inactive', ?, ?, ?, ?, ?, ?, ?, NULL)
            """,
                (
                    entry["server_id"],
                    entry["name"],
                    entry["type"],
                    entry["command"],
                    entry["category"],
                    now,
                    now,
                    entry.get("image_url"),
                    entry["description"],
                    entry.get("source_url"),
                    entry.get("instructions"),
                ),
            )

        # 6. Update existing catalog entries to the latest metadata from the catalog
        for entry in ENGINEERING_CATALOG:
            conn.execute(
                """
            UPDATE mcp_servers
            SET name = ?,
                type = ?,
                command = ?,
                category = ?,
                image_url = ?,
                description = ?,
                source_url = ?,
                instructions = ?
            WHERE server_id = ?
            """,
                (
                    entry["name"],
                    entry["type"],
                    entry["command"],
                    entry["category"],
                    entry.get("image_url"),
                    entry["description"],
                    entry.get("source_url"),
                    entry.get("instructions"),
                    entry["server_id"],
                ),
            )

        # 7. Create engineering_workspaces table
        conn.execute("""
        CREATE TABLE IF NOT EXISTS engineering_workspaces (
            workspace_id TEXT PRIMARY KEY,
            session_id TEXT NOT NULL UNIQUE,
            local_path TEXT NOT NULL,
            git_remote_url TEXT,
            git_username TEXT,
            git_token TEXT,
            enabled_tools TEXT,
            created_at INTEGER NOT NULL,
            updated_at INTEGER NOT NULL,
            workspace_name TEXT,
            workspace_prompt TEXT,
            git_large_file_threshold INTEGER DEFAULT 10485760
        );
        """)

        # Check if enabled_tools column exists, add it if not (for existing databases)
        cursor = conn.cursor()
        cursor.execute("PRAGMA table_info(engineering_workspaces)")
        columns = [col[1] for col in cursor.fetchall()]
        if columns and "enabled_tools" not in columns:
            conn.execute(
                "ALTER TABLE engineering_workspaces ADD COLUMN enabled_tools TEXT;"
            )
            print("Added enabled_tools column to engineering_workspaces table.")

        # Check if is_installed column exists in mcp_servers, add it if not (for existing databases)
        cursor.execute("PRAGMA table_info(mcp_servers)")
        mcp_columns = [col[1] for col in cursor.fetchall()]
        if mcp_columns and "is_installed" not in mcp_columns:
            conn.execute(
                "ALTER TABLE mcp_servers ADD COLUMN is_installed INTEGER NOT NULL DEFAULT 0 CHECK(is_installed IN (0, 1));"
            )
            print("Added is_installed column to mcp_servers table.")

        new_cols = [
            ("image_url", "TEXT"),
            ("description", "TEXT"),
            ("source_url", "TEXT"),
            ("installed_version", "TEXT"),
            ("env_vars", "TEXT"),
            ("instructions", "TEXT"),
        ]
        for col_name, col_def in new_cols:
            if mcp_columns and col_name not in mcp_columns:
                conn.execute(
                    f"ALTER TABLE mcp_servers ADD COLUMN {col_name} {col_def};"
                )
                print(f"Added {col_name} column to mcp_servers table.")

        # 8. Add workspace_name column if missing (007-workspace-dashboard-ux)
        cursor.execute("PRAGMA table_info(engineering_workspaces)")
        ws_columns = [col[1] for col in cursor.fetchall()]
        if ws_columns and "workspace_name" not in ws_columns:
            conn.execute(
                "ALTER TABLE engineering_workspaces ADD COLUMN workspace_name TEXT;"
            )
            print("Added workspace_name column to engineering_workspaces table.")

        if ws_columns and "workspace_prompt" not in ws_columns:
            conn.execute(
                "ALTER TABLE engineering_workspaces ADD COLUMN workspace_prompt TEXT;"
            )
            print("Added workspace_prompt column to engineering_workspaces table.")

        if ws_columns and "git_large_file_threshold" not in ws_columns:
            conn.execute(
                "ALTER TABLE engineering_workspaces ADD COLUMN git_large_file_threshold INTEGER DEFAULT 10485760;"
            )
            print("Added git_large_file_threshold column to engineering_workspaces table.")

        # 9. Create agent_contexts table (007-workspace-dashboard-ux)
        conn.execute("""
        CREATE TABLE IF NOT EXISTS agent_contexts (
            workspace_id TEXT PRIMARY KEY,
            context_data TEXT,
            updated_at INTEGER NOT NULL,
            FOREIGN KEY (workspace_id) REFERENCES engineering_workspaces(workspace_id) ON DELETE CASCADE
        );
        """)

        # 10. Create chat_messages table (008-quality-testing-observability)
        conn.execute("""
        CREATE TABLE IF NOT EXISTS chat_messages (
            id TEXT PRIMARY KEY,
            session_id TEXT NOT NULL,
            role TEXT NOT NULL CHECK(role IN ('user', 'assistant')),
            content TEXT NOT NULL,
            timestamp INTEGER NOT NULL,
            trace_id TEXT,
            created_at INTEGER NOT NULL
        );
        """)
        conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_chat_messages_session
            ON chat_messages(session_id, timestamp);
        """)

        # 11. Create system_settings table
        conn.execute("""
        CREATE TABLE IF NOT EXISTS system_settings (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL
        );
        """)

        conn.commit()
        print(
            f"Database migrations applied successfully. Seeded {len(ENGINEERING_CATALOG)} engineering MCP servers."
        )
    finally:
        conn.close()


if __name__ == "__main__":
    run_migrations()
