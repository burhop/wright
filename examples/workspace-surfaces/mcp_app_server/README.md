# Packaged MCP App reference

This server demonstrates the stable `io.modelcontextprotocol/ui` MCP Apps contract. It publishes `ui://wright.reference/design` by exact `resources/read` (while intentionally omitting it from `resources/list`), provides useful text and structured fallback, permits an app-visible resize tool, and exposes a model-only tool that Wright must deny to the app.

Build the self-contained, offline UI once:

```powershell
cd ui
npm install
npm run build
cd ..
uv run python server.py
```

Configure the last command as a stdio MCP server in Wright and call `show_design`. With MCP Apps enabled, the design appears in Wright's distinct-origin sandbox. With it disabled or if the resource fails validation, the text/structured result remains useful. **Close view** requests teardown; disconnecting the MCP server also removes its authority. No network domains or device permissions are requested.
