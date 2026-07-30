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
