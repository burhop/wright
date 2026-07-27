# Launch Binding Contract

## Trusted Input

The launch renderer accepts:

- a configured command (`str` or `list[str]`),
- a configured non-secret environment map,
- an optional authenticated canonical workspace path.

Only configuration loaded through Wright's administrator-controlled server/catalog APIs or bundled catalog is trusted to contain placeholders. Server-advertised MCP metadata is never evaluated as launch configuration.

## Placeholder Grammar

The only supported placeholder is:

```text
{workspace.path}
```

Rules:

1. Resolve the workspace to an absolute canonical path before rendering.
2. Replace every exact occurrence literally; do not use a shell or general-purpose formatter.
3. Allow replacement inside command-array elements and environment values.
4. Reject a placeholder in a string command because safe argument boundaries cannot be guaranteed.
5. Reject any other `{...}` token with an actionable configuration error.
6. When no placeholder exists, preserve command and environment behavior.
7. Never log unredacted secret-bearing environment values.

## Examples

```yaml
command:
  - example-mcp
  - --allowed-root
  - "{workspace.path}"
launch_env: {}
```

```yaml
command:
  - example-mcp
launch_env:
  EXAMPLE_ALLOWED_ROOTS: "{workspace.path}"
```

The second form keeps a legacy server environment contract in ordinary data without teaching Wright runtime code what the variable means.

## Failure Contract

Invalid configuration fails before subprocess creation with:

- a stable error category (`invalid_launch_template`),
- the server identity,
- the invalid field location,
- a message naming the supported placeholder,
- no rendered secret values.
