# Wright for Codex

Codex connects directly to Wright's provider-neutral MCP service. Hermes is not
installed or invoked.

Install the released Wright runtime with the Python environment tool used on
your machine, run `wright native start`, then register its STDIO command. STDIO
is the recommended local profile because it reads the owner-only Wright token
from `WRIGHT_HOME` without putting a secret in Codex configuration:

```text
codex mcp add wright --env WRIGHT_HOME=<wright-home> -- wright mcp serve --stdio --workspace <absolute-workspace> --api-url http://127.0.0.1:8000 --session-id <wright-session-id> --workspace-id <wright-workspace-id>
codex mcp get wright
```

For a workspace-specific STDIO connection, generate the exact configuration
with `wright_engineering.manager_profiles.codex_mcp_config`, passing the
`session_id` and `workspace_id` returned by Wright when the workspace was
created. Its command shape is:

```text
wright mcp serve --stdio --workspace <absolute-workspace> --api-url http://127.0.0.1:8000 --session-id <wright-session-id> --workspace-id <wright-workspace-id>
```

Set `WRIGHT_HOME` if you do not want the default `~/.wright`. The STDIO profile
also sets `WRIGHT_MANAGER_ID=codex` and `WRIGHT_MANAGER_PROTOCOL=mcp-v1`.
Codex-owned configuration stays outside `WRIGHT_HOME`; deleting the Codex MCP
entry does not uninstall or purge Wright.

For advanced Streamable HTTP use, configure the same `/mcp` endpoint with
`bearer_token_env_var = "WRIGHT_API_TOKEN"` and inject that environment value
through the local manager process. Do not put the token in a URL, TOML value,
command argument, or log.

Use the checked-in examples under `integrations/codex/` as templates. Public
support is claimed only when the exact Wright runtime and Codex profile pass MCP
initialize, tools/list, and a safe tool call in release evidence.
