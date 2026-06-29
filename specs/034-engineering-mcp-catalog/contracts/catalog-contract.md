# Catalog Contract

## Catalog Entry Shape

Catalog entries exposed by the backend and plugin loader must include:

```json
{
  "server_id": "zoo_cloud_cad_mcp",
  "name": "Zoo.dev Cloud CAD MCP",
  "type": "stdio",
  "command": ["uvx", "zoo-mcp"],
  "category": "code-cad",
  "description": "Cloud CAD modeling and conversion MCP.",
  "source_url": "https://zoo.dev/docs/developer-tools/mcp",
  "verification_state": "verified_mcp",
  "installability_tier": "might_work",
  "risk_level": "medium",
  "default_enabled": false,
  "host_software_required": [],
  "credentials_required": ["ZOO_API_TOKEN"],
  "platform_support": {
    "windows_11_x64": { "status": "likely", "tested": false, "notes": "uvx-supported platform expected" },
    "linux_x64": { "status": "likely", "tested": false, "notes": "first validation target" },
    "linux_arm64": { "status": "unknown", "tested": false, "notes": "not tested" },
    "macos_x64": { "status": "likely", "tested": false, "notes": "uvx-supported platform expected" },
    "macos_arm64": { "status": "likely", "tested": false, "notes": "uvx-supported platform expected" }
  },
  "validation_result": {
    "status": "not_tested",
    "message": "Not yet validated in this environment"
  },
  "follow_up_url": null
}
```

## Rules

- `server_id`, `verification_state`, `installability_tier`, `risk_level`, and all platform keys are required.
- `installability_tier` controls ordering: `tested`, `might_work`, `blocked`, `non_working`.
- `source_url` may be null only for states that explicitly allow missing URLs.
- Entries with missing URL or install evidence must not expose enabled install actions.
- API responses must remain backward-compatible for existing fields used by current UI cards.
