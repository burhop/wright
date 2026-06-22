# Data Model: Wright API Bridge Client

This document specifies the payload and response structures for bridge client operations.

## payload Mapping

### 1. Register MCP Server Payload (`McpServerCreate`)
This is the payload sent to `POST /api/mcp/servers`. It maps the catalog entry attributes directly to the FastAPI request body format.

* `name` (string): Human-readable name of the server.
* `type` (string: `stdio`, `sse`, or `webmcp`): Transport type.
* `command` (list[string] or string): Start command.
* `category` (string, default `"utilities"`): Mapped from the first domain tag in catalog entry.
* `image_url` (string, optional): Icon URL.
* `description` (string, optional): Description.
* `source_url` (string, optional): Repository link.
* `env_vars` (list[EnvVarDefinition], optional): List of required environment variables.

---

## Response Mappings

All API client calls wrap their return value in a standardized connection wrapper dictionary to prevent exceptions from bubbling up.

### 1. Standard Success Wrapper
```python
{
    "success": True,
    "data": ... # Response payload parsed from JSON
}
```

### 2. Standard Error Wrapper
```python
{
    "success": False,
    "error": "Error details here"
}
```
