# Data Model: MCP Docker Appliance

## MCP Bundle Manifest

- `schema_version`: manifest schema integer
- `bundle_id`: stable bundle identifier
- `base_image`: base Wright image reference
- `default_license_policy`: license allowlist and supported compliance profiles
- `applications`: local application/runtime records
- `mcp_servers`: MCP server records
- `generated_outputs`: generated config/status/license paths

Validation rules:

- The manifest must be deterministic and reviewable.
- Local entries must have exact package versions, exact Git refs, or an explicit configured source gate.
- Generated config must come only from `mcp_servers`.

## Application Entry

- `id`: stable machine identifier
- `display_name`: engineer-facing name
- `category`: application domain
- `availability`: `local_enabled`, `blocked_pending_review`, `remote_only`, or `windows_only`
- `source`: package/repo/release/system source and license evidence
- `compliance_profile`: permissive, GPL runtime, LGPL runtime, or other supported profile
- `install`: build-time application installation instructions
- `health_probe`: direct binary/runtime health probe
- `docs_summary`: short engineer documentation text

Validation rules:

- `local_enabled` applications require source, install, compliance, and health probe data.
- OpenSCAD uses GPL runtime compliance.
- FreeCAD uses LGPL runtime compliance.
- BREP and Playwright use permissive package compliance.

## MCP Server Entry

- `id`: stable server identifier used in generated Hermes config
- `display_name`: engineer-facing server name
- `application_id`: linked application id or `null` for externally backed/internal servers
- `availability`: local or external status
- `mcp_source`: server source and license evidence
- `compliance_profile`: compliance profile for the MCP source
- `install`: build-time server installation instructions
- `launch`: command, args, and environment generated into Hermes config
- `workspace_binding`: trusted `{workspace.path}` binding metadata
- `health_probe`: direct MCP health expectations
- `prompt_probe`: engineer-level validation prompt

Validation rules:

- Local MCP servers require install, launch, health probe, and compliance data.
- Non-null `application_id` must reference an application entry.
- `solid-edge-mcp` uses `application_id: null` because Solid Edge itself is not redistributed.

## Third-Party Compliance Profile

- `profile_id`: `permissive`, `gpl-2.0-runtime-redistribution`, `lgpl-runtime-redistribution`, or `internal-reviewed-source`
- `runtime_use_only`: true when redistributing an unmodified executable runtime
- `modification_status`: unmodified, patched, rebuilt, or unknown
- `source_access`: source URL/archive/repository/written-offer instruction
- `license_text`: generated or system license text path
- `no_warranty_notice`: generated no-warranty notice path
- `redistribution_scope`: internal-source distribution boundary when applicable

Validation rules:

- Unknown licenses fail closed.
- GPL/LGPL runtime profiles require unmodified status, source access, license text, and no-warranty notice.
- Internal-source profiles require explicit source access and redistribution scope.

## Generated Runtime Config

- `hermes-mcp.generated.yaml`: generated `mcp_servers` mapping
- `mcp-bundle-status.json`: accepted/blocked/remote status per application and MCP server
- `THIRD-PARTY-COMPLIANCE.json`: generated license/compliance evidence
- `NO-WARRANTY-GPL-2.0.txt`: GPL runtime notice
- `NO-WARRANTY-LGPL.txt`: LGPL runtime notice
- `source-offer.md`: source access/written-offer guidance

Validation rules:

- Generated config is idempotently merged into the `wright` Hermes profile at container startup.
- Generated status is copied to Wright config for inspection.

## MCP Appliance Image

- `image_name`: local or published Docker image name
- `base_revision`: base Wright image/source revision
- `bundle_manifest_sha256`: digest of manifest used
- `default_ports`: same primary Wright UI/API mapping as standard appliance
- `default_volumes`: MCP-specific volume names
- `runtime_mode`: localhost by default, LAN opt-in

Validation rules:

- Standard appliance behavior remains unchanged.
- MCP compose defaults must not reuse standard volume names.

## Managed Image Profile

- `id`: `wright-standard`, `wright-mcp-linux-amd64`,
  `wright-mcp-linux-arm64`, or `wright-mcp-windows-amd64`
- `image`: local/published image tag
- `dockerfile`: Dockerfile used to build the profile
- `platform`: Docker platform such as `linux/amd64`, `linux/arm64`, or
  `windows/amd64`
- `kind`: standard Wright appliance, MCP appliance, or Windows MCP runtime
- `bundle`: platform bundle file when applicable
- `persisted_paths`: directories that must be backed by Docker volumes or host
  bind mounts

Validation rules:

- The image family must declare the four managed profiles.
- Every profile must have persisted paths for data, workspace, config, Hermes
  or profile state, and logs.
- Linux arm64 must not depend on x86_64-only application assets.
- Windows profiles must not claim Solid Edge redistribution.

## Validation Workspace

- `workspace_id`: fresh workspace identity
- `workspace_path`: canonical container path
- `enabled_mcp_servers`: MCP servers attached to the workspace
- `health_results`: per-service/per-server status
- `prompt_results`: representative prompt outcomes
- `artifacts`: generated CAD/browser outputs

Validation rules:

- Workspaces must be fresh for Docker smoke and Playwright tests.
- Artifacts must remain inside the workspace.
