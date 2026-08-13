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
}

export const engineeringModelService = new EngineeringModelService();
