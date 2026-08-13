import { logger } from "./logger";
import { hostAdapter } from "./host-adapter";
import type { SelectOptions } from "./host-adapter/wright-desktop";

const workspaceLogger = logger.child("WorkspaceService");

export interface WorkspaceNode {
  name: string;
  path: string;
  type: "file" | "directory";
  size: number | null;
  last_modified: number;
  git_status: "Clean" | "M" | "U" | "A" | "D";
  children: WorkspaceNode[] | null;
}

export interface RivetWorkflowOperation {
  workflow_id: string;
  slug: string;
  revision: number;
  etag: string;
  review_state: "approved" | "rejected" | null;
  reviewer: string | null;
  reviewed_at: number | null;
  workflow_digest?: string | null;
  graph_id?: string | null;
  binding_set_id?: string | null;
  binding_set_digest?: string | null;
  policy_snapshot_digest?: string | null;
  review_digest?: string | null;
  stale_reasons?: string[];
}

export interface RivetMcpRequirement {
  graph_id: string;
  node_id: string;
  node_type: "mcpDiscovery" | "mcpToolCall";
  static_tool_name: string | null;
}

export interface RivetMcpCapability {
  qualified_tool_name: string;
  server_id: string;
  tool_name: string;
  title: string;
  description: string;
  server_revision: string;
  capability_digest: string;
  validation_evidence_id: string;
  workspace_grant_digest: string;
  input_schema: Record<string, unknown>;
  output_schema: Record<string, unknown> | null;
  schema_digest: string;
  annotations: Record<string, boolean>;
  required_approvals: string[];
  compatibility: string;
  binding_eligible: boolean;
  blocking_reasons: string[];
}

export interface RivetMcpCapabilities {
  workflow_id: string;
  slug: string;
  revision: number;
  etag: string;
  graph_id: string;
  snapshot_digest: string;
  policy_snapshot_digest: string;
  requirements: RivetMcpRequirement[];
  issues: Array<{
    code: string;
    message: string;
    graph_id?: string | null;
    node_id?: string | null;
  }>;
  capabilities: RivetMcpCapability[];
  next_after: number | null;
}

export interface RivetMcpBindingSelection {
  node_id: string;
  qualified_tool_name: string;
  units_policy?: Record<string, unknown>;
  material_defaults?: Record<string, unknown>;
}

export interface RivetMcpBindingPreview {
  workflow_id: string;
  slug: string;
  revision: number;
  etag: string;
  graph_id: string;
  snapshot_digest: string;
  policy_snapshot_digest: string;
  binding_set_id: string | null;
  binding_set_digest: string | null;
  expires_at: string;
  ready: boolean;
  bindings: Array<{
    node_id: string;
    node_handle: string | null;
    selected_tool: string | null;
    binding_digest: string | null;
    server_id: string | null;
    server_revision: string | null;
    schema_digest: string | null;
    validation_evidence_id: string | null;
    workspace_grant_digest: string | null;
    risk: Record<string, unknown> | null;
    units_policy: Record<string, unknown> | null;
    material_defaults: Record<string, unknown> | null;
    blockers: string[];
  }>;
}

export interface RivetWorkflowTemplate {
  template_id: string;
  title: string;
  description: string;
  kind: "starter" | "advanced" | "example";
  requirements: string[];
}

export interface RivetWorkflowRun {
  run_id: string;
  workflow_id: string;
  revision: number;
  digest: string | null;
  graph: string | null;
  generation: number;
  state: string;
  reason: string | null;
  outputs: Record<string, unknown> | null;
  duration_ms: number | null;
  output_truncated: boolean;
  manifest?: Record<string, unknown> | null;
}

export interface RivetRunEvidence {
  schema_version: 1;
  run_id: string;
  manifest: Record<string, unknown>;
  bindings: Array<Record<string, unknown>>;
  child_calls: Array<Record<string, unknown>>;
  approvals: Array<Record<string, unknown>>;
  artifacts: Array<{
    artifact_id?: string;
    domain?: string;
    kind?: string;
    content_digest?: string;
    validation_state?: string;
    producer?: { node_id?: string; capability?: string; call_id?: string };
    [key: string]: unknown;
  }>;
  timeline: Array<Record<string, unknown>>;
  reproducibility: {
    reproducible: boolean;
    differences: Array<{
      code: string;
      recorded: string;
      current: string;
      recovery_action: string;
    }>;
    summary: string;
  };
  accounting: Record<string, unknown>;
}

export interface EngineeringScenarioEntry {
  scenario_id: string;
  revision: number;
  title: string;
  summary: string;
  domains: string[];
  tier: "tier1" | "tier2" | "tier3";
  resource_class: "small" | "medium" | "large" | "external";
  expected_duration_seconds: number;
  manifest_digest: string;
}

export interface EngineeringScenarioDetail {
  manifest: Record<string, unknown>;
  manifest_digest: string;
}

export interface EngineeringScenarioPreflight {
  preflight_id: string;
  scenario_id: string;
  scenario_revision: number;
  manifest_digest: string;
  workflow_slug: string;
  workflow_revision: number | null;
  workflow_digest: string | null;
  graph_id: string;
  binding_set_digest: string | null;
  state: "ready" | "blocked" | "skipped";
  capabilities: Array<{
    node_id: string;
    requested_tool: string;
    selected_tool: string | null;
    binding_digest: string | null;
    blockers: string[];
  }>;
  environment: Record<string, unknown>;
  blockers: Array<{ code: string; message: string; recovery: string }>;
  expires_at: string;
}

export interface EngineeringScenarioReport {
  scenario_run_id: string;
  workflow_run_id: string;
  workspace_id: string;
  session_id: string;
  scenario_id: string;
  scenario_revision: number;
  manifest_digest: string;
  workflow_digest: string;
  binding_set_digest: string | null;
  state: string;
  identity: Record<string, unknown>;
  artifacts: Array<{
    artifact_id: string;
    domain: string;
    kind: string;
    content_digest: string;
    validation_state: string;
    producer: {
      run_id: string;
      node_id: string;
      call_id: string;
      capability: string;
    };
  }>;
  environment: Record<string, unknown>;
  cleanup_state: string;
  residue: Record<string, unknown>;
  assertions: Array<{
    assertion_id: string;
    plugin: string;
    state: "pass" | "fail" | "skip" | "error";
    reason_code: string;
    artifact_digests?: string[];
    expected?: unknown;
    observed?: unknown;
    units?: Record<string, unknown>;
    producer: { node_id: string; capability: string; call_id?: string };
    message?: string;
    recovery?: string;
  }>;
  report_digest: string | null;
}

export interface EngineeringScenarioComparison {
  strictly_reproducible: boolean;
  differences: Array<Record<string, unknown>>;
  assertion_changes: Array<Record<string, unknown>>;
}

export interface RivetCallApproval {
  approval_id: string;
  run_id: string;
  node_id: string;
  qualified_tool_name: string;
  binding_digest: string;
  argument_digest: string;
  argument_summary: Record<string, unknown>;
  required_gates: string[];
  state:
    "pending" | "approved" | "denied" | "expired" | "consumed" | "cancelled";
  expires_at: string;
  approval_digest: string;
  decided_by: string | null;
  decision_reason: string | null;
}

export interface RivetWorkflowRunOptions {
  expectedRevision: number;
  expectedDigest: string;
  graph?: string;
  inputs?: Record<string, unknown>;
  context?: Record<string, unknown>;
  timeoutSeconds?: number;
  expectedReviewDigest?: string;
  bindingSetDigest?: string;
}

export interface RivetWorkflowDocument extends RivetWorkflowOperation {
  project: string;
  datasets: Record<string, string>;
}

export interface RivetEditorSurface {
  availability: "disabled" | "available" | "missing" | "incompatible";
  detail: string | null;
  manifest: Record<string, unknown> | null;
}

export interface BrepPanelSession {
  server_id: string;
  control_url: string;
  module_url: string;
  connected: boolean;
}

export interface RivetWorkflowGraphNode {
  node_id: string;
  node_type: string | null;
  title: string | null;
  data: Record<string, unknown>;
  outgoing_connections: string[];
}

export interface RivetWorkflowGraph {
  graph_id: string;
  name: string | null;
  main: boolean;
  node_count: number;
  nodes: RivetWorkflowGraphNode[];
}

export interface RivetWorkflowGraphResponse extends RivetWorkflowOperation {
  graph: RivetWorkflowGraph;
  issues: Array<Record<string, unknown>>;
}

const slugifyWorkflowName = (name: string) =>
  name
    .trim()
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-+|-+$/g, "") || "untitled-workflow";

const titleFromSlug = (slug: string) =>
  slug
    .split("-")
    .filter(Boolean)
    .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
    .join(" ") || "Untitled Workflow";

const nextWorkflowSlug = (
  workflows: RivetWorkflowOperation[],
  preferredName: string,
) => {
  const taken = new Set(workflows.map((workflow) => workflow.slug));
  const base = slugifyWorkflowName(preferredName);
  let slug = base;
  let index = 2;
  while (taken.has(slug)) {
    slug = `${base}-${index}`;
    index += 1;
  }
  return slug;
};

const buildBlankRivetProject = (slug: string, title = titleFromSlug(slug)) =>
  `${JSON.stringify(
    {
      version: 4,
      data: {
        graphs: {
          main: {
            metadata: {
              id: "main",
              name: "Main",
              description: "",
            },
            nodes: {},
          },
        },
        metadata: {
          id: `wright-${slug}`,
          title,
          description: "",
          mainGraphId: "main",
        },
        plugins: [],
      },
    },
    null,
    2,
  )}\n`;

const getApiBase = () => {
  if (typeof window === "undefined") {
    return "http://127.0.0.1:8000";
  }
  const host = window.location.hostname;
  const port = window.location.port;
  if (port === "5173" || port === "5174") {
    return "";
  }
  return `${window.location.protocol}//${host}${port ? `:${port}` : ""}`;
};
export const API_BASE = getApiBase();

export class WorkspaceService {
  async openBrepPanel(sessionId: string): Promise<BrepPanelSession> {
    const response = await hostAdapter.fetch(
      `${API_BASE}/api/workspace/brep/panel`,
      {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ session_id: sessionId }),
      },
    );
    if (!response.ok) {
      let message = "BREP is unavailable";
      try {
        const body = (await response.json()) as { detail?: unknown };
        if (typeof body.detail === "string" && body.detail.trim()) {
          message = body.detail;
        }
      } catch {
        // Preserve the stable fallback when an intermediary returned no JSON.
      }
      throw new Error(message);
    }
    return response.json();
  }

  async getRivetEditorSurface(sessionId: string): Promise<RivetEditorSurface> {
    const response = await hostAdapter.fetch(
      `${API_BASE}/api/workspace/workflows/editor/surface`,
      {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ session_id: sessionId }),
      },
    );
    if (!response.ok) throw new Error("Rivet editor is unavailable");
    return response.json();
  }
  async listRivetWorkflowOperations(
    sessionId: string,
  ): Promise<RivetWorkflowOperation[]> {
    const response = await hostAdapter.fetch(
      `${API_BASE}/api/workspace/workflows?session_id=${encodeURIComponent(sessionId)}`,
    );
    if (!response.ok) throw new Error("Rivet workflows are unavailable");
    return (await response.json()).workflows || [];
  }

  async listRivetWorkflowTemplates(): Promise<RivetWorkflowTemplate[]> {
    const response = await hostAdapter.fetch(
      `${API_BASE}/api/workspace/workflow-templates`,
    );
    if (!response.ok) throw new Error("Rivet templates are unavailable");
    return (await response.json()).templates || [];
  }

  async ensureDefaultRivetWorkflow(
    sessionId: string,
  ): Promise<RivetWorkflowOperation> {
    const existing = await this.listRivetWorkflowOperations(sessionId);
    const first = existing[0];
    if (first) return first;
    return this.createBlankRivetWorkflow(sessionId, "rivet");
  }

  async createBlankRivetWorkflow(
    sessionId: string,
    preferredName = "untitled-workflow",
  ): Promise<RivetWorkflowOperation> {
    const existing = await this.listRivetWorkflowOperations(sessionId);
    const slug = nextWorkflowSlug(existing, preferredName);
    const response = await hostAdapter.fetch(
      `${API_BASE}/api/workspace/workflows`,
      {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          session_id: sessionId,
          slug,
          project: buildBlankRivetProject(slug),
          datasets: {},
        }),
      },
    );
    if (!response.ok) throw new Error("Unable to create a Rivet workflow");
    const created: RivetWorkflowOperation = await response.json();
    return {
      ...created,
      review_state: null,
      reviewer: null,
      reviewed_at: null,
    };
  }

  async createRivetWorkflowFromTemplate(
    sessionId: string,
    template: RivetWorkflowTemplate,
  ): Promise<RivetWorkflowOperation> {
    const existing = await this.listRivetWorkflowOperations(sessionId);
    const slug = nextWorkflowSlug(existing, template.title);
    const response = await hostAdapter.fetch(
      `${API_BASE}/api/workspace/workflow-templates/${encodeURIComponent(template.template_id)}/instantiate`,
      {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ session_id: sessionId, slug }),
      },
    );
    if (!response.ok) {
      let message = "Unable to create a workflow from this template";
      try {
        const body = (await response.json()) as { detail?: unknown };
        if (typeof body.detail === "string" && body.detail.trim()) {
          message = body.detail;
        }
      } catch {
        // Preserve the stable fallback when an intermediary returned no JSON.
      }
      throw new Error(message);
    }
    const created: RivetWorkflowOperation = await response.json();
    return {
      ...created,
      review_state: null,
      reviewer: null,
      reviewed_at: null,
    };
  }

  async readRivetWorkflow(
    sessionId: string,
    slug: string,
  ): Promise<RivetWorkflowDocument> {
    const response = await hostAdapter.fetch(
      `${API_BASE}/api/workspace/workflows/${encodeURIComponent(slug)}?session_id=${encodeURIComponent(sessionId)}`,
    );
    if (!response.ok) throw new Error("Unable to open Rivet workflow");
    const document = await response.json();
    return {
      ...document,
      review_state: null,
      reviewer: null,
      reviewed_at: null,
    };
  }

  async saveRivetWorkflow(
    sessionId: string,
    slug: string,
    expectedRevision: number,
    project: string,
    datasets: Record<string, string> = {},
  ): Promise<RivetWorkflowOperation> {
    const response = await hostAdapter.fetch(
      `${API_BASE}/api/workspace/workflows/${encodeURIComponent(slug)}`,
      {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          session_id: sessionId,
          expected_revision: expectedRevision,
          project,
          datasets,
        }),
      },
    );
    if (!response.ok) throw new Error("Unable to save Rivet workflow");
    const saved: RivetWorkflowOperation = await response.json();
    return { ...saved, review_state: null, reviewer: null, reviewed_at: null };
  }

  async lintRivetWorkflowGraph(
    sessionId: string,
    slug: string,
  ): Promise<RivetWorkflowGraphResponse> {
    const response = await hostAdapter.fetch(
      `${API_BASE}/api/workspace/workflows/${encodeURIComponent(slug)}/graph/lint?session_id=${encodeURIComponent(sessionId)}`,
    );
    if (!response.ok) throw new Error("Unable to lint Rivet workflow");
    return response.json();
  }

  async reviewRivetWorkflow(
    sessionId: string,
    slug: string,
    state: "approved" | "rejected",
    reviewer: string,
    exact?: {
      expectedDigest: string;
      graph?: string;
      bindingSetDigest: string;
    },
  ): Promise<RivetWorkflowOperation> {
    const response = await hostAdapter.fetch(
      `${API_BASE}/api/workspace/workflows/${encodeURIComponent(slug)}/review`,
      {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          session_id: sessionId,
          state,
          reviewer,
          expected_digest: exact?.expectedDigest || null,
          graph: exact?.graph || null,
          binding_set_digest: exact?.bindingSetDigest || null,
        }),
      },
    );
    if (!response.ok) throw new Error("Unable to record workflow review");
    return response.json();
  }

  async getRivetMcpCapabilities(
    sessionId: string,
    slug: string,
    graph?: string,
  ): Promise<RivetMcpCapabilities> {
    const query = new URLSearchParams({ session_id: sessionId, limit: "200" });
    if (graph) query.set("graph", graph);
    const response = await hostAdapter.fetch(
      `${API_BASE}/api/workspace/workflows/${encodeURIComponent(slug)}/mcp-capabilities?${query.toString()}`,
    );
    if (!response.ok)
      throw new Error("Workspace MCP capabilities are unavailable");
    return response.json();
  }

  async previewRivetMcpBindings(
    sessionId: string,
    slug: string,
    expectedRevision: number,
    expectedDigest: string,
    selections: RivetMcpBindingSelection[],
    graph?: string,
  ): Promise<RivetMcpBindingPreview> {
    const response = await hostAdapter.fetch(
      `${API_BASE}/api/workspace/workflows/${encodeURIComponent(slug)}/mcp-bindings/preview`,
      {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          session_id: sessionId,
          expected_revision: expectedRevision,
          expected_digest: expectedDigest,
          graph: graph || null,
          selections,
        }),
      },
    );
    if (!response.ok) {
      let message = "Unable to preview exact MCP bindings";
      try {
        const failure = await response.json();
        message = failure?.detail?.message || message;
      } catch {
        // Retain the safe fallback.
      }
      throw new Error(String(message));
    }
    return response.json();
  }

  async runRivetWorkflow(
    sessionId: string,
    slug: string,
    options: RivetWorkflowRunOptions,
  ): Promise<RivetWorkflowRun> {
    const response = await hostAdapter.fetch(
      `${API_BASE}/api/workspace/workflows/${encodeURIComponent(slug)}/runs`,
      {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          session_id: sessionId,
          expected_revision: options.expectedRevision,
          expected_digest: options.expectedDigest,
          expected_review_digest: options.expectedReviewDigest || null,
          binding_set_digest: options.bindingSetDigest || null,
          graph: options.graph || null,
          inputs: options.inputs || {},
          context: options.context || {},
          timeout_seconds: options.timeoutSeconds || null,
        }),
      },
    );
    if (!response.ok) {
      let message =
        "Workflow could not start; approve its current revision and enable the runner.";
      try {
        const failure = await response.json();
        message = failure?.detail?.message || failure?.detail || message;
      } catch {
        // Keep the stable fallback when the host returns no JSON body.
      }
      throw new Error(String(message));
    }
    return response.json();
  }

  async getRivetWorkflowRun(
    sessionId: string,
    runId: string,
  ): Promise<RivetWorkflowRun> {
    const response = await hostAdapter.fetch(
      `${API_BASE}/api/workspace/workflows/runs/${encodeURIComponent(runId)}?session_id=${encodeURIComponent(sessionId)}`,
    );
    if (!response.ok) throw new Error("Workflow run status is unavailable");
    return response.json();
  }

  async getRivetWorkflowHistory(
    sessionId: string,
    runId: string,
  ): Promise<
    Array<{
      sequence: number;
      kind: string;
      payload: Record<string, unknown>;
    }>
  > {
    const response = await hostAdapter.fetch(
      `${API_BASE}/api/workspace/workflows/runs/${encodeURIComponent(runId)}/history?session_id=${encodeURIComponent(sessionId)}`,
    );
    if (!response.ok) throw new Error("Workflow history is unavailable");
    return (await response.json()).events || [];
  }

  async getRivetRunEvidence(
    sessionId: string,
    runId: string,
  ): Promise<RivetRunEvidence> {
    const response = await hostAdapter.fetch(
      `${API_BASE}/api/workspace/workflows/runs/${encodeURIComponent(runId)}/evidence?session_id=${encodeURIComponent(sessionId)}`,
    );
    if (!response.ok) throw new Error("Run evidence is unavailable");
    return response.json();
  }

  async exportRivetRunEvidence(
    sessionId: string,
    runId: string,
  ): Promise<void> {
    const response = await hostAdapter.fetch(
      `${API_BASE}/api/workspace/workflows/runs/${encodeURIComponent(runId)}/evidence/export?session_id=${encodeURIComponent(sessionId)}`,
    );
    if (!response.ok) throw new Error("Run evidence export is unavailable");
    const blob = await response.blob();
    const url = URL.createObjectURL(blob);
    try {
      const anchor = document.createElement("a");
      anchor.href = url;
      anchor.download = `wright-rivet-run-${runId}-evidence.json`;
      anchor.click();
    } finally {
      URL.revokeObjectURL(url);
    }
  }

  async getRivetCallApprovals(
    sessionId: string,
    runId: string,
  ): Promise<RivetCallApproval[]> {
    const response = await hostAdapter.fetch(
      `${API_BASE}/api/workspace/workflows/runs/${encodeURIComponent(runId)}/approvals?session_id=${encodeURIComponent(sessionId)}`,
    );
    if (!response.ok) throw new Error("Call approvals are unavailable");
    return (await response.json()).approvals || [];
  }

  async decideRivetCallApproval(
    sessionId: string,
    runId: string,
    approval: RivetCallApproval,
    decision: "approved" | "denied",
    reason?: string,
  ): Promise<RivetCallApproval> {
    const response = await hostAdapter.fetch(
      `${API_BASE}/api/workspace/workflows/runs/${encodeURIComponent(runId)}/approvals/${encodeURIComponent(approval.approval_id)}`,
      {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          session_id: sessionId,
          expected_digest: approval.approval_digest,
          decision,
          actor: "local-user",
          reason: reason || null,
        }),
      },
    );
    if (!response.ok)
      throw new Error("This exact call changed or is no longer pending");
    return response.json();
  }

  async cancelRivetWorkflow(
    sessionId: string,
    run: RivetWorkflowRun,
  ): Promise<RivetWorkflowRun> {
    const response = await hostAdapter.fetch(
      `${API_BASE}/api/workspace/workflows/runs/${encodeURIComponent(run.run_id)}/cancel`,
      {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          session_id: sessionId,
          generation: run.generation,
        }),
      },
    );
    if (!response.ok) throw new Error("Workflow cancellation failed");
    return response.json();
  }

  async listEngineeringScenarios(): Promise<EngineeringScenarioEntry[]> {
    const response = await hostAdapter.fetch(
      `${API_BASE}/api/workspace/engineering-scenarios`,
    );
    if (!response.ok) throw new Error("Engineering scenarios are unavailable");
    return (await response.json()).scenarios || [];
  }

  async getEngineeringScenarioDetail(
    scenarioId: string,
  ): Promise<EngineeringScenarioDetail> {
    const response = await hostAdapter.fetch(
      `${API_BASE}/api/workspace/engineering-scenarios/${encodeURIComponent(scenarioId)}`,
    );
    if (!response.ok) throw new Error("Engineering scenario is unavailable");
    return response.json();
  }

  async preflightEngineeringScenario(
    sessionId: string,
    scenarioId: string,
  ): Promise<EngineeringScenarioPreflight> {
    const response = await hostAdapter.fetch(
      `${API_BASE}/api/workspace/engineering-scenarios/${encodeURIComponent(scenarioId)}/preflight`,
      {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ session_id: sessionId }),
      },
    );
    if (!response.ok) {
      let message = "Scenario preflight failed";
      try {
        const failure = await response.json();
        message = failure?.detail?.message || message;
      } catch {
        // Keep the safe fallback.
      }
      throw new Error(String(message));
    }
    return response.json();
  }

  async startEngineeringScenario(
    sessionId: string,
    preflight: EngineeringScenarioPreflight,
    workflow: RivetWorkflowOperation,
  ): Promise<{
    scenario_run_id: string;
    workflow_run: RivetWorkflowRun;
    state: "running";
  }> {
    if (
      !preflight.workflow_revision ||
      !preflight.workflow_digest ||
      !workflow.review_digest ||
      !workflow.binding_set_digest
    ) {
      throw new Error("Review the exact prepared scenario workflow first");
    }
    const response = await hostAdapter.fetch(
      `${API_BASE}/api/workspace/engineering-scenarios/${encodeURIComponent(preflight.scenario_id)}/runs`,
      {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          session_id: sessionId,
          manifest_digest: preflight.manifest_digest,
          workflow_revision: preflight.workflow_revision,
          workflow_digest: preflight.workflow_digest,
          review_digest: workflow.review_digest,
          binding_set_digest: workflow.binding_set_digest,
          seed: 0,
        }),
      },
    );
    if (!response.ok) {
      let message = "Engineering scenario could not start";
      try {
        const failure = await response.json();
        message = failure?.detail?.message || message;
      } catch {
        // Keep the safe fallback.
      }
      throw new Error(String(message));
    }
    return response.json();
  }

  async getEngineeringScenarioReport(
    sessionId: string,
    scenarioRunId: string,
  ): Promise<EngineeringScenarioReport> {
    const response = await hostAdapter.fetch(
      `${API_BASE}/api/workspace/engineering-scenarios/runs/${encodeURIComponent(scenarioRunId)}?session_id=${encodeURIComponent(sessionId)}`,
    );
    if (!response.ok) throw new Error("Scenario report is unavailable");
    return response.json();
  }

  async cancelEngineeringScenario(
    sessionId: string,
    scenarioRunId: string,
  ): Promise<RivetWorkflowRun> {
    const response = await hostAdapter.fetch(
      `${API_BASE}/api/workspace/engineering-scenarios/runs/${encodeURIComponent(scenarioRunId)}/cancel`,
      {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ session_id: sessionId }),
      },
    );
    if (!response.ok) throw new Error("Scenario cancellation failed");
    return response.json();
  }

  async compareEngineeringScenarioReports(
    sessionId: string,
    left: string,
    right: string,
  ): Promise<EngineeringScenarioComparison> {
    const response = await hostAdapter.fetch(
      `${API_BASE}/api/workspace/engineering-scenarios/runs/${encodeURIComponent(left)}/compare/${encodeURIComponent(right)}?session_id=${encodeURIComponent(sessionId)}`,
    );
    if (!response.ok) throw new Error("Scenario comparison is unavailable");
    return response.json();
  }

  async exportEngineeringScenarioReport(
    sessionId: string,
    scenarioRunId: string,
  ): Promise<void> {
    const response = await hostAdapter.fetch(
      `${API_BASE}/api/workspace/engineering-scenarios/runs/${encodeURIComponent(scenarioRunId)}/export?session_id=${encodeURIComponent(sessionId)}`,
    );
    if (!response.ok) throw new Error("Scenario report export is unavailable");
    const blob = await response.blob();
    const url = URL.createObjectURL(blob);
    try {
      const anchor = document.createElement("a");
      anchor.href = url;
      anchor.download = `wright-engineering-scenario-${scenarioRunId}.json`;
      anchor.click();
    } finally {
      URL.revokeObjectURL(url);
    }
  }

  async getWorkspaceFiles(sessionId: string): Promise<WorkspaceNode> {
    workspaceLogger.info("Fetching workspace files", { sessionId });

    if (hostAdapter.mode === "desktop") {
      try {
        const config = await window.wrightDesktop?.getConfig();
        const rootPath = config?.workspacePath;
        if (rootPath) {
          return await this.buildWorkspaceTree(rootPath);
        }
      } catch (e: any) {
        workspaceLogger.error(
          "Failed to build workspace tree via IPC, falling back to HTTP",
          { error: e?.message || String(e) },
        );
      }
    }

    const response = await hostAdapter.fetch(
      `${API_BASE}/api/workspace/files?session_id=${sessionId}`,
    );
    if (!response.ok) {
      workspaceLogger.error("Failed to fetch workspace files", {
        status: response.status,
      });
      throw new Error(
        `Failed to fetch workspace files: ${response.statusText}`,
      );
    }
    const data = await response.json();
    return data.workspace;
  }

  private async buildWorkspaceTree(dirPath: string): Promise<WorkspaceNode> {
    const name = dirPath.split(/[/\\]/).pop() || dirPath;
    const entries = await hostAdapter.listDirectory(dirPath);
    const children: WorkspaceNode[] = [];

    for (const entry of entries) {
      if (entry.name === ".git" || entry.name === "node_modules") continue;

      if (entry.isDirectory) {
        const childNode = await this.buildWorkspaceTree(entry.path);
        children.push(childNode);
      } else {
        children.push({
          name: entry.name,
          path: entry.path,
          type: "file",
          size: entry.size || 0,
          last_modified: Date.now(),
          git_status: "Clean",
          children: null,
        });
      }
    }

    children.sort((a, b) => {
      if (a.type !== b.type) {
        return a.type === "directory" ? -1 : 1;
      }
      return a.name.localeCompare(b.name);
    });

    return {
      name,
      path: dirPath,
      type: "directory",
      size: null,
      last_modified: Date.now(),
      git_status: "Clean",
      children,
    };
  }

  async getFileContentArrayBuffer(
    sessionId: string,
    filePath: string,
    backupId?: string,
  ): Promise<ArrayBuffer> {
    workspaceLogger.info("Fetching file content as ArrayBuffer", {
      sessionId,
      filePath,
      backupId,
    });
    if (hostAdapter.mode === "desktop" && !backupId) {
      const text = await hostAdapter.readFile(filePath);
      return new TextEncoder().encode(text).buffer;
    }
    const encodedPath = encodeURIComponent(filePath);
    let url = `${API_BASE}/api/workspace/files/content?session_id=${sessionId}&path=${encodedPath}`;
    if (backupId) {
      url += `&backup_id=${encodeURIComponent(backupId)}`;
    }
    const response = await hostAdapter.fetch(url);
    if (!response.ok) {
      workspaceLogger.error("Failed to fetch file content", {
        status: response.status,
      });
      throw new Error(`Failed to fetch file content: ${response.statusText}`);
    }
    return response.arrayBuffer();
  }

  async getFileContentText(
    sessionId: string,
    filePath: string,
    backupId?: string,
  ): Promise<string> {
    workspaceLogger.info("Fetching file content as text", {
      sessionId,
      filePath,
      backupId,
    });
    if (hostAdapter.mode === "desktop" && !backupId) {
      return hostAdapter.readFile(filePath);
    }
    const encodedPath = encodeURIComponent(filePath);
    let url = `${API_BASE}/api/workspace/files/content?session_id=${sessionId}&path=${encodedPath}`;
    if (backupId) {
      url += `&backup_id=${encodeURIComponent(backupId)}`;
    }
    const response = await hostAdapter.fetch(url);
    if (!response.ok) {
      workspaceLogger.error("Failed to fetch file content", {
        status: response.status,
      });
      throw new Error(`Failed to fetch file content: ${response.statusText}`);
    }
    const contentType = response.headers?.get?.("content-type");
    if (contentType && contentType.includes("application/json")) {
      const data = await response.json();
      return data.content;
    }
    return response.text();
  }

  async createFileNode(
    sessionId: string,
    filePath: string,
    nodeType: "file" | "directory",
  ): Promise<WorkspaceNode> {
    workspaceLogger.info("Creating workspace file node", {
      sessionId,
      filePath,
      nodeType,
    });
    const response = await hostAdapter.fetch(
      `${API_BASE}/api/workspace/files`,
      {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          session_id: sessionId,
          path: filePath,
          type: nodeType,
        }),
      },
    );
    if (!response.ok) {
      workspaceLogger.error("Failed to create workspace file node", {
        status: response.status,
      });
      throw new Error(`Failed to create file/folder: ${response.statusText}`);
    }
    return response.json();
  }

  async deleteFileNode(sessionId: string, filePath: string): Promise<void> {
    workspaceLogger.info("Deleting workspace file node", {
      sessionId,
      filePath,
    });
    const encodedPath = encodeURIComponent(filePath);
    const response = await hostAdapter.fetch(
      `${API_BASE}/api/workspace/files?session_id=${sessionId}&path=${encodedPath}`,
      {
        method: "DELETE",
      },
    );
    if (!response.ok) {
      workspaceLogger.error("Failed to delete workspace file node", {
        status: response.status,
      });
      throw new Error(`Failed to delete file/folder: ${response.statusText}`);
    }
  }

  async moveFileNode(
    sessionId: string,
    sourcePath: string,
    destinationPath: string,
  ): Promise<boolean> {
    workspaceLogger.info("Moving workspace file node", {
      sessionId,
      sourcePath,
      destinationPath,
    });
    const response = await hostAdapter.fetch(
      `${API_BASE}/api/workspace/files/move`,
      {
        method: "PUT",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          session_id: sessionId,
          source_path: sourcePath,
          destination_path: destinationPath,
        }),
      },
    );
    if (!response.ok) {
      workspaceLogger.error("Failed to move workspace file node", {
        status: response.status,
      });
      throw new Error(`Failed to move file/folder: ${response.statusText}`);
    }
    const data = await response.json();
    return data.success;
  }

  async getGitStatus(sessionId: string): Promise<{
    branch_name: string;
    is_clean: boolean;
    changes: {
      path: string;
      git_status: string;
      staged: boolean;
      file_size?: number;
    }[];
  }> {
    workspaceLogger.info("Fetching git status", { sessionId });
    const response = await hostAdapter.fetch(
      `${API_BASE}/api/workspace/git/status?session_id=${sessionId}`,
    );
    if (!response.ok) {
      workspaceLogger.error("Failed to fetch git status", {
        status: response.status,
      });
      throw new Error(`Failed to fetch git status: ${response.statusText}`);
    }
    return response.json();
  }

  async getGitDiff(sessionId: string, filePath: string): Promise<string> {
    workspaceLogger.info("Fetching git diff", { sessionId, filePath });
    const encodedPath = encodeURIComponent(filePath);
    const response = await hostAdapter.fetch(
      `${API_BASE}/api/workspace/git/diff?session_id=${sessionId}&path=${encodedPath}`,
    );
    if (!response.ok) {
      workspaceLogger.error("Failed to fetch git diff", {
        status: response.status,
      });
      throw new Error(`Failed to fetch git diff: ${response.statusText}`);
    }
    const data = await response.json();
    return data.diff;
  }

  async revertFile(sessionId: string, filePath: string): Promise<void> {
    workspaceLogger.info("Reverting file changes", { sessionId, filePath });
    const response = await hostAdapter.fetch(
      `${API_BASE}/api/workspace/git/revert`,
      {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          session_id: sessionId,
          path: filePath,
        }),
      },
    );
    if (!response.ok) {
      workspaceLogger.error("Failed to revert file changes", {
        status: response.status,
      });
      throw new Error(`Failed to revert file changes: ${response.statusText}`);
    }
  }

  async commitChanges(
    sessionId: string,
    message: string,
  ): Promise<{
    success: boolean;
    commit_hash: string;
    message: string;
    timestamp: number;
  }> {
    workspaceLogger.info("Committing changes", { sessionId, message });
    const response = await hostAdapter.fetch(
      `${API_BASE}/api/workspace/git/commit`,
      {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          session_id: sessionId,
          message,
        }),
      },
    );
    if (!response.ok) {
      workspaceLogger.error("Failed to commit changes", {
        status: response.status,
      });
      throw new Error(`Failed to commit changes: ${response.statusText}`);
    }
    return response.json();
  }

  async getGitHistory(
    sessionId: string,
    limit = 50,
  ): Promise<{
    commits: {
      commit_hash: string;
      message: string;
      author: string;
      timestamp: number;
    }[];
  }> {
    workspaceLogger.info("Fetching git history", { sessionId, limit });
    const response = await hostAdapter.fetch(
      `${API_BASE}/api/workspace/git/history?session_id=${sessionId}&limit=${limit}`,
    );
    if (!response.ok) {
      workspaceLogger.error("Failed to fetch git history", {
        status: response.status,
      });
      throw new Error(`Failed to fetch git history: ${response.statusText}`);
    }
    return response.json();
  }

  async getWorkspaceConfig(sessionId: string): Promise<{
    workspace_id: string;
    git_remote_url: string | null;
    git_username: string | null;
    has_token: boolean;
    workspace_path?: string;
    workspace_prompt?: string | null;
    git_large_file_threshold?: number | null;
  }> {
    workspaceLogger.info("Fetching workspace config", { sessionId });
    const response = await hostAdapter.fetch(
      `${API_BASE}/api/workspace/config?session_id=${sessionId}`,
    );
    if (!response.ok) {
      workspaceLogger.error("Failed to fetch workspace config", {
        status: response.status,
      });
      throw new Error(
        `Failed to fetch workspace config: ${response.statusText}`,
      );
    }
    return response.json();
  }

  async updateWorkspaceConfig(
    sessionId: string,
    remoteUrl: string | null,
    username: string | null,
    token: string | null,
    workspacePrompt?: string | null,
    gitLargeFileThreshold?: number | null,
  ): Promise<{ success: boolean; workspace_id: string }> {
    workspaceLogger.info("Updating workspace config", {
      sessionId,
      remoteUrl,
      username,
    });
    const response = await hostAdapter.fetch(
      `${API_BASE}/api/workspace/config`,
      {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          session_id: sessionId,
          git_remote_url: remoteUrl,
          git_username: username,
          git_token: token,
          workspace_prompt: workspacePrompt,
          git_large_file_threshold: gitLargeFileThreshold,
        }),
      },
    );
    if (!response.ok) {
      workspaceLogger.error("Failed to update workspace config", {
        status: response.status,
      });
      throw new Error(
        `Failed to update workspace config: ${response.statusText}`,
      );
    }
    return response.json();
  }

  async pushCommits(
    sessionId: string,
  ): Promise<{ success: boolean; message: string }> {
    workspaceLogger.info("Pushing commits to remote", { sessionId });
    const response = await hostAdapter.fetch(
      `${API_BASE}/api/workspace/git/push`,
      {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          session_id: sessionId,
        }),
      },
    );
    if (!response.ok) {
      workspaceLogger.error("Failed to push commits", {
        status: response.status,
      });
      throw new Error(`Failed to push changes: ${response.statusText}`);
    }
    return response.json();
  }

  async pullCommits(
    sessionId: string,
  ): Promise<{ success: boolean; message: string }> {
    workspaceLogger.info("Pulling commits from remote", { sessionId });
    const response = await hostAdapter.fetch(
      `${API_BASE}/api/workspace/git/pull`,
      {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          session_id: sessionId,
        }),
      },
    );
    if (response.status === 409) {
      const data = await response.json();
      throw new MergeConflictError(
        data.message || "Pull resulted in merge conflicts",
        data.conflicted_files || [],
      );
    }
    if (!response.ok) {
      workspaceLogger.error("Failed to pull commits", {
        status: response.status,
      });
      throw new Error(`Failed to pull changes: ${response.statusText}`);
    }
    return response.json();
  }
  async checkoutBranch(
    sessionId: string,
    branchName: string,
    create = false,
  ): Promise<{ success: boolean; message: string }> {
    workspaceLogger.info("Checking out branch", {
      sessionId,
      branchName,
      create,
    });
    const response = await hostAdapter.fetch(
      `${API_BASE}/api/workspace/git/branch`,
      {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          session_id: sessionId,
          branch_name: branchName,
          create,
        }),
      },
    );
    if (!response.ok) {
      const data = await response.json().catch(() => ({}));
      throw new Error(
        data.detail || `Failed to checkout branch: ${response.statusText}`,
      );
    }
    return response.json();
  }

  async mergeBranch(
    sessionId: string,
    branchName: string,
  ): Promise<{ success: boolean; message: string }> {
    workspaceLogger.info("Merging branch", { sessionId, branchName });
    const response = await hostAdapter.fetch(
      `${API_BASE}/api/workspace/git/merge`,
      {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          session_id: sessionId,
          branch_name: branchName,
        }),
      },
    );
    if (!response.ok) {
      const data = await response.json().catch(() => ({}));
      throw new Error(
        data.detail || `Failed to merge branch: ${response.statusText}`,
      );
    }
    return response.json();
  }

  async saveFileContent(
    sessionId: string,
    filePath: string,
    content: string,
  ): Promise<boolean> {
    workspaceLogger.info("Saving file content", { sessionId, filePath });
    if (hostAdapter.mode === "desktop") {
      await hostAdapter.writeFile(filePath, content);
      return true;
    }
    const response = await hostAdapter.fetch(
      `${API_BASE}/api/workspace/files/content`,
      {
        method: "PUT",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          session_id: sessionId,
          path: filePath,
          content,
        }),
      },
    );
    if (!response.ok) {
      workspaceLogger.error("Failed to save file content", {
        status: response.status,
      });
      throw new Error(`Failed to save file: ${response.statusText}`);
    }
    const data = await response.json();
    return data.success;
  }

  async backupFileContent(
    sessionId: string,
    filePath: string,
    content: string,
  ): Promise<string> {
    workspaceLogger.info("Backing up file content", { sessionId, filePath });
    const response = await hostAdapter.fetch(
      `${API_BASE}/api/workspace/files/backup`,
      {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          session_id: sessionId,
          path: filePath,
          content,
        }),
      },
    );
    if (!response.ok) {
      workspaceLogger.error("Failed to backup file content", {
        status: response.status,
      });
      throw new Error(`Failed to backup file: ${response.statusText}`);
    }
    const data = await response.json();
    return data.backup_id;
  }

  async deleteBackup(sessionId: string, backupId: string): Promise<boolean> {
    workspaceLogger.info("Deleting file backup", { sessionId, backupId });
    const response = await hostAdapter.fetch(
      `${API_BASE}/api/workspace/files/backup`,
      {
        method: "DELETE",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          session_id: sessionId,
          backup_id: backupId,
        }),
      },
    );
    if (!response.ok) {
      workspaceLogger.error("Failed to delete backup", {
        status: response.status,
      });
      throw new Error(`Failed to delete backup: ${response.statusText}`);
    }
    const data = await response.json();
    return data.success;
  }

  async getWorkspaceTools(sessionId: string): Promise<string[]> {
    workspaceLogger.info("Fetching workspace tools", { sessionId });
    const response = await hostAdapter.fetch(
      `${API_BASE}/api/workspace/tools?session_id=${sessionId}`,
    );
    if (!response.ok) {
      workspaceLogger.error("Failed to fetch workspace tools", {
        status: response.status,
      });
      throw new Error(
        `Failed to fetch workspace tools: ${response.statusText}`,
      );
    }
    const data = await response.json();
    return data.enabled_tools;
  }

  async getWorkspaceToolsById(workspaceId: string): Promise<string[]> {
    workspaceLogger.info("Fetching workspace tools by workspace ID", {
      workspaceId,
    });
    const response = await hostAdapter.fetch(
      `${API_BASE}/api/workspace/by-id/${encodeURIComponent(workspaceId)}/tools`,
    );
    if (!response.ok) {
      workspaceLogger.error("Failed to fetch workspace tools by workspace ID", {
        status: response.status,
      });
      throw new Error(
        `Failed to fetch workspace tools: ${response.statusText}`,
      );
    }
    const data = await response.json();
    return data.enabled_tools;
  }

  async toggleWorkspaceTool(
    sessionId: string,
    serverId: string,
    isEnabled: boolean,
  ): Promise<boolean> {
    workspaceLogger.info("Toggling workspace tool", {
      sessionId,
      serverId,
      isEnabled,
    });
    const response = await hostAdapter.fetch(
      `${API_BASE}/api/workspace/tools/toggle`,
      {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          session_id: sessionId,
          server_id: serverId,
          is_enabled: isEnabled,
        }),
      },
    );
    if (!response.ok) {
      workspaceLogger.error("Failed to toggle workspace tool", {
        status: response.status,
      });
      throw new Error(`Failed to toggle tool: ${response.statusText}`);
    }
    const data = await response.json();
    return data.success;
  }

  async toggleWorkspaceToolById(
    workspaceId: string,
    serverId: string,
    isEnabled: boolean,
  ): Promise<boolean> {
    workspaceLogger.info("Toggling workspace tool by workspace ID", {
      workspaceId,
      serverId,
      isEnabled,
    });
    const response = await hostAdapter.fetch(
      `${API_BASE}/api/workspace/by-id/${encodeURIComponent(workspaceId)}/tools/toggle`,
      {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          server_id: serverId,
          is_enabled: isEnabled,
        }),
      },
    );
    if (!response.ok) {
      workspaceLogger.error("Failed to toggle workspace tool by workspace ID", {
        status: response.status,
      });
      throw new Error(`Failed to toggle tool: ${response.statusText}`);
    }
    const data = await response.json();
    return data.success;
  }

  async getRecentWorkspaces(): Promise<WorkspaceInfo[]> {
    workspaceLogger.info("Fetching recent workspaces");
    const response = await hostAdapter.fetch(
      `${API_BASE}/api/workspace/recent`,
    );
    if (!response.ok) {
      workspaceLogger.error("Failed to fetch recent workspaces", {
        status: response.status,
      });
      throw new Error(
        `Failed to fetch recent workspaces: ${response.statusText}`,
      );
    }
    const data = await response.json();
    return data.workspaces;
  }

  async getAllWorkspaces(): Promise<WorkspaceInfo[]> {
    workspaceLogger.info("Fetching all workspaces");
    const response = await hostAdapter.fetch(`${API_BASE}/api/workspace/list`);
    if (!response.ok) {
      workspaceLogger.error("Failed to fetch all workspaces", {
        status: response.status,
      });
      throw new Error(`Failed to fetch all workspaces: ${response.statusText}`);
    }
    const data = await response.json();
    return data.workspaces;
  }

  async activateWorkspace(sessionId: string): Promise<boolean> {
    workspaceLogger.info("Activating workspace", { sessionId });
    const response = await hostAdapter.fetch(
      `${API_BASE}/api/workspace/activate`,
      {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ session_id: sessionId }),
      },
    );
    if (!response.ok) {
      workspaceLogger.error("Failed to activate workspace", {
        status: response.status,
      });
      throw new Error(`Failed to activate workspace: ${response.statusText}`);
    }
    const data = await response.json();
    return data.success;
  }

  async createWorkspace(
    name: string,
    localPath?: string,
  ): Promise<WorkspaceInfo> {
    workspaceLogger.info("Creating workspace", { name, localPath });
    const payload: { name: string; local_path?: string } = { name };
    if (localPath) {
      payload.local_path = localPath;
    }
    const response = await hostAdapter.fetch(
      `${API_BASE}/api/workspace/create`,
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
      workspaceLogger.error("Failed to create workspace", {
        status: response.status,
      });
      throw new Error(
        errData.detail || `Failed to create workspace: ${response.statusText}`,
      );
    }
    return response.json();
  }

  async getWorkspace(workspaceId: string): Promise<WorkspaceInfo> {
    workspaceLogger.info("Fetching workspace by ID", { workspaceId });
    const response = await hostAdapter.fetch(
      `${API_BASE}/api/workspace/by-id/${encodeURIComponent(workspaceId)}`,
    );
    if (!response.ok) {
      workspaceLogger.error("Failed to fetch workspace", {
        status: response.status,
      });
      throw new Error(`Failed to fetch workspace: ${response.statusText}`);
    }
    return response.json();
  }

  async getWorkspaceSessions(workspaceId: string): Promise<
    {
      sessionId: string;
      title: string;
      createdAt: number;
      updatedAt: number;
      messageCount: number;
    }[]
  > {
    workspaceLogger.info("Fetching workspace sessions", { workspaceId });
    const response = await hostAdapter.fetch(
      `${API_BASE}/api/workspace/by-id/${encodeURIComponent(workspaceId)}/sessions`,
    );
    if (!response.ok) {
      throw new Error(
        `Failed to fetch workspace sessions: ${response.statusText}`,
      );
    }
    const data = await response.json();
    return (data.sessions || []).map((session: any) => ({
      sessionId: session.session_id,
      title: session.title || "Untitled",
      createdAt: session.created_at,
      updatedAt: session.updated_at,
      messageCount: session.message_count || 0,
    }));
  }

  async createWorkspaceSession(workspaceId: string): Promise<{
    sessionId: string;
    title: string;
    createdAt: number;
    updatedAt: number;
    isActive: boolean;
  }> {
    workspaceLogger.info("Creating workspace session", { workspaceId });
    const response = await hostAdapter.fetch(
      `${API_BASE}/api/workspace/by-id/${encodeURIComponent(workspaceId)}/sessions`,
      { method: "POST" },
    );
    if (!response.ok) {
      throw new Error(
        `Failed to create workspace session: ${response.statusText}`,
      );
    }
    const data = await response.json();
    return {
      sessionId: data.session_id,
      title: data.title || "Untitled",
      createdAt: data.created_at,
      updatedAt: data.created_at,
      isActive: true,
    };
  }

  async selectWorkspaceSession(
    workspaceId: string,
    sessionId: string,
  ): Promise<string> {
    workspaceLogger.info("Selecting workspace session", {
      workspaceId,
      sessionId,
    });
    const response = await hostAdapter.fetch(
      `${API_BASE}/api/workspace/by-id/${encodeURIComponent(workspaceId)}/session/select`,
      {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ session_id: sessionId }),
      },
    );
    if (!response.ok) {
      throw new Error(
        `Failed to select workspace session: ${response.statusText}`,
      );
    }
    const data = await response.json();
    return data.session_id || sessionId;
  }

  async getDefaultWorkspaceDir(): Promise<string> {
    workspaceLogger.info("Fetching default workspace dir");
    const response = await hostAdapter.fetch(
      `${API_BASE}/api/workspace/default-dir`,
    );
    if (!response.ok) {
      workspaceLogger.error("Failed to fetch default workspace dir", {
        status: response.status,
      });
      throw new Error(
        `Failed to fetch default workspace dir: ${response.statusText}`,
      );
    }
    const data = await response.json();
    return data.default_dir;
  }

  async updateWorkspaceSession(
    workspaceId: string,
    sessionId: string,
  ): Promise<string> {
    workspaceLogger.info("Updating workspace session ID", {
      workspaceId,
      sessionId,
    });
    const response = await hostAdapter.fetch(
      `${API_BASE}/api/workspace/by-id/${encodeURIComponent(workspaceId)}/session/select`,
      {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ session_id: sessionId }),
      },
    );
    if (!response.ok) {
      workspaceLogger.error("Failed to update workspace session", {
        status: response.status,
      });
      throw new Error(
        `Failed to update workspace session: ${response.statusText}`,
      );
    }
    const data = await response.json();
    return data.session_id || sessionId;
  }

  async getMcpStatus(sessionId: string): Promise<{
    status: string;
    message: string;
    running_mcps?: {
      name: string;
      status: string;
      error_message?: string | null;
    }[];
  }> {
    const response = await hostAdapter.fetch(
      `${API_BASE}/api/workspace/mcp-status?session_id=${sessionId}`,
    );
    if (!response.ok) {
      throw new Error(`Failed to get MCP status: ${response.statusText}`);
    }
    return response.json();
  }

  async getWorkspaceMcpStatus(workspaceId: string): Promise<{
    status: string;
    message: string;
    running_mcps?: {
      name: string;
      status: string;
      error_message?: string | null;
    }[];
  }> {
    const response = await hostAdapter.fetch(
      `${API_BASE}/api/workspace/by-id/${encodeURIComponent(workspaceId)}/mcp-status`,
    );
    if (!response.ok) {
      throw new Error(
        `Failed to get workspace MCP status: ${response.statusText}`,
      );
    }
    return response.json();
  }

  async runFile(
    sessionId: string,
    filePath: string,
  ): Promise<{
    success: boolean;
    stdout: string;
    stderr: string;
    exit_code: number;
  }> {
    workspaceLogger.info("Running file in workspace", { sessionId, filePath });
    const response = await hostAdapter.fetch(
      `${API_BASE}/api/workspace/files/run`,
      {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          session_id: sessionId,
          path: filePath,
        }),
      },
    );
    if (!response.ok) {
      const data = await response.json().catch(() => ({}));
      workspaceLogger.error("Failed to run file", {
        status: response.status,
      });
      throw new Error(
        data.detail || `Failed to run file: ${response.statusText}`,
      );
    }
    return response.json();
  }

  async selectFiles(options?: SelectOptions): Promise<string[]> {
    return hostAdapter.selectFiles(options);
  }
}

export interface WorkspaceInfo {
  workspace_id: string;
  session_id: string;
  workspace_name?: string | null;
  local_path: string;
  git_remote_url: string | null;
  git_username: string | null;
  enabled_tools?: string[] | null;
  updated_at: number;
}

export class MergeConflictError extends Error {
  conflictedFiles: string[];
  constructor(message: string, conflictedFiles: string[]) {
    super(message);
    this.name = "MergeConflictError";
    this.conflictedFiles = conflictedFiles;
  }
}

export const workspaceService = new WorkspaceService();
export default workspaceService;
