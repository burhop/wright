# Tool Registry & MCP Engine

The **Model Context Protocol (MCP)** is the core interface through which LLMs execute actions in the physical world. Wright features an advanced `McpEngine` that controls the lifecycles, configuration syncs, and JSON-RPC dispatch of multiple concurrent MCP servers.

```
sequenceDiagram
    participant Agent as LLM / Agent Engine
    participant API as FastAPI Router
    participant Engine as McpEngine
    participant Runner as Stdio / SSE Runner
    participant Tool as CAD/FEA Binary

    Agent->>API: Chat Request
    API->>Engine: call_tool(server_id, tool_name, arguments)
    Engine->>Runner: dispatch JSON-RPC Request
    Runner->>Tool: Execute subprocess (e.g., FreeCAD script)
    Tool-->>Runner: Return geometry/stdout
    Runner-->>Engine: JSON-RPC Response
    Engine-->>API: Tool Result Dict
    API-->>Agent: Observe Result (Geometry updated)
```

## Supported Execution Runners

1.  **`stdio`**: Launches local binaries or Python packages as background subprocesses, communicating via JSON-RPC over stdin/stdout pipes.
2.  **`sse`**: Establishes connections to remote web servers hosting specialized tools, using server-sent event streams.
3.  **`webmcp`**: Connects client-side browser DOM actions to the backend via WebSockets. This allows an AI agent to execute commands that manipulate WebGL render canvases, trigger browser downloads, or read highlighted elements in the user's active viewport.

## Dynamic Tool Lifecycle Management

*   **Auto-Installation Discovery**: During database migration and engine startup, the system uses `shutil.which` to scan the host shell `$PATH`. If a tool's executable dependency (e.g., `openscad` or `calculix-mcp`) is present, it automatically toggles the server's `is_installed` status in the SQLite registry.
*   **Workspace-Scoped Tool Syncing**: When a user activates a workspace, the system reads the project's enabled tools list. An asynchronous background task starts the required MCP servers (initiating subprocesses) and shuts down disabled or unneeded runners, optimizing the appliance's local memory footprint.
*   **Agent Server Synchronization**: The system synchronizes the list of active tools into the agent configuration files on disk. The selected LLM is instantly notified of the available tools, enabling zero-latency tool-use transitions.

## Extensible Tool Registry

The primary purpose of the Wright platform is to serve as an **extensible tool registry** that collects, installs, and validates diverse engineering packages, making them programmatically accessible to AI agents.

Because agents operate headlessly without interacting with graphical UIs, all tools integrated into the platform are configured to run via command-line interfaces (CLIs), Python API scripts, local geometry kernels, or direct REST connections. New tools can be wrapped in the `tool_registry` package as MCP servers without requiring changes to the core orchestrator or agent schemas.
