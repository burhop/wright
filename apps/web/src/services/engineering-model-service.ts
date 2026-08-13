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
}

export const engineeringModelService = new EngineeringModelService();
