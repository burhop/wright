# Wright Hermes Plugin — Comprehensive Development Plan

**Document Owner**: Wright Project  
**Status**: Draft — Revised  
**Created**: 2026-06-22  
**Last Updated**: 2026-06-22  
**Related Specs**: [026-mcp-credential-setup](../specs/026-mcp-credential-setup/plan.md)

---

## Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [Existing Architecture — What's Already Built](#2-existing-architecture--whats-already-built)
3. [What the Plugin Actually Needs to Do](#3-what-the-plugin-actually-needs-to-do)
4. [Architecture Overview](#4-architecture-overview)
5. [Plugin Structure & File Layout](#5-plugin-structure--file-layout)
6. [Catalog System](#6-catalog-system)
7. [Gateway Bridge — The Core Mechanism](#7-gateway-bridge--the-core-mechanism)
8. [Workspace Context Injection](#8-workspace-context-injection)
9. [Slash Commands — User-Facing Surface](#9-slash-commands--user-facing-surface)
10. [Credential Management — Already Solved](#10-credential-management--already-solved)
11. [Distribution Strategy](#11-distribution-strategy)
12. [Docker Appliance Integration](#12-docker-appliance-integration)
13. [Existing-Install Integration](#13-existing-install-integration)
14. [Security Considerations](#14-security-considerations)
15. [Testing & Validation Strategy](#15-testing--validation-strategy)
16. [Submission & Community Sharing](#16-submission--community-sharing)
17. [Implementation Phases](#17-implementation-phases)
18. [Open Questions & Risks](#18-open-questions--risks)
19. [Appendix: Reference Links](#19-appendix-reference-links)

---

## 1. Executive Summary

The **Wright Hermes Plugin** (`hermes-plugin-wright`) is a Hermes Agent plugin that connects Hermes to Wright's existing MCP infrastructure. The key insight is that **Wright already has a comprehensive tool management system** — the plugin's job is to bridge Hermes into it, not to rebuild it.

### What Wright Already Has

| Capability | Where It Lives | Status |
|:---|:---|:---|
| MCP server lifecycle (start/stop/call) | `tool_registry.McpEngine` | ✅ Built |
| Tool selection per workspace | `engineering_workspaces.enabled_tools` | ✅ Built |
| Live MCP reload without restart | `gateway.py` SSE → `notifications/tools/list_changed` | ✅ Built |
| Credential store (0600 JSON, fcntl locking) | `tool_registry.secrets` | ✅ Built |
| Credential prompting via UI | Workspace tools panel + MCP settings | ✅ Built |
| Tool schema discovery & DB sync | `McpEngine.start_server()` → `list_tools()` | ✅ Built |
| Workspace-scoped tool enablement | `toggle_workspace_tool_endpoint` + gateway filter | ✅ Built |
| WebMCP browser-side tools | `McpEngine.call_tool()` → WebSocket broadcast | ✅ Built |
| Hermes config.yaml sync | `hermes_sync.py` | ✅ Built |

### What the Plugin Adds

The plugin is a **thin bridge layer** that:
1. Registers the `wright-gateway` MCP server entry in Hermes config
2. Provides workspace-aware context injection via `.hermes.md`
3. Exposes a catalog of installable engineering MCP servers (browseable, not pre-activated)
4. Offers optional `/wright` slash commands for status and catalog browsing within Hermes

---

## 2. Existing Architecture — What's Already Built

### 2.1 The Wright Application Stack

Wright is a **full-stack application** with three main layers. The Hermes plugin bridges into this system — it does not replace any part of it.

```
┌──────────────────────────────────────────────────────────────────┐
│  React Web UI (apps/web)  ─ Port 5173 (dev) / co-hosted (prod)  │
│  ┌────────────┐ ┌──────────┐ ┌──────────┐ ┌───────────────────┐ │
│  │ Workspace  │ │ Chat     │ │ Tool     │ │ Credential Setup  │ │
│  │ Dashboard  │ │ Composer │ │ Cards    │ │ Modal (per-tool)  │ │
│  └────────────┘ └──────────┘ └──────────┘ └───────────────────┘ │
│              ↕ HTTP                                              │
├──────────────────────────────────────────────────────────────────┤
│  FastAPI Server (apps/api) ─ Port 8000                           │
│  ┌───────────────────────────────────────────────────────────┐   │
│  │ Routers:                                                  │   │
│  │  /api/mcp/servers     — Register, install, toggle, creds  │   │
│  │  /api/mcp/tools       — List/toggle individual tools      │   │
│  │  /api/workspace/      — CRUD, activate, tool toggle       │   │
│  │  /api/gateway/        — Proxy tools/list + tools/call     │   │
│  │  /api/agent/          — Chat, sessions, streaming         │   │
│  │  /api/settings/       — LLM config, system settings       │   │
│  └───────────────────────────────────────────────────────────┘   │
│  ┌───────────────────────────────────────────────────────────┐   │
│  │ Services:                                                 │   │
│  │  hermes_sync.py       — Writes wrightgateway to config    │   │
│  │  McpEngine            — Server lifecycle (start/stop/call)│   │
│  │  Secrets Store        — ~/.config/wright/mcp-secrets.json │   │
│  └───────────────────────────────────────────────────────────┘   │
│  ┌───────────────────────────────────────────────────────────┐   │
│  │ Database: SQLite (WAL mode)                               │   │
│  │  mcp_servers           — Registry of all MCP servers      │   │
│  │  mcp_tools             — Discovered tool schemas          │   │
│  │  engineering_workspaces — Workspaces + enabled_tools       │   │
│  │  chat_messages         — Conversation history             │   │
│  └───────────────────────────────────────────────────────────┘   │
├──────────────────────────────────────────────────────────────────┤
│  Packages (packages/)                                            │
│  ┌────────────────┐ ┌─────────────────┐ ┌──────────────────────┐│
│  │ tool_registry   │ │ agent_adapters  │ │ core (workspace.py)  ││
│  │ McpEngine       │ │ HermesAdapter   │ │ WorkspaceManager     ││
│  │ StdioRunner     │ │ OpenClawAdapter │ │ enabled_tools logic  ││
│  │ SseRunner       │ │                 │ │ .hermes.md writer    ││
│  │ gateway.py      │ │                 │ │                      ││
│  │ secrets.py      │ │                 │ │                      ││
│  └────────────────┘ └─────────────────┘ └──────────────────────┘│
└──────────────────────────────────────────────────────────────────┘
```

**Key source files:**

| Layer | File | Purpose |
|:---|:---|:---|
| **API Routers** | [mcp.py](file:///home/burhop/repos/wright/apps/api/src/api/routers/mcp.py) | Server CRUD, install/uninstall, credential save, tool toggle |
| | [gateway.py](file:///home/burhop/repos/wright/apps/api/src/api/routers/gateway.py) | MCP proxy `tools/list` + `tools/call` + SSE events |
| | [workspace.py](file:///home/burhop/repos/wright/apps/api/src/api/routers/workspace.py) | Workspace CRUD, activate, tool toggle per workspace |
| | [agent.py](file:///home/burhop/repos/wright/apps/api/src/api/routers/agent.py) | Chat streaming, session management |
| **Services** | [hermes_sync.py](file:///home/burhop/repos/wright/apps/api/src/api/services/hermes_sync.py) | Writes `wrightgateway` to Hermes `config.yaml` |
| **Frontend** | [mcp-service.ts](file:///home/burhop/repos/wright/apps/web/src/services/mcp-service.ts) | TypeScript client calling all `/api/mcp/*` routes |
| | [ToolCard.tsx](file:///home/burhop/repos/wright/apps/web/src/components/tools/ToolCard.tsx) | Tool install/uninstall/credential UI |
| | [AddToolModal.tsx](file:///home/burhop/repos/wright/apps/web/src/components/tools/AddToolModal.tsx) | Register new MCP server modal |
| **Packages** | [manager.py](file:///home/burhop/repos/wright/packages/tool_registry/src/tool_registry/manager.py) | McpEngine — server lifecycle |
| | [gateway.py](file:///home/burhop/repos/wright/packages/tool_registry/src/tool_registry/gateway.py) | Stdio bridge (the single MCP server Hermes sees) |
| | [secrets.py](file:///home/burhop/repos/wright/packages/tool_registry/src/tool_registry/secrets.py) | Credential store (`0600`, `fcntl` locking) |
| | [hermes.py](file:///home/burhop/repos/wright/packages/agent_adapters/src/agent_adapters/hermes.py) | Hermes agent adapter (chat proxy) |

### 2.2 The Gateway Proxy Pattern (MCP Reload is Solved)

Wright's `wright-gateway` is a **single MCP server process** that acts as a multiplexing proxy between Hermes and all of Wright's managed MCP servers. This is the key architectural insight that eliminates the MCP reload problem entirely.

**How it works:**

```
Hermes Agent ←───stdio───→ wright-gateway ←───HTTP───→ Wright API Backend
                                                           │
                                                     ┌─────┴─────┐
                                                     │ McpEngine  │
                                                     │  ├─ FreeCAD (stdio runner)
                                                     │  ├─ OpenSCAD (stdio runner)
                                                     │  ├─ Onshape (sse runner)
                                                     │  └─ WebMCP (websocket)
                                                     └───────────┘
```

**Key behaviors:**

1. Hermes only sees **one** MCP server: `wrightgateway`
2. Tool names are **prefixed**: `freecadengineering__create_new_document`, `openscadmcp__render_preview`
3. When tools change (workspace switch, tool toggle, credential save), the gateway sends `notifications/tools/list_changed` via SSE → Hermes re-fetches `tools/list`
4. **No Hermes restart or `/reload-mcp` needed** — the gateway handles it

**Source**: [gateway.py](file:///home/burhop/repos/wright/packages/tool_registry/src/tool_registry/gateway.py) — The stdio bridge  
**Source**: [gateway.py (router)](file:///home/burhop/repos/wright/apps/api/src/api/routers/gateway.py) — The API backend

### 2.2 Workspace-Scoped Tool Selection

Users explicitly pick which MCP servers to enable **per workspace**. This is stored in the `engineering_workspaces.enabled_tools` column as a JSON array of server names.

**How it works:**

1. User creates a workspace in the Wright UI
2. User toggles tools on/off via the workspace tools panel → `POST /api/workspace/tools/toggle`
3. The enabled list is saved → `update_workspace_enabled_tools()`
4. The gateway filters `tools/list` responses to only include tools from enabled servers
5. `notify_gateway_tool_change()` pushes SSE → Hermes refreshes its tool list

**Source**: [workspace.py (toggle)](file:///home/burhop/repos/wright/apps/api/src/api/routers/workspace.py#L616-L647) — Toggle endpoint  
**Source**: [workspace.py (core)](file:///home/burhop/repos/wright/packages/core/src/core/workspace.py#L116-L169) — Enabled tools logic

### 2.3 Credential Store

The credential system is built and operational:

- Secrets stored at `~/.config/wright/mcp-secrets.json` with `0600` perms
- `fcntl` advisory locking prevents concurrent write corruption
- Values are never logged (structlog sanitization)
- `McpEngine.start_server()` reads credentials from the store and injects them as env vars
- Missing required credentials produce clear error messages
- UI shows credential status via `credentials_configured` field on `McpServer`

**Source**: [secrets.py](file:///home/burhop/repos/wright/packages/tool_registry/src/tool_registry/secrets.py)

### 2.4 Hermes Config Sync

The `hermes_sync.py` service already handles writing the `wrightgateway` entry to Hermes `config.yaml`:

```yaml
# Written automatically by Wright
mcp_servers:
  wrightgateway:
    command: uv
    args: [run, --project, /home/burhop/repos/wright, python, -m, tool_registry.gateway]
terminal:
  cwd: /home/burhop/repos/wright
```

**Source**: [hermes_sync.py](file:///home/burhop/repos/wright/apps/api/src/api/services/hermes_sync.py)

---

## 3. What the Plugin Actually Needs to Do

Given the existing architecture, the plugin's scope is **narrower and more focused** than originally planned:

### Must Have (Plugin Core)

| Feature | Description |
|:---|:---|
| **Gateway registration** | Ensure `wrightgateway` is registered in Hermes config on plugin load |
| **Catalog data file** | Bundle `catalog.yaml` describing ~30 installable engineering MCP servers with metadata (id, name, vendor, domains, transport, command, env_vars, dependencies) |
| **Install from catalog** | Agent-callable tool or slash command to install a catalog entry into Wright's SQLite registry (calls the Wright API) |
| **Workspace context** | Inject workspace-aware instructions into the Hermes session via `.hermes.md` generation |

### Nice to Have (UX Enhancements)

| Feature | Description |
|:---|:---|
| **`/wright status`** | Show active workspace, enabled tools, credential health |
| **`/wright catalog [domain]`** | Browse available engineering tools by domain |
| **`/wright install <id>`** | Install a tool from the catalog |
| **Dependency checks** | When installing from catalog, verify system dependencies (e.g., `freecad` on `$PATH`) |

### What the Plugin Does NOT Do

| Responsibility | Why Not |
|:---|:---|
| ~~Manage `config.yaml` with 30 MCP servers~~ | Gateway proxy pattern — Hermes only needs `wrightgateway` |
| ~~Budget enforcement (MAX_ACTIVE_SERVERS)~~ | Users explicitly choose tools per workspace |
| ~~Credential prompting in Hermes~~ | Wright UI handles this; credentials are stored in `mcp-secrets.json` |
| ~~MCP reload / `/reload-mcp`~~ | Gateway SSE `list_changed` notification handles this automatically |
| ~~Tool activation/deactivation~~ | Wright API `POST /api/workspace/tools/toggle` handles this |

---

## 4. Architecture Overview

```
                    ┌───────────────────────────────────────┐
                    │  Wright Web UI (React, port 5173/prod)│
                    │  Workspace Dashboard, Tool Cards,     │
                    │  Credential Setup, Chat Composer      │
                    └──────────────┬────────────────────────┘
                                   │ HTTP
                                   ▼
┌─────────────────────────────────────────────────────────────────┐
│  Wright FastAPI Server (port 8000)                               │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │ /api/mcp/*        Server CRUD, install, creds, tools     │   │
│  │ /api/workspace/*  Workspace CRUD, tool toggle            │   │
│  │ /api/gateway/*    Proxy to MCP runners + SSE events      │   │
│  │ /api/agent/*      Chat session management                │   │
│  └──────────────────────────────────────────────────────────┘   │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │ McpEngine → StdioRunner / SseRunner / WebMCP connections │   │
│  │ Secrets Store (mcp-secrets.json)                          │   │
│  │ SQLite DB (mcp_servers, mcp_tools, engineering_workspaces)│   │
│  └──────────────────────────────────────────────────────────┘   │
│                           ▲                                      │
│                           │ HTTP                                 │
│  ┌────────────────────────┴───────────────────────────────────┐ │
│  │ wright-gateway (stdio bridge, single MCP server)           │ │
│  │ Proxies tools/list and tools/call to FastAPI backend       │ │
│  │ SSE listener → forwards list_changed to Hermes             │ │
│  └────────────────────────────────────────────────────────────┘ │
│                           ▲                                      │
│                           │ stdio (JSON-RPC)                     │
│  ┌────────────────────────┴───────────────────────────────────┐ │
│  │ Hermes Agent Runtime                                       │ │
│  │  ┌──────────────────────────────────────────────────────┐  │ │
│  │  │ Wright Plugin                                        │  │ │
│  │  │  • catalog.yaml (30 entries, metadata only)          │  │ │
│  │  │  • /wright commands (status, catalog, install)       │  │ │
│  │  │  • bridge.py → HTTP calls to Wright API              │  │ │
│  │  └──────────────────────────────────────────────────────┘  │ │
│  └────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
```

### Key Interaction Patterns

**User managing tools (via Wright UI):**
```
Wright Web UI → POST /api/mcp/servers/{id}/install
  └→ FastAPI writes to SQLite mcp_servers table
       └→ McpEngine.start_server() discovers tools
            └→ User toggles in workspace tools panel
                 └→ POST /api/workspace/tools/toggle
                      └→ notify_gateway_tool_change()
                           └→ SSE "list_changed" → Hermes refreshes tools
```

**User installing via Hermes plugin:**
```
Hermes "/wright install freecad-mcp"
  └→ Plugin bridge.py → POST http://localhost:8000/api/mcp/servers
       └→ FastAPI registers in DB (same as UI flow above)
            └→ User enables via Wright UI workspace tools panel
                 └→ Same flow as above
```

**User sending a chat message:**
```
Wright Web UI → POST /api/agent/chat
  └→ FastAPI → HermesAdapter.stream_chat()
       └→ Hermes /v1/chat/completions (with session_id)
            └→ Agent uses tools via wright-gateway stdio bridge
                 └→ gateway.py → POST /api/gateway/call
                      └→ McpEngine.call_tool() → runner.call_tool()
```

---

## 5. Plugin Structure & File Layout

### 5.1 Directory-Based Plugin (for `~/.hermes/plugins/` or Docker bake-in)

```text
hermes-plugin-wright/
├── plugin.yaml              # Plugin metadata manifest
├── __init__.py              # Registration entry point: register(ctx)
├── catalog.yaml             # ~30 engineering MCP server entries (metadata only)
├── catalog.py               # Catalog loader, query engine, domain filtering
├── commands.py              # /wright slash command handlers
├── bridge.py                # Wright API client (HTTP calls to localhost:8000)
├── schemas.py               # Pydantic models for catalog entries
├── tests/
│   ├── test_catalog.py      # Catalog loading, filtering, validation
│   ├── test_bridge.py       # API client tests (mocked HTTP)
│   └── test_commands.py     # Slash command integration tests
└── README.md                # User-facing documentation
```

### 5.2 `plugin.yaml`

```yaml
name: wright-engineering-catalog
version: "1.0.0"
description: >
  Curated catalog of ~30 engineering MCP servers for CAD, FEA, CAM,
  and simulation. Bridges Hermes to Wright's tool management system.
  Browse by engineering domain, install on demand.
author: Wright Project (github.com/burhop/wright)
license: MIT
homepage: https://github.com/burhop/wright
capabilities:
  - commands
min_hermes_version: "1.0.0"
```

### 5.3 `__init__.py` — Registration Entry Point

```python
"""Wright Engineering Catalog — Hermes Plugin Registration."""
from .catalog import load_catalog
from .commands import register_commands


def register(ctx):
    """Main plugin entry point called by Hermes PluginManager."""
    catalog = load_catalog()
    register_commands(ctx, catalog)
```

---

## 6. Catalog System

### 6.1 Purpose

The catalog is a **data file** describing engineering MCP servers that can be installed into Wright's tool registry. It does **not** activate anything — it provides browseable metadata so users (or the agent) can discover what's available.

### 6.2 `catalog.yaml` Schema

Each catalog entry describes one installable MCP server:

```yaml
servers:
  # ─── Open Source Geometry Engines ───────────────────────
  - id: freecad-mcp-sandraschi
    name: "FreeCAD Engineering"
    vendor: sandraschi
    description: >
      End-to-end engineering: FreeCAD geometry → CalculiX FEA →
      OpenFOAM CFD → PrusaSlicer G-code.
    domains: [cad, fea, cfd, cam]
    tags: [open-source, linux, headless]
    transport: stdio
    command: ["uv", "run", "--with", "freecad-mcp", "freecad-mcp"]
    source_url: https://github.com/sandraschi/freecad-mcp
    image_url: https://raw.githubusercontent.com/sandraschi/freecad-mcp/main/icon.png
    locality: local
    weight: heavy
    env_vars: []
    dependencies:
      system: [freecad]
      python: []
      node: []

  - id: jarvis-onshape-mcp
    name: "Jarvis OnShape MCP"
    vendor: ReshefElisha
    description: >
      AI copilot for Onshape CAD. 60+ tools: parametric sketches,
      extrudes, fillets, assemblies, Variable Studios, FeatureScript,
      and multi-view rendering with vision feedback.
    domains: [cad, cloud-cad]
    tags: [startup, cloud, rest-api]
    transport: stdio
    command: ["uv", "run", "--with", "jarvis-onshape-mcp", "onshape-mcp"]
    source_url: https://github.com/ReshefElisha/jarvis-onshape-mcp
    image_url: https://avatars.githubusercontent.com/u/6536550?s=64
    locality: remote
    weight: light
    env_vars:
      - name: ONSHAPE_API_KEY
        label: "Access Key"
        description: "Onshape API access key from dev-portal.onshape.com"
        required: true
        secret: false
      - name: ONSHAPE_API_SECRET
        label: "Secret Key"
        description: "Onshape API secret key (shown once at creation)"
        required: true
        secret: true
    dependencies:
      system: []
      python: [jarvis-onshape-mcp]
      node: []

  # ... (remaining ~28 entries follow the same schema)
```

### 6.3 Catalog Entry Schema (Pydantic)

```python
# schemas.py
from pydantic import BaseModel
from typing import Optional


class EnvVarDefinition(BaseModel):
    name: str
    label: str
    description: str = ""
    required: bool = True
    secret: bool = False


class DependencySpec(BaseModel):
    system: list[str] = []
    python: list[str] = []
    node: list[str] = []


class CatalogEntry(BaseModel):
    id: str
    name: str
    vendor: str
    description: str
    domains: list[str]
    tags: list[str] = []
    transport: str             # stdio | sse | webmcp
    command: list[str]
    url: Optional[str] = None  # For SSE/remote servers
    source_url: Optional[str] = None
    image_url: Optional[str] = None
    locality: str = "local"    # local | remote
    weight: str = "medium"     # light | medium | heavy
    env_vars: list[EnvVarDefinition] = []
    dependencies: DependencySpec = DependencySpec()
```

> **Note**: The `EnvVarDefinition` schema matches the existing `tool_registry.models.EnvVarDefinition` exactly. This is intentional — catalog entries should be directly insertable into the Wright DB.

### 6.4 Domain Taxonomy

| Domain Tag | Description | Example Servers |
|:---|:---|:---|
| `cad` | 3D parametric modeling | FreeCAD, Fusion 360, SolidWorks MCP |
| `code-cad` | Procedural/scripted geometry | OpenSCAD, Zoo.dev |
| `cloud-cad` | Cloud-native CAD platforms | Onshape, APS |
| `fea` | Finite Element Analysis | CalculiX, ANSYS bridges |
| `cfd` | Computational Fluid Dynamics | OpenFOAM, FluidX3D |
| `cam` | Computer-Aided Manufacturing | Fusion 360 CAM, PrusaSlicer |
| `plm` | Product Lifecycle Management | APS, ThingWorx |
| `bim` | Building Information Modeling | Revit MCP |
| `eda` | Electronic Design Automation | Siemens Fuse EDA |
| `thermal` | Thermal analysis | (future entries) |
| `tolerance` | Tolerance stackup analysis | (future entries) |
| `drafting` | 2D CAD / AutoLISP | AutoCAD MCP, multiCAD |
| `mesh` | 3D mesh / surface modeling | Blender, Rhino, SketchUp |
| `iot` | IoT / SCADA telemetry | WinCC Unified, ThingWorx |

---

## 7. Gateway Bridge — The Core Mechanism

### 7.1 The Plugin Does NOT Manage MCP Servers Directly

This is the most critical architectural constraint. The plugin communicates with the **Wright FastAPI backend** via HTTP, not with MCP servers directly.

```python
# bridge.py
import httpx

WRIGHT_API_BASE = "http://127.0.0.1:8000"


async def install_tool_from_catalog(entry: "CatalogEntry") -> dict:
    """Install a catalog entry into Wright's tool registry via the API."""
    async with httpx.AsyncClient(timeout=30.0) as client:
        payload = {
            "name": entry.name,
            "type": entry.transport,
            "command": entry.command,
            "category": entry.domains[0] if entry.domains else "utilities",
            "image_url": entry.image_url,
            "description": entry.description,
            "source_url": entry.source_url,
            "env_vars": [v.model_dump() for v in entry.env_vars] if entry.env_vars else None,
        }
        r = await client.post(f"{WRIGHT_API_BASE}/api/tools/install", json=payload)
        r.raise_for_status()
        return r.json()


async def get_wright_status() -> dict:
    """Query Wright API for current workspace and tool status."""
    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            # Get workspace info
            r = await client.get(f"{WRIGHT_API_BASE}/api/workspace/recent")
            workspaces = r.json().get("workspaces", [])

            # Get installed tools
            r2 = await client.get(f"{WRIGHT_API_BASE}/api/tools")
            tools = r2.json()

            return {
                "connected": True,
                "workspaces": workspaces,
                "installed_tools": tools,
            }
        except Exception as e:
            return {"connected": False, "error": str(e)}
```

### 7.2 Why This Works

The gateway proxy pattern means:

1. **No MCP server process management in the plugin** — Wright's `McpEngine` handles all stdio/sse runners
2. **No config.yaml juggling** — only `wrightgateway` is ever in Hermes config
3. **No credential prompting** — Wright UI handles it, plugin just checks status
4. **Live tool updates** — when the user toggles tools in Wright, Hermes sees the change immediately via the SSE `list_changed` notification

---

## 8. Workspace Context Injection

### 8.1 `.hermes.md` — Already Implemented

Wright already writes a `.hermes.md` file to each workspace directory with instructions for the agent. This is handled by `write_workspace_hermes_md()` in [workspace.py](file:///home/burhop/repos/wright/packages/core/src/core/workspace.py).

The plugin's role is to ensure this file is up-to-date when a workspace is activated and to add any catalog-aware context if needed.

### 8.2 Session Workspace Prefix

The Hermes adapter already prefixes user messages with workspace context:

```python
# From hermes.py adapter
message_content = f"[Workspace::v1: {workspace_path}] {message_content}"
```

This means the agent already knows which workspace directory is active. The plugin doesn't need to duplicate this.

---

## 9. Slash Commands — User-Facing Surface

The `/wright` command is both a **launcher** and a **management surface**. It can start
the Wright stack, open the UI, browse the catalog, and install tools — all from within Hermes.

### 9.1 Command Reference

| Command | Description | Example |
|:---|:---|:---|
| `/wright` or `/wright status` | Check Wright API health, show workspace + enabled tools | `/wright status` |
| `/wright start` | **Build frontend → start FastAPI server → open browser** | `/wright start` |
| `/wright stop` | Gracefully shut down the FastAPI server | `/wright stop` |
| `/wright open` | Open Wright UI in default browser (assumes server running) | `/wright open` |
| `/wright doctor` | Full health check: API, Hermes gateway, DB, credentials | `/wright doctor` |
| `/wright catalog [domain]` | Browse available engineering tools from the catalog | `/wright catalog cad` |
| `/wright catalog search <query>` | Free-text search across the catalog | `/wright catalog search tolerance` |
| `/wright info <id>` | Show detailed info for a specific catalog entry | `/wright info jarvis-onshape-mcp` |
| `/wright install <id>` | Install a catalog entry into Wright's tool registry | `/wright install openscad-mcp` |

### 9.2 Repo Path Detection

The plugin auto-detects the Wright repo path from the Hermes `config.yaml` `wrightgateway`
entry. The `hermes_sync.py` service writes this on every startup:

```yaml
# ~/.hermes/profiles/wright/config.yaml (written by hermes_sync.py)
mcp_servers:
  wrightgateway:
    command: uv
    args: [run, --project, /home/burhop/repos/wright, python, -m, tool_registry.gateway]
```

```python
# bridge.py — repo path detection
import os
import yaml

WRIGHT_API_BASE = "http://127.0.0.1:8000"
WRIGHT_UI_URL = "http://localhost:8000"  # Single port — frontend served by FastAPI

def detect_repo_dir() -> str | None:
    """Auto-detect the Wright repo directory from Hermes config.yaml."""
    config_paths = [
        os.path.expanduser("~/.hermes/profiles/wright/config.yaml"),
        os.path.expanduser("~/.hermes/config.yaml"),
    ]
    for path in config_paths:
        if not os.path.exists(path):
            continue
        try:
            with open(path, "r") as f:
                config = yaml.safe_load(f) or {}
            mcp_servers = config.get("mcp_servers", {})
            gateway = mcp_servers.get("wrightgateway", {})
            args = gateway.get("args", [])
            # Find --project flag value
            for i, arg in enumerate(args):
                if arg == "--project" and i + 1 < len(args):
                    return args[i + 1]
        except Exception:
            continue
    return None
```

### 9.3 `/wright start` — Build, Launch, and Open

This is the primary command. It ensures the Wright stack is fully operational
from a single command inside Hermes. Dev and prod work identically — the frontend
is always built and served by FastAPI on port 8000.

```python
# commands.py — /wright start handler
import asyncio
import subprocess
import sys
import webbrowser

import httpx

from .bridge import detect_repo_dir, WRIGHT_API_BASE, WRIGHT_UI_URL


async def is_api_healthy() -> bool:
    """Quick health check against the Wright FastAPI server."""
    try:
        async with httpx.AsyncClient(timeout=3.0) as client:
            r = await client.get(f"{WRIGHT_API_BASE}/api/health")
            return r.status_code == 200
    except Exception:
        return False


async def handle_start() -> str:
    """Build frontend, start FastAPI, open browser."""
    
    # 1. Already running?
    if await is_api_healthy():
        webbrowser.open(WRIGHT_UI_URL)
        return (
            "✅ Wright is already running at http://localhost:8000\n"
            "   Browser opened."
        )
    
    # 2. Find repo
    repo_dir = detect_repo_dir()
    if not repo_dir:
        return (
            "❌ Could not find the Wright repo.\n"
            "   Clone it first:\n"
            "   git clone https://github.com/burhop/wright.git\n"
            "   Then run: /wright start"
        )
    
    # 3. Build frontend (npm run build in apps/web)
    web_dir = os.path.join(repo_dir, "apps", "web")
    dist_dir = os.path.join(web_dir, "dist")
    
    # Only rebuild if dist/ is missing or stale
    needs_build = not os.path.exists(dist_dir)
    if not needs_build:
        # Check if source is newer than dist
        src_mtime = _newest_mtime(os.path.join(web_dir, "src"))
        dist_mtime = os.path.getmtime(dist_dir)
        needs_build = src_mtime > dist_mtime
    
    if needs_build:
        yield "⏳ Building Wright UI..."
        
        # Ensure node_modules exist
        if not os.path.exists(os.path.join(web_dir, "node_modules")):
            proc = subprocess.run(
                ["npm", "install"],
                cwd=web_dir,
                capture_output=True, text=True, timeout=120
            )
            if proc.returncode != 0:
                return f"❌ npm install failed:\n{proc.stderr[:500]}"
        
        proc = subprocess.run(
            ["npm", "run", "build"],
            cwd=web_dir,
            capture_output=True, text=True, timeout=120
        )
        if proc.returncode != 0:
            return f"❌ Frontend build failed:\n{proc.stderr[:500]}"
        yield "✅ Frontend built."
    
    # 4. Start FastAPI server (detached background process)
    log_dir = os.path.join(repo_dir, "tmp")
    os.makedirs(log_dir, exist_ok=True)
    log_path = os.path.join(log_dir, "wright-api.log")
    
    env = os.environ.copy()
    env["FRONTEND_DIST_DIR"] = dist_dir
    
    server_proc = subprocess.Popen(
        [
            sys.executable, "-m", "uvicorn",
            "api.main:app",
            "--host", "127.0.0.1",
            "--port", "8000",
        ],
        cwd=repo_dir,
        env=env,
        stdout=open(log_path, "a"),
        stderr=subprocess.STDOUT,
        start_new_session=True,  # Detach from Hermes process tree
    )
    
    # 5. Wait for health check (up to 15 seconds)
    yield "⏳ Starting Wright API server..."
    for attempt in range(15):
        if await is_api_healthy():
            break
        if server_proc.poll() is not None:
            return f"❌ Server process exited with code {server_proc.returncode}\n   Check logs: {log_path}"
        await asyncio.sleep(1)
    else:
        return f"❌ Server did not become healthy within 15 seconds.\n   Check logs: {log_path}"
    
    # 6. Open browser
    webbrowser.open(WRIGHT_UI_URL)
    
    # 7. Write PID file for /wright stop
    pid_path = os.path.join(log_dir, "wright-api.pid")
    with open(pid_path, "w") as f:
        f.write(str(server_proc.pid))
    
    return (
        "🚀 Wright is running!\n\n"
        f"   API:     http://localhost:8000\n"
        f"   UI:      http://localhost:8000 (browser opened)\n"
        f"   Logs:    {log_path}\n"
        f"   PID:     {server_proc.pid}\n\n"
        "   Use `/wright stop` to shut down."
    )


def _newest_mtime(directory: str) -> float:
    """Find the newest file modification time under a directory."""
    newest = 0.0
    for root, _, files in os.walk(directory):
        for f in files:
            try:
                t = os.path.getmtime(os.path.join(root, f))
                if t > newest:
                    newest = t
            except OSError:
                pass
    return newest
```

### 9.4 `/wright stop` — Graceful Shutdown

```python
# commands.py — /wright stop handler
import signal

async def handle_stop() -> str:
    """Stop the Wright FastAPI server."""
    repo_dir = detect_repo_dir()
    if not repo_dir:
        return "❌ Could not find the Wright repo."
    
    pid_path = os.path.join(repo_dir, "tmp", "wright-api.pid")
    if not os.path.exists(pid_path):
        # Check if server is even running
        if not await is_api_healthy():
            return "ℹ️ Wright is not running."
        return "⚠️ Wright is running but no PID file found. Stop it manually."
    
    try:
        with open(pid_path, "r") as f:
            pid = int(f.read().strip())
        
        os.kill(pid, signal.SIGTERM)
        
        # Wait for process to exit (up to 5 seconds)
        for _ in range(10):
            try:
                os.kill(pid, 0)  # Check if still alive
                await asyncio.sleep(0.5)
            except ProcessLookupError:
                break
        
        os.remove(pid_path)
        return "✅ Wright server stopped."
    except ProcessLookupError:
        os.remove(pid_path)
        return "ℹ️ Wright server was already stopped (stale PID file cleaned up)."
    except Exception as e:
        return f"❌ Failed to stop Wright: {e}"
```

### 9.5 `/wright open` — Open Browser

```python
async def handle_open() -> str:
    """Open the Wright UI in the default browser."""
    if not await is_api_healthy():
        return (
            "❌ Wright is not running.\n"
            "   Use `/wright start` to launch it first."
        )
    webbrowser.open(WRIGHT_UI_URL)
    return "🌐 Opened Wright UI at http://localhost:8000"
```

### 9.6 `/wright doctor` — Full Health Check

```python
async def handle_doctor() -> str:
    """Run a full health check of the Wright stack."""
    lines = ["🩺 Wright Doctor\n"]
    
    # 1. Repo detection
    repo_dir = detect_repo_dir()
    if repo_dir:
        lines.append(f"  ✅ Repo found:     {repo_dir}")
    else:
        lines.append("  ❌ Repo not found — clone https://github.com/burhop/wright.git")
        return "\n".join(lines)
    
    # 2. FastAPI server
    if await is_api_healthy():
        lines.append("  ✅ API server:     http://localhost:8000 (healthy)")
    else:
        lines.append("  ❌ API server:     not running — use /wright start")
    
    # 3. Frontend build
    dist_dir = os.path.join(repo_dir, "apps", "web", "dist")
    if os.path.exists(dist_dir):
        lines.append(f"  ✅ Frontend build: {dist_dir}")
    else:
        lines.append("  ⚠️ Frontend build: missing — /wright start will build it")
    
    # 4. Database
    db_paths = [
        os.path.expanduser("~/.config/wright/wright.db"),
        os.path.join(repo_dir, "wright.db"),
    ]
    db_found = any(os.path.exists(p) for p in db_paths)
    if db_found:
        lines.append("  ✅ Database:       exists")
    else:
        lines.append("  ⚠️ Database:       not yet created (will be created on first API start)")
    
    # 5. Credentials store
    secrets_path = os.path.expanduser("~/.config/wright/mcp-secrets.json")
    if os.path.exists(secrets_path):
        perms = oct(os.stat(secrets_path).st_mode)[-3:]
        if perms == "600":
            lines.append(f"  ✅ Secrets store:  {secrets_path} (mode 0600)")
        else:
            lines.append(f"  ⚠️ Secrets store:  {secrets_path} (mode 0{perms} — should be 0600)")
    else:
        lines.append("  ℹ️ Secrets store:  not yet created (created on first credential save)")
    
    # 6. Tool status (if API is up)
    if await is_api_healthy():
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                r = await client.get(f"{WRIGHT_API_BASE}/api/mcp/servers")
                servers = r.json().get("servers", [])
                installed = [s for s in servers if s.get("is_installed")]
                active = [s for s in servers if s.get("is_active")]
                lines.append(f"  ✅ MCP servers:    {len(installed)} installed, {len(active)} active")
                
                # Check for credential issues
                cred_issues = []
                for s in installed:
                    creds = s.get("credentials_configured", {})
                    missing = [k for k, v in creds.items() if not v]
                    if missing:
                        cred_issues.append(f"     ⚠️ {s['name']}: missing {', '.join(missing)}")
                if cred_issues:
                    lines.append("  ⚠️ Credentials:")
                    lines.extend(cred_issues)
        except Exception:
            lines.append("  ⚠️ MCP servers:    could not query")
    
    return "\n".join(lines)
```

### 9.7 Command Router

```python
# commands.py — main router
def register_commands(ctx, catalog):
    """Register /wright slash commands with Hermes."""

    async def handle_wright(raw_args: str, **kwargs):
        args = raw_args.strip().split()
        subcommand = args[0] if args else "status"

        if subcommand == "start":
            return await handle_start()
        elif subcommand == "stop":
            return await handle_stop()
        elif subcommand == "open":
            return await handle_open()
        elif subcommand == "doctor":
            return await handle_doctor()
        elif subcommand == "status":
            return await format_status()
        elif subcommand == "catalog":
            if len(args) > 1 and args[1] == "search":
                query = " ".join(args[2:])
                return format_search(catalog, query)
            domain = args[1] if len(args) > 1 else None
            return format_browse(catalog, domain_filter=domain)
        elif subcommand == "info":
            entry_id = args[1] if len(args) > 1 else None
            return format_info(catalog, entry_id)
        elif subcommand == "install":
            entry_id = args[1] if len(args) > 1 else None
            return await install_from_catalog(catalog, entry_id)
        else:
            return WRIGHT_HELP_TEXT

    ctx.register_command(
        name="wright",
        handler=handle_wright,
        description="Wright engineering platform: start, stop, open UI, browse catalog, install tools.",
        args_hint="<subcommand> [args...]"
    )

WRIGHT_HELP_TEXT = """🔧 Wright Engineering Platform

Usage: /wright <command>

  Launcher:
    start              Build frontend, start API server, open browser
    stop               Stop the API server
    open               Open Wright UI in browser
    doctor             Full health check of the Wright stack

  Catalog:
    catalog [domain]   Browse engineering tools (cad, fea, cfd, cam, ...)
    catalog search Q   Search the catalog
    info <id>          Show details for a catalog entry
    install <id>       Register a catalog entry in Wright

  Status:
    status             Show Wright connection, workspace, enabled tools

Repo: https://github.com/burhop/wright
"""
```

### 9.8 Output Formatting

Example `/wright status` output:

```
🔧 Wright Engineering Platform

  Connection:  ● Connected (http://127.0.0.1:8000)
  Workspace:   Gearbox Assembly (/home/user/wright/gearbox)

  Active Tools:
    ● FreeCAD Engineering     (cad, fea, cfd)     22 tools
    ● OpenSCAD MCP            (code-cad)           8 tools
    ○ Jarvis OnShape MCP      (cloud-cad)          needs credentials

  Manage tools: /wright open → Workspace → Tools Panel
```

Example `/wright catalog cad` output:

```
🔧 Engineering Tools Catalog — CAD

  ID                        Name                          Locality    Weight
  ─────────────────────────────────────────────────────────────────────────
  freecad-mcp-sandraschi    FreeCAD Engineering           local       heavy
  jarvis-onshape-mcp        Jarvis OnShape MCP            remote      light
  openscad-mcp              OpenSCAD MCP                  local       medium
  fusion360-mcp             Fusion 360 MCP                local       medium
  zoo-mcp                   Zoo.dev Cloud CAD             remote      light

  Use `/wright install <id>` to add a tool   |   `/wright info <id>` for details
```

Example `/wright doctor` output:

```
🩺 Wright Doctor

  ✅ Repo found:     /home/burhop/repos/wright
  ✅ API server:     http://localhost:8000 (healthy)
  ✅ Frontend build: /home/burhop/repos/wright/apps/web/dist
  ✅ Database:       exists
  ✅ Secrets store:  ~/.config/wright/mcp-secrets.json (mode 0600)
  ✅ MCP servers:    4 installed, 2 active
  ⚠️ Credentials:
     ⚠️ Jarvis OnShape MCP: missing ONSHAPE_API_KEY, ONSHAPE_API_SECRET
```

---

## 10. Credential Management — Already Solved

The plugin does **not** implement its own credential management. Wright's existing system handles everything:

| Step | Who Handles It | How |
|:---|:---|:---|
| Declaring required env vars | Catalog entry `env_vars` field + `McpServer.env_vars` in DB | `EnvVarDefinition` model |
| Prompting the user | Wright UI (MCP settings panel) | `POST /api/tools/{id}/credentials` |
| Storing secrets | `tool_registry.secrets.write_secrets()` | `~/.config/wright/mcp-secrets.json` (0600) |
| Injecting at runtime | `McpEngine.start_server()` reads from secrets store | Env vars passed to `StdioRunner` |
| Checking status | `has_credentials()` → `credentials_configured` on API response | UI shows ● / ○ status |

The plugin can **check** credential status (to display in `/wright status`) but should direct users to the Wright UI to configure them:

```
⚠️ Jarvis OnShape MCP requires credentials:
   • Access Key (ONSHAPE_API_KEY) — not configured
   • Secret Key (ONSHAPE_API_SECRET) — not configured

   Configure via Wright UI → Tools → Jarvis OnShape MCP → Settings
```

---

## 11. Distribution Strategy

### 11.1 Three Distribution Paths

```
                    ┌──────────────────────────────┐
                    │    hermes-plugin-wright       │
                    │    (source repository)        │
                    └─────────────┬────────────────┘
                                  │
                ┌─────────────────┼─────────────────┐
                ▼                 ▼                  ▼
    ┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐
    │   pip install    │ │  Copy to        │ │  Docker image   │
    │   hermes-plugin- │ │  ~/.hermes/     │ │  layer          │
    │   wright         │ │  plugins/wright │ │  (baked in)     │
    └─────────────────┘ └─────────────────┘ └─────────────────┘
    Auto-discovered       Manual install     Pre-provisioned
    via entry point       for development    for appliance
```

### 11.2 PyPI Distribution

```toml
# pyproject.toml
[project]
name = "hermes-plugin-wright"
version = "1.0.0"
description = "Wright engineering MCP catalog for Hermes Agent"
authors = [{name = "Wright Project", email = "wright@example.com"}]
license = {text = "MIT"}
requires-python = ">=3.11"
dependencies = [
    "pyyaml>=6.0",
    "pydantic>=2.0",
    "httpx>=0.27",
]

[project.entry-points."hermes_agent.plugins"]
wright = "hermes_plugin_wright:register"

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"
```

### 11.3 Git Clone Install

```bash
# For development or manual installation
git clone https://github.com/burhop/hermes-plugin-wright.git
cp -r hermes-plugin-wright ~/.hermes/plugins/wright
# Restart Hermes or run /reload-skills
```

---

## 12. Docker Appliance Integration

### 12.1 Image Build Strategy

In the Docker appliance, the plugin is baked into the image alongside the Wright API. The gateway is already configured by `hermes_sync.py` on startup.

```dockerfile
# In docker/Dockerfile (Wright production image)
FROM wright-base:latest

# ── Install the Wright Hermes plugin ───────────────────────
COPY hermes-plugin-wright/ /opt/hermes-plugins/wright/
```

### 12.2 Blank Slate Provisioning

The Docker appliance starts from Blank Slate. The entrypoint must ensure:

1. Hermes config has the `wrightgateway` MCP server entry (handled by `hermes_sync.py`)
2. Plugin directory is discoverable (either via `~/.hermes/plugins/wright/` symlink or entry point)
3. All Hermes config commands run as the `agent` user (not root) to avoid the root-ownership bug

```bash
# docker/entrypoint.sh — run during first-boot provisioning
# Run as agent user to avoid root-ownership of config.yaml
su - agent -c "hermes config set platform_toolsets.cli '[\"file\", \"terminal\", \"plugins\", \"mcp\"]'"
```

### 12.3 Volume Mapping

Following the existing Docker architecture:

| Data | Location | Volume |
|:---|:---|:---|
| Plugin code | `/opt/hermes-plugins/wright/` | `wright_opt` (persisted) |
| Hermes config | `~/.hermes/config.yaml` | `wright_home` (persisted) |
| Wright DB | SQLite (managed by Wright API) | `wright_data` (persisted) |
| Credentials | `~/.config/wright/mcp-secrets.json` | `wright_home` (persisted) |

---

## 13. Existing-Install Integration

### 13.1 For Users With an Existing Hermes Installation

```bash
# Option A: pip install (recommended)
pip install hermes-plugin-wright
# Hermes auto-discovers via entry point on next startup

# Option B: git clone
git clone https://github.com/burhop/hermes-plugin-wright.git ~/.hermes/plugins/wright

# Enable the plugin
hermes plugins enable wright

# Verify
hermes doctor  # Should show wright plugin as loaded
```

### 13.2 Prerequisites

The plugin requires the Wright API to be running at `http://127.0.0.1:8000`. If Wright isn't running, the plugin gracefully degrades:
- `/wright status` shows "disconnected"
- `/wright catalog` still works (catalog is bundled, not fetched from API)
- `/wright install` fails with a clear error message

---

## 14. Security Considerations

### 14.1 Secret Handling (Already Enforced)

| Rule | Implementation |
|:---|:---|
| Secrets never in version control | `.gitignore`; no defaults in catalog |
| Secrets never in Docker images | Prompted at runtime; stored in mounted volumes |
| Secrets never logged | structlog sanitization in `tool_registry.secrets` |
| Secrets never in API responses | Wright API masks credential values |
| File permissions locked | `0600` on `mcp-secrets.json`; `fcntl` locking |

### 14.2 Plugin Safety

| Risk | Mitigation |
|:---|:---|
| Plugin calls unauthorized API endpoints | Plugin only calls documented Wright API routes |
| Catalog entries point to malicious repos | Catalog is curated; source URLs are auditable |
| Wright API not running | Plugin degrades gracefully; catalog browse still works |

---

## 15. Testing & Validation Strategy

### 15.1 Unit Tests

```bash
cd hermes-plugin-wright
pytest tests/ -v
```

| Test Suite | What It Validates |
|:---|:---|
| `test_catalog.py` | YAML loading, schema validation, domain filtering, search |
| `test_bridge.py` | Wright API client (mocked HTTP calls) |
| `test_commands.py` | Slash command parsing, argument validation, output formatting |

### 15.2 Integration Tests

| Test | Description |
|:---|:---|
| Plugin load | Install plugin → `hermes doctor` shows it loaded |
| Catalog browse | `/wright catalog cad` → renders correctly |
| Status check | `/wright status` → shows Wright connection and active tools |
| Install flow | `/wright install openscad-mcp` → tool appears in Wright registry |
| Gateway SSE | Toggle tool in Wright UI → Hermes `tools/list` updates without restart |

### 15.3 Existing Test Coverage

Many of the critical paths are already covered by existing tests:

- [test_mcp_credentials.py](file:///home/burhop/repos/wright/apps/api/tests/test_mcp_credentials.py) — Credential store
- [test_gateway_api.py](file:///home/burhop/repos/wright/apps/api/tests/test_gateway_api.py) — Gateway proxy
- [test_workspace_api.py](file:///home/burhop/repos/wright/apps/api/tests/test_workspace_api.py) — Workspace tool toggles

---

## 16. Submission & Community Sharing

### 16.1 Distribution Channels

1. **PyPI** — Publish as `hermes-plugin-wright`; users install via pip
2. **GitHub** — Tag repository with `hermes-agent`, `hermes-plugin`, `mcp`, `engineering`
3. **Awesome Lists** — Submit to awesome-hermes and awesome-mcp curated lists
4. **NousResearch Discord** — Share in the `#plugins` channel

### 16.2 Plugin Quality Checklist

Before publishing:

- [ ] `plugin.yaml` has all required fields
- [ ] `register(ctx)` is the single entry point
- [ ] All Pydantic schemas validate with strict mode
- [ ] No hardcoded secrets anywhere in the codebase
- [ ] `hermes doctor` shows no errors with plugin installed
- [ ] Unit test coverage ≥ 80%
- [ ] README.md includes installation, usage examples, configuration reference
- [ ] Plugin does not modify global state at import time (only during `register()`)
- [ ] Graceful degradation when Wright API is unavailable

---

## 17. Implementation Phases

### Phase 1 — Plugin Skeleton & Catalog (Week 1-2)

> **Goal**: Working plugin that can browse the catalog inside Hermes.

| Task | Deliverable |
|:---|:---|
| Create plugin directory structure | `hermes-plugin-wright/` with all files |
| Define catalog schema | `schemas.py` with Pydantic models |
| Build initial catalog | `catalog.yaml` with 10 core entries |
| Implement catalog loader | `catalog.py` — load, validate, filter, search |
| Implement `/wright catalog` and `/wright info` | Read-only catalog browsing |
| Write unit tests | `test_catalog.py`, `test_schemas.py` |

### Phase 2 — Wright API Bridge & Status (Week 3-4)

> **Goal**: Plugin connects to Wright API for status and install.

| Task | Deliverable |
|:---|:---|
| Implement `bridge.py` | Wright API HTTP client |
| Implement `/wright status` | Show connection, workspace, enabled tools |
| Implement `/wright install` | Install catalog entry via Wright API |
| Graceful degradation | Offline catalog browse when Wright is down |
| Write tests | `test_bridge.py`, `test_commands.py` |

### Phase 3 — Full Catalog & Docker (Week 5-6)

> **Goal**: Complete catalog, Docker image integration, PyPI packaging.

| Task | Deliverable |
|:---|:---|
| Expand catalog to ~30 entries | Complete `catalog.yaml` |
| Docker image integration | Copy plugin into image, verify on first boot |
| PyPI packaging | `pyproject.toml`, build, publish |
| Documentation | README.md, CONTRIBUTING.md |

### Phase 4 — Polish & Submission (Week 7-8)

> **Goal**: Production-ready, community-shareable plugin.

| Task | Deliverable |
|:---|:---|
| Dependency health checks | Verify system binaries, report missing deps |
| Output formatting polish | Rich markdown for TUI |
| Error handling hardening | Graceful failures, actionable error messages |
| Community submission | PyPI publish, GitHub tags, Discord announcement |

---

## 18. Open Questions & Risks

### 18.1 Open Questions

| # | Question | Impact | Status |
|:---|:---|:---|:---|
| 1 | Should the plugin also be a location for installing MCP servers (via `pip`/`npm`) or should it only register metadata in the DB and let the user handle installation? | Determines whether `/wright install` triggers actual package installation or just DB registration | **Needs Decision** |
| 2 | Should the catalog be synced from a remote URL (e.g., GitHub raw file) or only bundled with the plugin? | Determines update frequency and offline behavior | **Needs Decision** |
| 3 | Should `/wright` commands be available in gateway contexts (Telegram, Discord) or CLI-only? | Affects command registration flags | **Needs Decision** |

### 18.2 Risks

| Risk | Likelihood | Impact | Mitigation |
|:---|:---|:---|:---|
| Wright API not running when plugin loads | Medium | Graceful degradation — catalog browse still works | Check connection lazily, not at registration time |
| Catalog entries go stale (broken URLs, renamed packages) | High | Install fails | CI job to validate catalog entries periodically |
| Hermes plugin API changes break registration | Low | Plugin won't load | Pin `min_hermes_version`, test against releases |
| User installs plugin but doesn't have Wright running | Medium | `/wright status` shows disconnected, install fails | Clear error messages directing to Wright setup docs |

---

## 19. Appendix: Reference Links

### Wright Project — Existing Implementation

| File | Description |
|:---|:---|
| [gateway.py (bridge)](file:///home/burhop/repos/wright/packages/tool_registry/src/tool_registry/gateway.py) | The stdio MCP gateway proxy |
| [gateway.py (API)](file:///home/burhop/repos/wright/apps/api/src/api/routers/gateway.py) | FastAPI router for tool listing and calls |
| [manager.py](file:///home/burhop/repos/wright/packages/tool_registry/src/tool_registry/manager.py) | McpEngine — server lifecycle management |
| [models.py](file:///home/burhop/repos/wright/packages/tool_registry/src/tool_registry/models.py) | McpServer, McpTool, EnvVarDefinition |
| [db.py](file:///home/burhop/repos/wright/packages/tool_registry/src/tool_registry/db.py) | SQLite persistence layer |
| [secrets.py](file:///home/burhop/repos/wright/packages/tool_registry/src/tool_registry/secrets.py) | Credential store (0600, fcntl) |
| [hermes_sync.py](file:///home/burhop/repos/wright/apps/api/src/api/services/hermes_sync.py) | Hermes config.yaml synchronization |
| [hermes.py](file:///home/burhop/repos/wright/packages/agent_adapters/src/agent_adapters/hermes.py) | Hermes agent adapter |
| [workspace.py (core)](file:///home/burhop/repos/wright/packages/core/src/core/workspace.py) | Workspace management, enabled_tools |
| [workspace.py (API)](file:///home/burhop/repos/wright/apps/api/src/api/routers/workspace.py) | Workspace API routes incl. tool toggle |
| [constitution.md](file:///home/burhop/repos/wright/constitution.md) | Project principles |

### External References

- [Hermes Documentation](https://hermes-agent.nousresearch.com/) — Official docs
- [Build a Plugin Guide](https://hermes-agent.nousresearch.com/docs/guides/build-a-plugin) — Plugin development
- [MCP Specification](https://github.com/modelcontextprotocol) — Protocol spec
- [Engineering MCP Tools Discovery](file:///home/burhop/repos/wright/docs/Engineering%20MCP%20Tools%20Discovery.md) — Full research document

---

*This document is the canonical reference for the Wright Hermes Plugin. It accurately reflects the existing Wright architecture and avoids duplicating functionality that is already implemented.*
