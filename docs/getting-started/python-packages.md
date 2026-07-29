# Python Distribution Role

`wright-engineering` is Wright's one public Python distribution. It contains
the manager-neutral lifecycle, packaged API/UI, canonical MCP catalog,
provider-neutral gateway, direct MCP profile generator, and bounded `runtime`
extra.

The thin Hermes Git adapter installs the exact compatible distribution into
Wright-owned state. Codex users may install it with their normal
Python environment tool or connect to an already running Wright HTTP endpoint.
Manager adapters never contain a second copy of Wright application logic.

Manual artifact installation remains useful for a direct manager environment,
release verification, and package diagnosis:

```bash
python -m pip install 'wright-engineering[runtime]==<version>'
wright --version
wright doctor
```

Internal distributions such as `wright-core`, `wright-tool-registry`,
`wright-data-vault`, `wright-agent-adapters`, `wright-workspace-service`, and
`wright-api` are private development surfaces. The public runtime has no index
dependency on them; their modules are bundled into the application wheel.
