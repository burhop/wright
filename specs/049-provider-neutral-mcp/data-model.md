# Data Model: Provider-Neutral MCP Integration

## Server Launch Configuration

Represents trusted process configuration for one MCP server.

| Field | Type | Rules |
|---|---|---|
| `command` | string or list of strings | Existing string commands remain supported only when they contain no workspace placeholder. Template-bearing commands must be argument arrays. |
| `launch_env` | map of string to string | Non-secret literal/template values. Defaults to empty. Keys must be valid environment names. |
| `env_vars` | credential definitions or legacy map | Existing secret/config compatibility; secrets continue through the secrets provider. |
| `deployment_mode` | string | Existing provider-neutral ownership/deployment declaration. |
| `operation_timeout` | application setting | Existing positive bounded call timeout. |

### Workspace Placeholder

- Grammar: exact token `{workspace.path}`.
- Source: immutable authenticated gateway workspace binding.
- Rendered value: canonical absolute workspace path.
- Allowed locations: command-array element and `launch_env` value.
- Unknown `{...}` token: configuration error before subprocess creation.
- String command containing a placeholder: configuration error.
- No placeholder: value is preserved exactly.

## Advertised Tool

Represents the cached contract returned by one server's `tools/list`.

| Field | Type | Trust |
|---|---|---|
| `tool_id` | string | Wright identity (`server_id:name`) |
| `server_id` | string | Wright server binding |
| `name` | string | Advertised, namespaced only at the gateway boundary |
| `title` | optional string | Untrusted advertised display metadata |
| `description` | optional string | Untrusted advertised guidance |
| `input_schema` | object | Advertised validation contract |
| `output_schema` | optional object | Advertised result validation contract |
| `annotations` | object | Untrusted standard descriptive hints |
| `is_enabled` | boolean | Trusted user/workspace selection |
| `required_approvals` | derived set | Trusted server/catalog policy; not sourced from annotations |

## Tool Progress Update

Transient request-scoped value; not a new database entity.

| Field | Type | Rules |
|---|---|---|
| `server_id` | optional string | Known from gateway routing when available |
| `tool_name` | string | Advertised or gateway-qualified identity |
| `tool_title` | optional string | Advertised title, sanitized for display |
| `progress` | optional number | Must not decrease for one token |
| `total` | optional number | Must be positive when supplied |
| `message` | optional string | Server-authored, bounded and safe for display |
| `elapsed_seconds` | non-negative number | Calculated by Wright stream projection |
| `correlation_id` | optional string | Existing request/turn identity |
| `status` | enum | `running`, `succeeded`, `failed`, `cancelled`, `timed_out` |
| `heartbeat` | boolean | Wright liveness fallback, not server progress |

### State Transitions

```text
running -> succeeded
running -> failed
running -> cancelled
running -> timed_out
```

Terminal states are final. Updates after terminal are ignored. Numeric child updates are clamped/ignored if they regress; they never reopen a terminal request.

## Relationships

- One server launch configuration is rendered against one immutable workspace binding when its managed process starts.
- One server advertises many tools; a refresh atomically replaces its cached tool rows.
- One active tool request owns at most one child progress token and maps it to at most one outer caller token.
- One chat stream projection contains ordered progress events for one agent session and correlation identity.
