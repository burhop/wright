# Wright for Codex

Codex connects directly to Wright's provider-neutral MCP service; Hermes is not
in the path. Install the `wright-engineering` runtime, start Wright, and add the
workspace-specific STDIO profile to Codex configuration. STDIO is the default
because the bridge reads Wright's owner-only installation token directly from
`WRIGHT_HOME`; the token is not copied into Codex configuration.

The checked-in `config.toml.example` uses Codex's documented `command`, `args`,
and `env` fields. Replace the workspace and Wright-home placeholders.

Streamable HTTP is also supported when the manager process receives the token
through an environment variable:

```toml
[mcp_servers.wright]
url = "http://127.0.0.1:8000/mcp"
bearer_token_env_var = "WRIGHT_API_TOKEN"
```

Do not copy the token into TOML, a URL, or a command argument. Generate either
shape with `wright_engineering.manager_profiles.codex_mcp_config`. Both connect
directly to Wright and store lifecycle state only under `WRIGHT_HOME`.

Codex itself is not a Wright runtime dependency.

## Desktop UI integration (candidate qualification)

The maintained desktop composition is opt-in and remains experimental until the
platform acceptance matrix passes. It reuses the normal API, workspace storage,
source editor, gateway and durable run owners. It does not embed a second model
or workflow executor. Confined generated-UI authoring remains gated.

Start an **isolated** native installation with `WRIGHT_DESKTOP_ENABLED=1` in its
server environment. Use `WRIGHT_MCP_OAUTH_FLOW=device_code` when device sign-in is
required; unsupported provider grants remain explicit. The normal local sign-in
default is unchanged. Never copy credentials into a profile. Existing installations
are not enabled merely by installing updated code.

The desktop MCP command is `wright mcp desktop --api-url http://127.0.0.1:8000`.
For a managed installation it uses the selected private runtime environment; a
standalone installation needs the runtime dependencies. It reads authenticated
configuration from the same loopback API and verifies SDK, transport and UI
identities before connecting. It needs no preview server, repository path,
`preview.json`, or `desktop-binding.json` file.

Use `desktop-config.toml.example`, or generate its MCP configuration with
`codex_mcp_config(desktop=True, wright_home=...)`. This profile begins at the
workspace chooser. The existing workspace-specific direct MCP profile is retained.
The desktop conversation supplies reasoning; helpers and recovery use the same
frozen routing contract. A disconnected conversation means waiting/unavailable,
not an automatic fallback to Hermes or another model.

The desktop advertises the content-hashed workflow viewer and thread entrypoint.
Native automatic file-viewer selection has **not** been qualified. The host may
open source text first. Manual selection still requires an authorized saved
workspace file; arbitrary external files do not acquire workspace access.
Conversation-panel rendering and native-file rendering are separate acceptance
rows. No Windows rendering or download claim follows from a successful tool call.

Current scope, evidence and remaining acceptance are tracked in
`docs/design/codex-production-integration/`. Historical prototype scripts delegate
to the maintained implementation for regression compatibility; they are not the
installation path. Their immutable installed snapshots and run evidence remain
unchanged.
