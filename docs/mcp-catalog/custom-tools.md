# Writing Custom MCP Tools

Developers can expand the Wright appliance's capabilities by writing custom Model Context Protocol servers. Wright supports wrapping custom Python scripts or Node.js packages into the registry.

---

## 1. Custom Python Server Example

To build a custom tool, write a server exposing standard JSON-RPC tool schemas.

```python
from mcp.server.fastmcp import FastMCP

# Initialize FastMCP server
mcp = FastMCP("custom-geometry-helper")

@mcp.tool()
def compute_volume(length: float, width: float, height: float) -> str:
    """Compute structural volume of standard box primitives."""
    volume = length * width * height
    return f"Computed volume: {volume:.4f} cubic units."

if __name__ == "__main__":
    mcp.run()
```

---

## 2. Registering with Wright

Once written, register the custom server in the SQLite database via the dashboard UI or API:

```bash
curl -X POST http://localhost:8000/api/tools/install \
  -H "Content-Type: application/json" \
  -d '{
    "name": "custom-geometry-helper",
    "transport": "stdio",
    "command": "python",
    "args": ["/path/to/custom_server.py"]
  }'
```

---

## 3. Destructive Gating annotations

If your custom tool performs irreversible actions (e.g. executing system changes), annotate the schemas with hints to trigger user approval:

```python
# Annotation meta hints
@mcp.tool(meta={"destructiveHint": True})
def erase_part_body(part_id: str) -> str:
    """Delete a CAD body representation from the active workspace."""
    ...
```
