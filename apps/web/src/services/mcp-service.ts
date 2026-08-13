import { logger } from "./logger";
import { hostAdapter } from "./host-adapter";

const mcpLogger = logger.child("McpService");

export interface EnvVarDefinition {
  name: string;
  label: string;
  description?: string;
  required: boolean;
  secret: boolean;
}

export interface CredentialStatusResponse {
  server_id: string;
  env_vars: EnvVarDefinition[];
  configured: Record<string, boolean>;
}

export type VerificationState =
  | "verified_mcp"
  | "verified_docs_mcp"
  | "community_mcp"
  | "user_reported_url_needed"
  | "verified_api_wrapper_candidate"
  | "capability_alias"
  | "ui_or_web_standard"
  | "watchlist"
  | "excluded";

export type InstallabilityTier =
  "tested" | "might_work" | "blocked" | "non_working";

export type RiskLevel =
  "read-only" | "low" | "medium" | "high" | "safety-critical";

export type EvidenceClass =
  | "official_production"
  | "official_preview"
  | "verified_community"
  | "community_candidate"
  | "user_reported_source_needed"
  | "api_wrapper_candidate"
  | "documentation_only"
  | "blocked_validation"
  | "excluded_or_stale";

export type TransportVariant = "stdio" | "streamable_http" | "sse" | "webmcp";

export type CompatibilityStatus =
  "compatible" | "incompatible" | "uncertain" | "blocked";

export interface CapabilityDiagnostic {
  code: string;
  message: string;
  recovery: string;
  path?: string;
  source?: string;
}

export interface PlatformSupportRecord {
  status: "yes" | "likely" | "host-dependent" | "unknown" | "no";
  tested: boolean;
  notes: string;
}

export interface ValidationSummary {
  status:
    | "passed"
    | "dependency_missing"
    | "blocked"
    | "failed"
    | "skipped"
    | "not_tested";
  message: string;
  environment?: string;
  missing_dependencies: string[];
}

export interface McpServer {
  server_id: string;
  name: string;
  type: "stdio" | "sse" | "webmcp";
  transport_variant?: TransportVariant;
  command?: string[] | string;
  is_active: boolean;
  is_installed: boolean;
  status: "active" | "inactive" | "error";
  error_message?: string;
  category: string;
  created_at: number;
  updated_at: number;
  image_url?: string;
  description?: string;
  source_url?: string;
  installed_version?: string;
  env_vars?: EnvVarDefinition[];
  credentials_configured?: Record<string, boolean>;
  verification_state: VerificationState;
  installability_tier: InstallabilityTier;
  risk_level: RiskLevel;
  deployment_mode: string;
  platform_support: Record<string, PlatformSupportRecord>;
  host_software_required: string[];
  credentials_required: string[];
  default_enabled: boolean;
  approval_gates: string[];
  validation_result: ValidationSummary;
  follow_up_url?: string;
  install_blocked_reason?: string;
}

export interface CapabilityView {
  capability_id: string;
  canonical_id: string;
  name: string;
  vendor: string;
  description: string;
  domains: string[];
  tags: string[];
  aliases: string[];
  capability_summary: string[];
  field_provenance: Record<string, string>;
  data_touched: string[];
  examples: string[];
  validation_history: Array<{
    status: string;
    message?: string;
    source?: string;
    evidence_id?: string;
    observed_at?: string;
    reason_codes?: string[];
    limitation?: string | null;
    environment?: string;
    missing_dependencies?: string[];
  }>;
  lifecycle_stage: string;
  maturity: string;
  evidence_class: EvidenceClass;
  transport: TransportVariant;
  locality: "local" | "remote";
  risk_level: RiskLevel;
  installability_tier: InstallabilityTier;
  compatibility: CapabilityCompatibility;
  source_records: Array<{
    url: string;
    kind: string;
    primary: boolean;
    authority: string;
    observed_at?: string;
    notes: string;
  }>;
  requirements: {
    runtime?: Record<string, unknown>;
    dependencies?: Record<string, string[]>;
    host_software?: string[];
    credentials?: string[];
    license?: string | null;
    approval_gates?: string[];
    supported_platforms?: Record<string, PlatformSupportRecord>;
  };
  validation_result: ValidationSummary;
  local_validation?: {
    evidence_id: string;
    state: CapabilityValidationEvidence["state"];
    observed_at: string;
    reason_codes: string[];
    limitation?: string;
  } | null;
  user_state: {
    server_id?: string;
    installed: boolean;
    active: boolean;
    process_status: string;
    explicit_disabled: boolean;
    installed_version?: string;
    credentials_configured: Record<string, boolean>;
    enabled_workspaces: Array<{ workspace_id: string; label: string }>;
  };
  custom: boolean;
  available_actions: string[];
  alternatives: string[];
}

export interface CapabilityCompatibility {
  status: CompatibilityStatus;
  platform_key: string;
  reasons: CapabilityDiagnostic[];
  observation_id?: string;
  observed_at?: string;
}

export interface MachineCompatibilityObservation {
  observation_id: string;
  observed_at: string;
  expires_at: string;
  platform_key: string;
  os_name: string;
  os_version: string;
  architecture: string;
  distribution_mode: string;
  runtimes: Record<string, Record<string, unknown>>;
  package_managers: Record<string, Record<string, unknown>>;
  container_runtime?: Record<string, unknown>;
  network_policy: "offline" | "allowed" | "unknown";
  host_observations: Record<string, Record<string, unknown>>;
  digest: string;
}

export interface CapabilityQuery {
  search?: string;
  domain?: string[];
  platform?: string[];
  lifecycle_stage?: string[];
  maturity?: string[];
  evidence_class?: EvidenceClass[];
  compatibility?: CompatibilityStatus[];
  risk?: RiskLevel[];
  locality?: Array<"local" | "remote">;
  host?: string[];
  validation?: string[];
  installed?: boolean;
  limit?: number;
  cursor?: string;
}

export interface CatalogSnapshotSummary {
  snapshot_id: string;
  channel: string;
  sequence: number;
  offline: boolean;
  updated_at: string;
}

export interface CapabilityListResponse {
  snapshot: CatalogSnapshotSummary;
  capabilities: CapabilityView[];
  next_cursor: string | null;
  total: number;
}

export interface CatalogActivationHistory {
  activation_id: string;
  from_snapshot_id: string | null;
  to_snapshot_id: string;
  kind: "bootstrap" | "activate" | "rollback" | "recovery";
  actor: string;
  trace_id: string;
  occurred_at: number;
  result: "succeeded" | "failed";
  reason_code: string | null;
}

export interface CatalogStateResponse {
  bundled_snapshot_id: string;
  active_snapshot_id: string;
  previous_snapshot_id: string | null;
  active_sequence: number;
  active_channel: string;
  active_generation: number;
  updated_at: string;
  updated_by: string;
  history: CatalogActivationHistory[];
  configured_channels: string[];
  diagnostic: CapabilityDiagnostic | null;
}

export interface CatalogUpdatePreview {
  preview_id: string;
  active_snapshot_id: string;
  candidate_snapshot_id: string;
  candidate: {
    channel: string;
    sequence: number;
    schema_version: number;
    payload_sha256: string;
    signer_key_id: string;
    expires_at: string;
  };
  diff: {
    added: Array<{ id: string }>;
    removed: Array<{ id: string }>;
    changed: Array<{ id: string; fields: Array<{ field: string }> }>;
    summary: {
      added: number;
      removed: number;
      changed: number;
      total_before: number;
      total_after: number;
    };
  };
  risk_summary: {
    new_executable_entries: number;
    new_remote_entries: number;
    high_or_safety_critical: number;
    note: string;
  };
  actor: string;
  created_at: string;
  expires_at: string;
  state: string;
  preview_digest: string;
}

export interface CatalogMutationResult {
  state: CatalogStateResponse;
  reconciled: number;
  preserved_user_state: boolean;
  preserved_counts: Record<string, number>;
}

interface ApiErrorBody {
  error_code?: string;
  message?: string;
  trace_id?: string;
  details?: { recovery?: string };
}

export class CapabilityApiError extends Error {
  readonly errorCode: string;
  readonly traceId?: string;
  readonly recovery?: string;

  constructor(
    message: string,
    errorCode: string,
    traceId?: string,
    recovery?: string,
  ) {
    super(message);
    this.name = "CapabilityApiError";
    this.errorCode = errorCode;
    this.traceId = traceId;
    this.recovery = recovery;
  }
}

export interface ImportedMcpDraft {
  draft_id: string;
  name: string;
  source_format: "claude_mcp_servers" | "vscode_servers" | "plain_server";
  transport: TransportVariant;
  command?: string;
  arguments: string[];
  endpoint?: string;
  environment_requirements: Array<{
    name: string;
    credential_required: boolean;
    value_supplied: boolean;
  }>;
  header_requirements: Array<{
    name: string;
    credential_required: boolean;
    value_supplied: boolean;
  }>;
  warnings: CapabilityDiagnostic[];
  errors: CapabilityDiagnostic[];
  redacted_preview: Record<string, unknown>;
  draft_digest: string;
}

export interface ImportPreview {
  preview_id: string;
  detected_format:
    "claude_mcp_servers" | "vscode_servers" | "plain_server" | "unknown";
  drafts: ImportedMcpDraft[];
  document_errors: CapabilityDiagnostic[];
  created_at: string;
  expires_at: string;
  source_discarded: true;
}

export interface InstallPlan {
  plan_id: string;
  plan_version: 1;
  state: string;
  capability_id: string;
  snapshot_id: string;
  machine_observation_id: string;
  backend_kind:
    "local_package" | "remote_endpoint" | "host_bridge" | "local_command";
  requested_scope: "global_registered" | "workspace";
  workspace_id?: string;
  source: Record<string, unknown>;
  requirements: {
    platform: string[];
    runtimes: string[];
    license: {
      state: string;
      reference?: string;
      independent_completion_required: boolean;
      independent_completion_recorded_at?: string;
    };
    credentials: string[];
    network: string[];
    storage: string[];
    host: string[];
  };
  effects: InstallPlanStep[];
  steps: InstallPlanStep[];
  validation_steps: InstallPlanStep[];
  rollback_steps: InstallPlanStep[];
  approval_gates: string[];
  blocking_reasons: CapabilityDiagnostic[];
  expires_at: string;
  plan_digest: string;
}

export interface InstallPlanStep {
  step_id: string;
  kind: string;
  description: string;
  target?: string;
  reversible: boolean;
  rollback_step_id?: string;
}

export interface InstallPlanRequest {
  capability_id?: string;
  import_preview_id?: string;
  draft_id?: string;
  draft_digest?: string;
  requested_scope: "global_registered" | "workspace";
  workspace_id?: string;
  independently_completed_license?: boolean;
}

export interface OnboardingRun {
  run_id: string;
  plan_id: string;
  plan_digest: string;
  state: string;
  adapter_kind: string;
  adapter_version: string;
  started_at: string;
  completed_at?: string;
  effects: Array<Record<string, unknown>>;
  validation_evidence_id?: string;
  trace_id: string;
  failure_code?: string;
  rollback_state?: string;
}

export interface CapabilityValidationEvidence {
  evidence_id: string;
  capability_id: string;
  server_id: string;
  snapshot_id: string;
  capability_digest: string;
  observation_id: string;
  platform_key: string;
  architecture: string;
  server_revision: string;
  credential_binding_digest: string;
  state:
    | "not_checked"
    | "queued"
    | "running"
    | "passed"
    | "partially_passed"
    | "failed"
    | "blocked"
    | "stale"
    | "unavailable";
  protocol_steps: Record<string, "pending" | "passed" | "failed" | "skipped">;
  schema_digest?: string;
  tool_count?: number;
  read_only_probe?: {
    name: string;
    argument_digest: string;
    result_digest: string;
    status: string;
    limitation: string;
  };
  observed_at: string;
  trace_id?: string;
  reason_codes: string[];
  missing_requirements: string[];
}

export interface WorkspaceCapabilityEnablement {
  workspace_id: string;
  capability_id: string;
  server_id: string;
  enabled: boolean;
  validation_evidence_id: string;
  invocation_approved: false;
  message: string;
}

export interface McpTool {
  tool_id: string;
  server_id: string;
  name: string;
  description?: string;
  input_schema: Record<string, any>;
  is_enabled: boolean;
  created_at: number;
}

export interface RegisterServerPayload {
  name: string;
  type: "stdio" | "sse" | "webmcp";
  command?: string[] | string;
  category: string;
  image_url?: string;
  description?: string;
  source_url?: string;
}

export const defaultMcpMetadata = () => ({
  verification_state: "user_reported_url_needed" as VerificationState,
  installability_tier: "might_work" as InstallabilityTier,
  risk_level: "low" as RiskLevel,
  deployment_mode: "unknown",
  platform_support: {
    windows_11_x64: {
      status: "unknown" as const,
      tested: false,
      notes: "not tested",
    },
    linux_x64: {
      status: "unknown" as const,
      tested: false,
      notes: "not tested",
    },
    linux_arm64: {
      status: "unknown" as const,
      tested: false,
      notes: "not tested",
    },
    macos_x64: {
      status: "unknown" as const,
      tested: false,
      notes: "not tested",
    },
    macos_arm64: {
      status: "unknown" as const,
      tested: false,
      notes: "not tested",
    },
  },
  host_software_required: [],
  credentials_required: [],
  default_enabled: true,
  approval_gates: [],
  validation_result: {
    status: "not_tested" as const,
    message: "Not yet validated in this environment",
    missing_dependencies: [],
  },
});

export interface MissingMcpReportPayload {
  name: string;
  source_url?: string;
  notes?: string;
  category?: string;
}

export interface MissingCapabilitySearchContext {
  query: string;
  filters: Record<string, string>;
}

export interface MissingCapabilityReportPayload {
  name: string;
  vendor: string;
  source_url?: string;
  domains: string[];
  expected_task: string;
  platform?: string;
  host_application?: string;
  notes?: string;
  search_context: MissingCapabilitySearchContext;
}

export interface MissingCapabilityReport extends MissingCapabilityReportPayload {
  report_id: string;
  reporter: string;
  created_at: string;
  updated_at: string;
  state: "submitted" | "exported" | "under_review" | "matched" | "closed";
  matched_capability_id?: string | null;
}
export interface VersionCheckResult {
  server_id: string;
  installed: string | null;
  latest: string | null;
  update_available: boolean;
  error: string | null;
}

const apiUrl = (path: string) => `${hostAdapter.getApiBaseUrl()}${path}`;

export class McpService {
  private async catalogRequest<T>(
    path: string,
    init?: RequestInit,
  ): Promise<T> {
    const response = await hostAdapter.fetch(apiUrl(path), init);
    if (!response.ok) {
      const body = (await response.json().catch(() => ({}))) as ApiErrorBody;
      throw new CapabilityApiError(
        body.message || "The catalog operation failed.",
        body.error_code || `HTTP_${response.status}`,
        body.trace_id,
        body.details?.recovery,
      );
    }
    return response.json();
  }

  async getCatalogState(): Promise<CatalogStateResponse> {
    return this.catalogRequest("/api/mcp/catalog/state");
  }

  async previewCatalogUpdate(
    source:
      { configured_channel: true } | { envelope: Record<string, unknown> },
  ): Promise<CatalogUpdatePreview> {
    return this.catalogRequest("/api/mcp/catalog/updates/preview", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(source),
    });
  }

  async activateCatalogUpdate(
    previewId: string,
    previewDigest: string,
  ): Promise<CatalogMutationResult> {
    return this.catalogRequest(
      `/api/mcp/catalog/updates/${encodeURIComponent(previewId)}/activate`,
      {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ preview_digest: previewDigest }),
      },
    );
  }

  async rollbackCatalog(
    activeSnapshotId: string,
    previousSnapshotId: string,
  ): Promise<CatalogMutationResult> {
    return this.catalogRequest("/api/mcp/catalog/rollback", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        active_snapshot_id: activeSnapshotId,
        previous_snapshot_id: previousSnapshotId,
      }),
    });
  }

  async previewImport(configuration: string): Promise<ImportPreview> {
    return this.catalogRequest("/api/mcp/imports/preview", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ configuration }),
    });
  }

  async createInstallPlan(request: InstallPlanRequest): Promise<InstallPlan> {
    return this.catalogRequest("/api/mcp/install-plans", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(request),
    });
  }

  async getInstallPlan(planId: string): Promise<InstallPlan> {
    return this.catalogRequest(
      `/api/mcp/install-plans/${encodeURIComponent(planId)}`,
    );
  }

  async approveInstallPlan(
    planId: string,
    planDigest: string,
  ): Promise<InstallPlan> {
    return this.catalogRequest(
      `/api/mcp/install-plans/${encodeURIComponent(planId)}/approve`,
      {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ plan_digest: planDigest }),
      },
    );
  }

  async applyInstallPlan(
    planId: string,
    planDigest: string,
  ): Promise<OnboardingRun> {
    return this.catalogRequest(
      `/api/mcp/install-plans/${encodeURIComponent(planId)}/apply`,
      {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ plan_digest: planDigest }),
      },
    );
  }

  async getOnboardingRun(runId: string): Promise<OnboardingRun> {
    return this.catalogRequest(
      `/api/mcp/onboarding-runs/${encodeURIComponent(runId)}`,
    );
  }

  async cancelOnboardingRun(runId: string): Promise<OnboardingRun> {
    return this.catalogRequest(
      `/api/mcp/onboarding-runs/${encodeURIComponent(runId)}/cancel`,
      { method: "POST" },
    );
  }

  async runCapabilityValidation(
    serverId: string,
  ): Promise<CapabilityValidationEvidence> {
    return this.catalogRequest(
      `/api/mcp/servers/${encodeURIComponent(serverId)}/validation-runs`,
      { method: "POST" },
    );
  }

  async enableCapabilityForWorkspace(
    serverId: string,
    workspaceId: string,
  ): Promise<WorkspaceCapabilityEnablement> {
    return this.catalogRequest(
      `/api/mcp/workspaces/${encodeURIComponent(workspaceId)}/capabilities/${encodeURIComponent(serverId)}/enable`,
      { method: "POST" },
    );
  }

  async getCapabilities(
    query: CapabilityQuery = {},
  ): Promise<CapabilityListResponse> {
    const parameters = new URLSearchParams();
    for (const [key, raw] of Object.entries(query)) {
      if (raw === undefined || raw === "" || raw === null) continue;
      const values = Array.isArray(raw) ? raw : [raw];
      for (const value of values) parameters.append(key, String(value));
    }
    const suffix = parameters.size ? `?${parameters.toString()}` : "";
    const response = await hostAdapter.fetch(
      apiUrl(`/api/mcp/capabilities${suffix}`),
    );
    if (!response.ok) {
      throw new Error(`Failed to fetch capabilities: ${response.status}`);
    }
    return response.json();
  }

  async getCapability(capabilityId: string): Promise<CapabilityView> {
    const response = await hostAdapter.fetch(
      apiUrl(`/api/mcp/capabilities/${encodeURIComponent(capabilityId)}`),
    );
    if (!response.ok) {
      throw new Error(`Failed to fetch capability: ${response.status}`);
    }
    return response.json();
  }

  async observeCapability(capabilityId: string): Promise<{
    observation: MachineCompatibilityObservation;
    compatibility: CapabilityCompatibility;
  }> {
    const response = await hostAdapter.fetch(
      apiUrl(
        `/api/mcp/capabilities/${encodeURIComponent(capabilityId)}/observe`,
      ),
      { method: "POST" },
    );
    if (!response.ok) {
      throw new Error(`Failed to observe capability: ${response.status}`);
    }
    return response.json();
  }

  async getServers(): Promise<McpServer[]> {
    mcpLogger.info("Fetching MCP servers");
    const response = await hostAdapter.fetch(apiUrl("/api/mcp/servers"));
    if (!response.ok) {
      mcpLogger.error("Failed to fetch MCP servers", {
        status: response.status,
      });
      throw new Error(`Failed to fetch MCP servers: ${response.statusText}`);
    }
    const data = await response.json();
    return data.servers;
  }

  async registerServer(
    payload: RegisterServerPayload,
  ): Promise<{ server_id: string; name: string; status: string }> {
    mcpLogger.info("Registering custom MCP server", { ...payload } as Record<
      string,
      unknown
    >);
    const response = await hostAdapter.fetch(apiUrl("/api/mcp/servers"), {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(payload),
    });

    if (!response.ok) {
      const errData = await response.json().catch(() => ({}));
      const msg = errData.detail || response.statusText;
      mcpLogger.error("Failed to register MCP server", { msg });
      throw new Error(msg);
    }

    return response.json();
  }

  async reportMissingMcp(
    payload: MissingMcpReportPayload,
  ): Promise<{ server_id: string; name: string; status: string }> {
    const response = await hostAdapter.fetch(
      apiUrl("/api/mcp/servers/report-missing"),
      {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(payload),
      },
    );

    if (!response.ok) {
      const errData = await response.json().catch(() => ({}));
      throw new Error(errData.detail || response.statusText);
    }
    return response.json();
  }

  async reportMissingCapability(
    payload: MissingCapabilityReportPayload,
    idempotencyKey: string,
  ): Promise<MissingCapabilityReport> {
    const response = await hostAdapter.fetch(
      apiUrl("/api/mcp/missing-capability-reports"),
      {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "Idempotency-Key": idempotencyKey,
        },
        body: JSON.stringify(payload),
      },
    );
    if (!response.ok) {
      const error = await response.json().catch(() => ({}));
      const detail = error.detail;
      throw new Error(
        (typeof detail === "object" && detail?.message) ||
          (typeof detail === "string" && detail) ||
          "The missing-capability report could not be saved.",
      );
    }
    return response.json();
  }

  async toggleServer(serverId: string, isActive: boolean): Promise<McpServer> {
    mcpLogger.info("Toggling server active state", { serverId, isActive });
    const response = await hostAdapter.fetch(
      apiUrl(`/api/mcp/servers/${serverId}`),
      {
        method: "PATCH",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ is_active: isActive }),
      },
    );

    if (!response.ok) {
      mcpLogger.error("Failed to toggle MCP server state", {
        status: response.status,
      });
      throw new Error(`Failed to toggle MCP server: ${response.statusText}`);
    }

    const data = await response.json();
    return {
      server_id: data.server_id,
      name: "", // backend patch returns server_id, is_active, status, error_message
      type: data.type,
      is_active: data.is_active,
      is_installed: data.is_installed || false,
      status: data.status,
      error_message: data.error_message,
      category: "",
      created_at: 0,
      updated_at: 0,
      ...defaultMcpMetadata(),
    };
  }

  async deleteServer(serverId: string): Promise<void> {
    mcpLogger.info("Deleting MCP server", { serverId });
    const response = await hostAdapter.fetch(
      apiUrl(`/api/mcp/servers/${serverId}`),
      {
        method: "DELETE",
      },
    );

    if (!response.ok) {
      mcpLogger.error("Failed to delete MCP server", {
        status: response.status,
      });
      throw new Error(`Failed to delete MCP server: ${response.statusText}`);
    }
  }

  async getTools(): Promise<McpTool[]> {
    mcpLogger.info("Fetching MCP tools");
    const response = await hostAdapter.fetch(apiUrl("/api/mcp/tools"));
    if (!response.ok) {
      mcpLogger.error("Failed to fetch MCP tools", { status: response.status });
      throw new Error(`Failed to fetch MCP tools: ${response.statusText}`);
    }
    const data = await response.json();
    return data.tools;
  }

  async toggleTool(toolId: string, isEnabled: boolean): Promise<McpTool> {
    mcpLogger.info("Toggling tool enabled state", { toolId, isEnabled });
    const response = await hostAdapter.fetch(
      apiUrl(`/api/mcp/tools/${toolId}`),
      {
        method: "PATCH",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ is_enabled: isEnabled }),
      },
    );

    if (!response.ok) {
      mcpLogger.error("Failed to toggle tool state", {
        status: response.status,
      });
      throw new Error(`Failed to toggle MCP tool: ${response.statusText}`);
    }

    return response.json();
  }

  async installServer(
    serverId: string,
    sessionId?: string | null,
  ): Promise<McpServer> {
    mcpLogger.info("Installing MCP server", { serverId, sessionId });
    const url = sessionId
      ? apiUrl(`/api/mcp/servers/${serverId}/install?session_id=${sessionId}`)
      : apiUrl(`/api/mcp/servers/${serverId}/install`);
    const response = await hostAdapter.fetch(url, { method: "POST" });

    if (!response.ok) {
      const errData = await response.json().catch(() => ({}));
      const msg = errData.detail || response.statusText;
      mcpLogger.error("Failed to install MCP server", { msg });
      throw new Error(msg);
    }

    const data = await response.json();
    return {
      server_id: data.server_id,
      name: "",
      type: data.type,
      is_active: false,
      is_installed: data.is_installed,
      status: data.status,
      error_message: data.error_message,
      category: "",
      created_at: 0,
      updated_at: 0,
      ...defaultMcpMetadata(),
    };
  }

  async uninstallServer(
    serverId: string,
    sessionId?: string | null,
  ): Promise<McpServer> {
    mcpLogger.info("Uninstalling MCP server", { serverId, sessionId });
    const url = sessionId
      ? apiUrl(`/api/mcp/servers/${serverId}/uninstall?session_id=${sessionId}`)
      : apiUrl(`/api/mcp/servers/${serverId}/uninstall`);
    const response = await hostAdapter.fetch(url, { method: "POST" });

    if (!response.ok) {
      const errData = await response.json().catch(() => ({}));
      const msg = errData.detail || response.statusText;
      mcpLogger.error("Failed to uninstall MCP server", { msg });
      throw new Error(msg);
    }

    const data = await response.json();
    return {
      server_id: data.server_id,
      name: "",
      type: data.type,
      is_active: false,
      is_installed: data.is_installed,
      status: data.status,
      error_message: data.error_message,
      category: "",
      created_at: 0,
      updated_at: 0,
      ...defaultMcpMetadata(),
    };
  }

  async checkServerVersion(serverId: string): Promise<VersionCheckResult> {
    mcpLogger.info("Checking server version", { serverId });
    const response = await hostAdapter.fetch(
      apiUrl(`/api/mcp/servers/${serverId}/version-check`),
    );
    if (!response.ok) {
      mcpLogger.error("Failed to check server version", {
        status: response.status,
      });
      throw new Error(`Failed to check server version: ${response.statusText}`);
    }
    return response.json();
  }

  async updateServer(serverId: string): Promise<{ installed_version: string }> {
    mcpLogger.info("Updating server", { serverId });
    const response = await hostAdapter.fetch(
      apiUrl(`/api/mcp/servers/${serverId}/update`),
      {
        method: "POST",
      },
    );
    if (!response.ok) {
      mcpLogger.error("Failed to update server", { status: response.status });
      throw new Error(`Failed to update server: ${response.statusText}`);
    }
    return response.json();
  }

  async getCredentialStatus(
    serverId: string,
  ): Promise<CredentialStatusResponse> {
    mcpLogger.info("Fetching credential status", { serverId });
    const response = await hostAdapter.fetch(
      apiUrl(`/api/mcp/servers/${serverId}/credentials`),
    );
    if (!response.ok) {
      mcpLogger.error("Failed to get credential status", {
        status: response.status,
      });
      throw new Error(
        `Failed to get credential status: ${response.statusText}`,
      );
    }
    return response.json();
  }

  async saveCredentials(
    serverId: string,
    credentials: Record<string, string>,
  ): Promise<CredentialStatusResponse> {
    mcpLogger.info("Saving credentials", { serverId });
    const response = await hostAdapter.fetch(
      apiUrl(`/api/mcp/servers/${serverId}/credentials`),
      {
        method: "PUT",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ credentials }),
      },
    );
    if (!response.ok) {
      const errData = await response.json().catch(() => ({}));
      const msg = errData.detail || response.statusText;
      mcpLogger.error("Failed to save credentials", { msg });
      throw new Error(msg);
    }
    return response.json();
  }

  async deleteCredentials(serverId: string): Promise<void> {
    mcpLogger.info("Deleting credentials", { serverId });
    const response = await hostAdapter.fetch(
      apiUrl(`/api/mcp/servers/${serverId}/credentials`),
      {
        method: "DELETE",
      },
    );
    if (!response.ok) {
      mcpLogger.error("Failed to delete credentials", {
        status: response.status,
      });
      throw new Error(`Failed to delete credentials: ${response.statusText}`);
    }
  }
}

export const mcpService = new McpService();
