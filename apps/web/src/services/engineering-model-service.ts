import { hostAdapter } from "./host-adapter";

export interface ModelCatalogSnapshot {
  snapshot_id: string;
  catalog_digest: string;
  freshness: string;
  offline: boolean;
  channel?: string;
  sequence?: number;
}

export interface EngineeringModelBlocker {
  category: string;
  message: string;
  recovery: string;
}

export interface EngineeringModelVariant {
  variant_id: string;
  format: string;
  precision?: string;
  platforms?: string[];
  accelerator?: string;
  runtime?: Record<string, unknown>;
  resources?: Record<string, number>;
  artifacts?: Array<Record<string, unknown>>;
  compatibility?: { state: string; reasons: string[] };
  evidence?: Record<string, string>;
}

export interface EngineeringModelView {
  model_id: string;
  display_name: string;
  description: string;
  tasks: string[];
  source: {
    kind: string;
    uri: string;
    immutable_revision: string;
    access?: string;
  };
  license: {
    expression: string;
    attribution: string;
    redistribution: string;
    acceptance_required?: boolean;
  };
  readiness: string;
  compatibility: { state: string; reasons: string[] };
  evidence: Record<string, string>;
  limitations: Array<{
    limitation_id: string;
    description: string;
    severity?: string;
  }>;
  variants: EngineeringModelVariant[];
  blockers: EngineeringModelBlocker[];
  generator: {
    kind: string;
    recipe: string;
    inputs: Record<string, unknown>;
    constraints: string[];
    manifest_digest: string;
    artifact_set_digest: string;
  } | null;
  qualification?: {
    dataset: string;
    dataset_digest: string;
    feature_count: number;
    membership: Record<string, unknown>;
    recipe: Record<string, unknown>;
    serving_boundary: string;
    parity_requirements: Record<string, unknown>;
  } | null;
  manifest_digest: string;
  entry_digest: string;
  snapshot: ModelCatalogSnapshot;
}

export interface EngineeringModelCatalogResponse {
  snapshot: ModelCatalogSnapshot;
  models: EngineeringModelView[];
  next_cursor: string | null;
  total: number;
}

export interface EngineeringModelCatalogQuery {
  search?: string;
  task?: string;
  source_kind?: string;
  readiness?: string[];
  platform?: string;
  architecture?: string;
  accelerator?: string;
  evidence_state?: string;
  maximum_bytes?: number;
  cursor?: string;
  limit?: number;
}

export interface EngineeringModelInstallation {
  installation_id: string;
  model_id: string;
  package_revision: number;
  variant_id: string;
  manifest_digest: string;
  state:
    | "installed"
    | "testing"
    | "ready"
    | "unhealthy"
    | "disabled"
    | "uninstalled"
    | "missing";
  active_revision: boolean;
  runtime_adapter_id: string;
  runtime_adapter_version: string;
  standard_test_evidence_id?: string;
  installed_at: string;
  last_verified_at?: string;
}

export interface EngineeringModelEffect {
  kind: string;
  description: string;
  source?: string;
  safe_location?: string;
  exact_bytes?: number;
  maximum_bytes: number;
  reversible: boolean;
}

export interface EngineeringModelPlan {
  schema_version: "1.0";
  plan_id: string;
  plan_digest: string;
  operation_kind:
    | "install"
    | "import"
    | "update"
    | "rollback"
    | "export"
    | "disable"
    | "uninstall"
    | "purge";
  model_id: string;
  variant_id: string;
  state: string;
  effects: EngineeringModelEffect[];
  blockers: EngineeringModelBlocker[];
  requirements: {
    network: string;
    credential: string;
    license_action: string;
    runtime_change: string;
  };
  rollback: string;
  cleanup: string;
  expires_at: string;
}

export interface EngineeringModelProgress {
  completed_items: number;
  total_items: number;
  completed_bytes: number;
  maximum_bytes: number;
  message?: string;
}

export interface EngineeringModelOperation {
  operation_id: string;
  state: string;
  phase: string;
  progress: EngineeringModelProgress;
  cleanup_state: string;
  result?: Record<string, unknown> | null;
  failure?: EngineeringModelBlocker | null;
}

export interface EngineeringModelOperationEvent {
  sequence: number;
  operation: EngineeringModelOperation;
}

export interface EngineeringModelEvidence {
  evidence_id: string;
  state: "passed" | "failed" | "blocked" | "error";
  material_digest: string;
  observation_digest: string;
  material?: Record<string, unknown>;
  observation?: Record<string, unknown>;
  evidence?: Record<string, unknown>;
}

export interface EngineeringModelRuntimeTest {
  installation_id: string;
  installation_state: "installed" | "testing" | "ready" | "unhealthy";
  adapter_id: string;
  adapter_version: string;
  evidence: EngineeringModelEvidence[];
}

export interface EngineeringModelWorkspaceBinding {
  binding_id: string;
  binding_digest: string;
  workspace_id: string;
  installation_id: string;
  task_id: string;
  tool_name: string;
  policy_snapshot_digest: string;
  state: "enabled" | "disabled" | "stale" | "blocked";
}

export interface EngineeringModelUpdateComparison {
  current_manifest_digest?: string;
  candidate_manifest_digest?: string;
  changed_facets: string[];
  diff_digest: string;
  requires_retest: boolean;
  requires_license_review?: boolean;
}

export interface EngineeringModelMaintenanceStatus {
  installation_id?: string;
  state: string;
  active?: boolean;
  reclaimable_bytes?: number;
  reclaimed_bytes?: number;
  blockers: Array<Record<string, unknown>>;
  references: Array<Record<string, unknown>>;
  target_installation_id?: string;
  current_installation_id?: string;
  active_installation_id?: string;
  predecessor_id?: string;
  cached_content_reused?: boolean;
  cleanup_state?: string;
  category?: string;
  message?: string;
}

export interface EngineeringModelOfflineExport {
  artifact_id: string;
  sha256: string;
  size: number;
  filename?: string;
}

export class EngineeringModelServiceError extends Error {
  readonly category: string;
  readonly recovery: string;
  readonly status: number;

  constructor(
    category: string,
    message: string,
    recovery: string,
    status: number,
  ) {
    super(message);
    this.name = "EngineeringModelServiceError";
    this.category = category;
    this.recovery = recovery;
    this.status = status;
  }
}

async function readResponse<T>(response: Response): Promise<T> {
  if (response.ok) return response.json() as Promise<T>;
  const body = await response.json().catch(() => ({}));
  const detail = body?.detail ?? body?.error ?? {};
  throw new EngineeringModelServiceError(
    String(detail.category ?? "model_request_failed"),
    String(detail.message ?? "The engineering model request failed."),
    String(detail.recovery ?? "Retry from the current offline snapshot."),
    response.status,
  );
}

export class EngineeringModelService {
  private apiUrl(path: string): string {
    return `${hostAdapter.getApiBaseUrl()}${path}`;
  }

  async listCatalog(
    query: EngineeringModelCatalogQuery = {},
  ): Promise<EngineeringModelCatalogResponse> {
    const parameters = new URLSearchParams();
    for (const [key, raw] of Object.entries(query)) {
      if (raw === undefined || raw === null || raw === "") continue;
      const values = Array.isArray(raw) ? raw : [raw];
      for (const value of values) parameters.append(key, String(value));
    }
    const suffix = parameters.size ? `?${parameters.toString()}` : "";
    const response = await hostAdapter.fetch(
      this.apiUrl(`/api/v1/engineering-models/catalog${suffix}`),
    );
    return readResponse<EngineeringModelCatalogResponse>(response);
  }

  async getCatalogModel(modelId: string): Promise<EngineeringModelView> {
    const response = await hostAdapter.fetch(
      this.apiUrl(
        `/api/v1/engineering-models/catalog/${encodeURIComponent(modelId)}`,
      ),
    );
    return readResponse<EngineeringModelView>(response);
  }

  async listInstallations(
    modelId?: string,
  ): Promise<EngineeringModelInstallation[]> {
    const suffix = modelId ? `?model_id=${encodeURIComponent(modelId)}` : "";
    const response = await hostAdapter.fetch(
      this.apiUrl(`/api/v1/engineering-models/installations${suffix}`),
    );
    const result = await readResponse<{
      installations: EngineeringModelInstallation[];
    }>(response);
    return result.installations;
  }

  async createPlan(
    modelId: string,
    variantId: string,
    operationKind: "install" | "import" = "install",
  ): Promise<EngineeringModelPlan> {
    const response = await hostAdapter.fetch(
      this.apiUrl("/api/v1/engineering-models/plans"),
      {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          operation_kind: operationKind,
          model_id: modelId,
          variant_id: variantId,
        }),
      },
    );
    return readResponse<EngineeringModelPlan>(response);
  }

  async createMaintenancePlan(
    installationId: string,
    operationKind:
      "update" | "rollback" | "export" | "disable" | "uninstall" | "purge",
    targetInstallationId?: string,
  ): Promise<EngineeringModelPlan> {
    const response = await hostAdapter.fetch(
      this.apiUrl("/api/v1/engineering-models/plans"),
      {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          operation_kind: operationKind,
          installation_id: installationId,
          ...(targetInstallationId
            ? { target_installation_id: targetInstallationId }
            : {}),
        }),
      },
    );
    return readResponse<EngineeringModelPlan>(response);
  }

  async createImportPlan(
    archive: Blob,
    filename = "model.wright-model.zip",
  ): Promise<EngineeringModelPlan> {
    const body = new FormData();
    body.append("package", archive, filename);
    const response = await hostAdapter.fetch(
      this.apiUrl("/api/v1/engineering-models/imports"),
      { method: "POST", body },
    );
    return readResponse<EngineeringModelPlan>(response);
  }

  async getPlan(planId: string): Promise<EngineeringModelPlan> {
    const response = await hostAdapter.fetch(
      this.apiUrl(
        `/api/v1/engineering-models/plans/${encodeURIComponent(planId)}`,
      ),
    );
    return readResponse<EngineeringModelPlan>(response);
  }

  async confirmPlan(
    planId: string,
    planDigest: string,
  ): Promise<EngineeringModelOperation> {
    const response = await hostAdapter.fetch(
      this.apiUrl(
        `/api/v1/engineering-models/plans/${encodeURIComponent(planId)}/confirm`,
      ),
      {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ plan_digest: planDigest }),
      },
    );
    return readResponse<EngineeringModelOperation>(response);
  }

  async getOperation(operationId: string): Promise<EngineeringModelOperation> {
    const response = await hostAdapter.fetch(
      this.apiUrl(
        `/api/v1/engineering-models/operations/${encodeURIComponent(operationId)}`,
      ),
    );
    return readResponse<EngineeringModelOperation>(response);
  }

  async cancelOperation(
    operationId: string,
  ): Promise<EngineeringModelOperation> {
    const response = await hostAdapter.fetch(
      this.apiUrl(
        `/api/v1/engineering-models/operations/${encodeURIComponent(operationId)}/cancel`,
      ),
      { method: "POST" },
    );
    return readResponse<EngineeringModelOperation>(response);
  }

  async readOperationEvents(
    operationId: string,
    after = 0,
  ): Promise<EngineeringModelOperationEvent[]> {
    const response = await hostAdapter.fetch(
      this.apiUrl(
        `/api/v1/engineering-models/operations/${encodeURIComponent(operationId)}/events`,
      ),
      {
        headers: {
          Accept: "text/event-stream",
          "Last-Event-ID": String(after),
        },
      },
    );
    if (!response.ok)
      return readResponse<EngineeringModelOperationEvent[]>(response);
    const text = await response.text();
    const events = text
      .split(/\r?\n\r?\n/)
      .filter(Boolean)
      .map((block) => {
        const data = block
          .split(/\r?\n/)
          .filter((line) => line.startsWith("data:"))
          .map((line) => line.slice(5).trimStart())
          .join("\n");
        if (!data) throw new Error("Engineering model event data is missing.");
        return JSON.parse(data) as EngineeringModelOperationEvent;
      });
    if (events.length > 1000) {
      throw new Error("Engineering model event history exceeds its bound.");
    }
    return events;
  }

  async runStandardTest(
    installationId: string,
  ): Promise<EngineeringModelRuntimeTest> {
    const response = await hostAdapter.fetch(
      this.apiUrl(
        `/api/v1/engineering-models/installations/${encodeURIComponent(installationId)}/standard-test`,
      ),
      { method: "POST" },
    );
    return readResponse<EngineeringModelRuntimeTest>(response);
  }

  async getStandardTestEvidence(
    installationId: string,
  ): Promise<EngineeringModelRuntimeTest> {
    const response = await hostAdapter.fetch(
      this.apiUrl(
        `/api/v1/engineering-models/installations/${encodeURIComponent(installationId)}/evidence`,
      ),
    );
    return readResponse<EngineeringModelRuntimeTest>(response);
  }

  async createWorkspaceBinding(
    workspaceId: string,
    installationId: string,
    taskId: string,
  ): Promise<EngineeringModelWorkspaceBinding> {
    const response = await hostAdapter.fetch(
      this.apiUrl(
        `/api/v1/engineering-models/workspaces/${encodeURIComponent(workspaceId)}/bindings`,
      ),
      {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "X-Wright-Workspace-ID": workspaceId,
        },
        body: JSON.stringify({
          installation_id: installationId,
          task_id: taskId,
        }),
      },
    );
    return readResponse<EngineeringModelWorkspaceBinding>(response);
  }

  async setWorkspaceBindingState(
    workspaceId: string,
    bindingId: string,
    state: "enabled" | "disabled",
  ): Promise<EngineeringModelWorkspaceBinding> {
    const response = await hostAdapter.fetch(
      this.apiUrl(
        `/api/v1/engineering-models/workspaces/${encodeURIComponent(workspaceId)}/bindings/${encodeURIComponent(bindingId)}`,
      ),
      {
        method: "PATCH",
        headers: {
          "Content-Type": "application/json",
          "X-Wright-Workspace-ID": workspaceId,
        },
        body: JSON.stringify({ state }),
      },
    );
    return readResponse<EngineeringModelWorkspaceBinding>(response);
  }

  async getInstallationMaintenance(
    installationId: string,
  ): Promise<EngineeringModelMaintenanceStatus> {
    const response = await hostAdapter.fetch(
      this.apiUrl(
        `/api/v1/engineering-models/installations/${encodeURIComponent(installationId)}/maintenance`,
      ),
    );
    return readResponse<EngineeringModelMaintenanceStatus>(response);
  }

  async compareInstallationUpdate(
    installationId: string,
    modelId: string,
    variantId: string,
  ): Promise<EngineeringModelUpdateComparison> {
    const response = await hostAdapter.fetch(
      this.apiUrl(
        `/api/v1/engineering-models/installations/${encodeURIComponent(installationId)}/compare-update`,
      ),
      {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ model_id: modelId, variant_id: variantId }),
      },
    );
    return readResponse<EngineeringModelUpdateComparison>(response);
  }

  async maintainInstallation(
    installationId: string,
    action: "disable" | "uninstall" | "purge" | "update" | "rollback",
    targetInstallationId?: string,
  ): Promise<EngineeringModelMaintenanceStatus> {
    const response = await hostAdapter.fetch(
      this.apiUrl(
        `/api/v1/engineering-models/installations/${encodeURIComponent(installationId)}/maintenance`,
      ),
      {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          action,
          ...(targetInstallationId
            ? { target_installation_id: targetInstallationId }
            : {}),
        }),
      },
    );
    return readResponse<EngineeringModelMaintenanceStatus>(response);
  }

  async setModelReferenceState(
    referenceId: string,
    state: "detached" | "archived",
  ): Promise<{ reference_id: string; state: string }> {
    const response = await hostAdapter.fetch(
      this.apiUrl(
        `/api/v1/engineering-models/references/${encodeURIComponent(referenceId)}`,
      ),
      {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ state }),
      },
    );
    return readResponse<{ reference_id: string; state: string }>(response);
  }

  async createOfflineExport(
    installationId: string,
  ): Promise<EngineeringModelOfflineExport> {
    const response = await hostAdapter.fetch(
      this.apiUrl(
        `/api/v1/engineering-models/installations/${encodeURIComponent(installationId)}/exports`,
      ),
      { method: "POST" },
    );
    return readResponse<EngineeringModelOfflineExport>(response);
  }
}

export const engineeringModelService = new EngineeringModelService();
