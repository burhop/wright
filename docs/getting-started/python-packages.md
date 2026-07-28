# Python Distribution Role

`wright-engineering` is Wright's one public Python distribution. It contains the
thin Hermes entry point, native lifecycle bootstrap, complete packaged API/UI,
canonical MCP catalog, provider-neutral gateway, and a bounded `runtime` extra.

Normal users do not run `pip install` themselves. A released package-capable
Hermes resolves the exact version, installs the base entry point in its managed
environment, and lets `/wright start` install the same exact distribution's
runtime extra into Wright's contained environment.

Manual artifact installation is reserved for release verification and package
diagnosis:

```bash
python -m pip install wright-engineering==<version>
wright --version
wright doctor
```

Internal distributions such as `wright-core`, `wright-tool-registry`,
`wright-data-vault`, `wright-agent-adapters`, `wright-workspace-service`,
`wright-api`, and `hermes-plugin-wright` are private development/migration
surfaces. The public runtime has no dependency on them from an index; their
modules are bundled into the one application wheel.
