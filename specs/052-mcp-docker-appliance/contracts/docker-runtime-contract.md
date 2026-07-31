# Contract: Docker Runtime

The MCP appliance must behave like the standard Wright Docker appliance from the engineer's point of view.

## Standard Access Preservation

- The primary Wright UI/API remains reachable through the same container port used by the standard appliance.
- Existing environment file settings for LLM URL, key, model, and Wright token remain valid unless explicitly documented as MCP-specific additions.
- `WRIGHT_LLM_CONFIG_FILE` may point at a mounted YAML/JSON provider seed file. The image must read it at startup and must not copy that secret file into an image layer.
- `WRIGHT_LLM_PROVIDER`, `WRIGHT_LLM_BASE_URL`, `WRIGHT_LLM_MODEL`, `WRIGHT_LLM_API_KEY`, and `WRIGHT_LLM_AUTH_FILE` are optional startup overrides for disposable test containers.
- The entrypoint continues to bootstrap Hermes profile configuration idempotently.
- Supervisor continues to own Wright API and Hermes gateway processes.

## Isolation

- The MCP compose path uses MCP-specific default volume names.
- The MCP image does not write to host Wright or Hermes paths unless the operator explicitly mounts them.
- The standard Dockerfile and standard compose file continue to work without installing MCP host software.

## Remote Access

- Localhost-only binding remains the safe default.
- Remote/LAN access requires an explicit documented bind choice and token configuration.
- Documentation must warn that LAN access exposes the Wright UI/API to the selected network interface.

## Startup Outcome

On startup, the MCP appliance must report:

- Wright API status
- Hermes gateway status
- MCP bundle manifest identity
- generated runtime config status
- generated application and MCP server statuses
- LLM provider seed status without token or API key values

Startup must not install Solid Edge desktop/vendor assets. SolidEdgeMCP source
installation belongs to the Windows MCP runtime and is controlled by explicit
build arguments there.

If no LLM settings are supplied, startup must continue and report disconnected
inference. It must not write a fake localhost model endpoint into the Wright
Hermes profile.
