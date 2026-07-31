# Contract: MCP Bundle Manifest

The MCP bundle manifest is the authoritative source for what the MCP appliance installs, exposes, validates, and documents.

## Required Manifest Behavior

- A manifest parse failure stops the MCP image build before dependency installation.
- Any local application or MCP server without an exact source pin, exact package version, or explicit configured source gate stops validation.
- Any local application or MCP server without accepted license/compliance evidence stops validation.
- Generated Hermes config is produced only from `mcp_servers`.
- Applications and MCP servers are modeled separately.

## Required Shape

```yaml
schema_version: 1
bundle_id: wright-mcp-appliance
applications:
  - id: openscad
    display_name: OpenSCAD
    availability: local_enabled
    source:
      type: apt
      packages: [openscad, xvfb]
      license: GPL-2.0-or-later
    compliance_profile:
      id: gpl-2.0-runtime-redistribution
      runtime_use_only: true
      modification_status: unmodified
      source_access: apt source openscad for the installed package
      license_text: /usr/share/common-licenses/GPL-2
      no_warranty_notice: /opt/wright/mcp/generated/licenses/NO-WARRANTY-GPL-2.0.txt
    install: {}
    health_probe: {}
mcp_servers:
  - id: openscad-mcp
    application_id: openscad
    availability: local_enabled
    mcp_source:
      type: git
      url: https://github.com/quellant/openscad-mcp
      ref: d438b84fff8af9d646c2bcb76fe58fa4ad387de0
      license: MIT
    compliance_profile:
      id: permissive
    install: {}
    launch:
      command: [/opt/wright/mcp/bin/openscad-mcp]
    workspace_binding:
      required: true
      env:
        OPENSCAD_WORKSPACE: "{workspace.path}"
    health_probe: {}
```

## Status Semantics

- `local_enabled`: build installs the component and generated config can launch it locally.
- `blocked_pending_review`: build records the component but does not install or launch it.
- `remote_only`: generated status points to external setup requirements.
- `windows_only`: generated status cannot run inside the Linux container.

Generated Hermes config must exclude blocked entries. Linux bundles may keep a
blocked SolidEdgeMCP metadata entry so the platform boundary remains visible.

## License And Compliance Semantics

Default permissive licenses:

- MIT
- Apache-2.0
- BSD-2-Clause
- BSD-3-Clause
- ISC

Supported compliance profiles:

- `permissive`: accepted SPDX expression, copyright notices, license text, and generated notice file
- `gpl-2.0-runtime-redistribution`: GPL-2.0-only or GPL-2.0-or-later component executed as a separate unmodified runtime program, with source access and no-warranty artifacts
- `lgpl-runtime-redistribution`: LGPL runtime component executed unmodified, with source access and no-warranty artifacts
- `internal-reviewed-source`: reviewed source-configured entry with explicit source access and redistribution scope
- `blocked`: unresolved source/license state
- `remote-only`: no binary redistribution in the Linux image

## SolidEdgeMCP

Windows SolidEdgeMCP uses `internal-reviewed-source` and a configured Git
source:

```yaml
mcp_source:
  type: configured_git
  url_env: WRIGHT_SOLIDEDGE_MCP_GIT_URL
  ref_env: WRIGHT_SOLIDEDGE_MCP_GIT_REF
```

Distributable Windows trial builds that claim SolidEdgeMCP installed must
supply both values with an exact ref.

The default source values are:

```yaml
default_url: https://github.com/burhop/SolidEdgeMCP.git
default_ref: 2aad5bd24df6ce1ac9578ad35c4da7ac241b5330
```

At that ref, `src/SolidEdgeMcpServer/SolidEdgeMcpServer.csproj` targets
`net10.0-windows`, so Linux bundles keep SolidEdgeMCP blocked until a
Linux-runnable server target exists.
