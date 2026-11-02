import { hostAdapter } from "./host-adapter";
import type { WorkspaceWorkflowSourceDocument } from "./workspace-service";

export const handleToolRoles = [
  "construction",
  "geometry",
  "slicer",
  "inspection",
] as const;
export const handleProfileRoles = [
  "machine",
  "process_original",
  "process_orca",
  "filament",
] as const;
export type HandleToolRole = (typeof handleToolRoles)[number];
export type HandleProfileRole = (typeof handleProfileRoles)[number];
export interface HandleSetupTool {
  server_id: string;
  name: string;
  tool_name: string;
  schema_digest: string;
  title?: string;
  server_name?: string;
}
interface HandleRecipe {
  id: "printed-handle-orca";
  version: string;
  digest: string;
}
export interface HandleSetupOptions {
  workspace_id: string;
  path: string;
  workflow_id: string;
  recipe: HandleRecipe;
  workspace_mount: string;
  tools: Record<HandleToolRole, HandleSetupTool[]>;
  profiles: { mode: "workspace_files"; roles: HandleProfileRole[] };
  requirements: string[];
}
export interface HandleSetupSelection {
  tools: Record<
    HandleToolRole,
    Pick<HandleSetupTool, "server_id" | "name" | "schema_digest">
  >;
  workspace_mount: string;
  profiles: Record<HandleProfileRole, { path: string }>;
  selected_orientation: "pads_down" | "side";
}
export interface HandleSetupProposal {
  workspace_id: string;
  workflow_id: string;
  path: string;
  expected_storage_revision: number;
  expected_storage_digest: string;
  proposal_id: string;
  proposal_digest: string;
  recipe: HandleRecipe;
  source: string;
  source_digest: string;
  dependencies: Array<{ path: string; sha256: string; size_bytes: number }>;
  summary: Record<string, unknown>;
}

const record = (value: unknown): value is Record<string, unknown> =>
  !!value && typeof value === "object" && !Array.isArray(value);
const hash = (value: unknown) =>
  typeof value === "string" && /^[a-f0-9]{64}$/.test(value);
const strings = (value: unknown): value is string[] =>
  Array.isArray(value) && value.every((item) => typeof item === "string");
const recipe = (value: unknown) =>
  record(value) &&
  value.id === "printed-handle-orca" &&
  value.version === "2" &&
  hash(value.digest);
const requireRecipe = (value: unknown) => {
  if (!recipe(value))
    throw new Error(
      "This setup recipe is unsupported or invalid. This interface requires printed-handle-orca version 2. Check the Wright version and reopen setup before preparing a proposal.",
    );
};
const scope = (
  sessionId: string,
  document: WorkspaceWorkflowSourceDocument,
) => ({
  session_id: sessionId,
  path: document.path,
  expected_storage_revision: document.storage_revision,
  expected_storage_digest: document.storage_digest,
});

async function request(operation: string, body: Record<string, unknown>) {
  const response = await hostAdapter.fetch(
    hostAdapter.resolveBackendUrl(
      `/api/workspace/workflow-source-templates/replacement-drawer-handle/setup/${operation}`,
    ),
    {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    },
  );
  const text = await response.text();
  if (new TextEncoder().encode(text).length > 4 * 1024 * 1024)
    throw new Error(
      "The setup response is too large to inspect. Reopen the saved source before another request.",
    );
  const value: unknown = JSON.parse(text);
  if (!response.ok) {
    const detail = record(value) ? (value.details ?? value.detail) : null;
    // The shared API error envelope keeps its public message at the top level.
    const message =
      record(value) && typeof value.message === "string"
        ? value.message
        : record(detail) && typeof detail.message === "string"
          ? detail.message
          : null;
    throw new Error(
      message
        ? [
            message,
            record(detail) && typeof detail.correction === "string"
              ? detail.correction
              : "",
          ]
            .filter(Boolean)
            .join(" ")
        : "Handle setup could not be completed. Check the current source and selected capabilities before retrying.",
    );
  }
  if (!record(value))
    throw new Error("Wright returned an invalid setup response.");
  return value;
}

/** Setup proposes and accepts source only. It never starts or approves a run. */
export const printedHandleSetup = {
  async options(
    sessionId: string,
    document: WorkspaceWorkflowSourceDocument,
  ): Promise<HandleSetupOptions> {
    const value = await request("options", scope(sessionId, document));
    const tools = value.tools;
    requireRecipe(value.recipe);
    if (
      !record(tools) ||
      handleToolRoles.some((role) => !Array.isArray(tools[role]))
    )
      throw new Error(
        "Setup requirements are missing a required tool role: construction, geometry repair/preview, slicing or inspection. Refresh choices or update Wright before preparing a proposal.",
      );
    if (
      value.workspace_id !== document.workspace_id ||
      value.path !== document.path ||
      typeof value.workflow_id !== "string" ||
      typeof value.workspace_mount !== "string" ||
      !record(value.profiles) ||
      value.profiles.mode !== "workspace_files" ||
      !strings(value.profiles.roles) ||
      handleProfileRoles.some(
        (role) => !(value.profiles as { roles: string[] }).roles.includes(role),
      ) ||
      !strings(value.requirements) ||
      handleToolRoles.some(
        (role) =>
          !Array.isArray(tools[role]) ||
          tools[role].length > 1000 ||
          tools[role].some(
            (tool: unknown) =>
              !record(tool) ||
              typeof tool.server_id !== "string" ||
              typeof tool.name !== "string" ||
              typeof tool.tool_name !== "string" ||
              !hash(tool.schema_digest),
          ),
      )
    )
      throw new Error(
        "Wright returned setup requirements for an invalid or different workspace.",
      );
    return value as unknown as HandleSetupOptions;
  },
  async propose(
    sessionId: string,
    document: WorkspaceWorkflowSourceDocument,
    selection: HandleSetupSelection,
  ): Promise<HandleSetupProposal> {
    const value = await request("proposals", {
      ...scope(sessionId, document),
      ...selection,
    });
    requireRecipe(value.recipe);
    if (
      value.workspace_id !== document.workspace_id ||
      value.path !== document.path ||
      value.expected_storage_revision !== document.storage_revision ||
      value.expected_storage_digest !== document.storage_digest ||
      typeof value.workflow_id !== "string" ||
      typeof value.proposal_id !== "string" ||
      !/^[a-zA-Z0-9_-]{1,128}$/.test(value.proposal_id) ||
      !hash(value.proposal_digest) ||
      !hash(value.source_digest) ||
      typeof value.source !== "string" ||
      !record(value.summary) ||
      !Array.isArray(value.dependencies) ||
      value.dependencies.length > 1000 ||
      value.dependencies.some(
        (item: unknown) =>
          !record(item) ||
          typeof item.path !== "string" ||
          !hash(item.sha256) ||
          !Number.isSafeInteger(item.size_bytes) ||
          (item.size_bytes as number) < 0,
      )
    )
      throw new Error(
        "The setup proposal does not match this saved source. Reopen setup before accepting a revision.",
      );
    return value as unknown as HandleSetupProposal;
  },
  async accept(
    sessionId: string,
    document: WorkspaceWorkflowSourceDocument,
    proposal: HandleSetupProposal,
  ): Promise<WorkspaceWorkflowSourceDocument> {
    const value = await request("accept", {
      ...scope(sessionId, document),
      proposal_id: proposal.proposal_id,
      proposal_digest: proposal.proposal_digest,
    });
    if (
      value.workspace_id !== document.workspace_id ||
      value.path !== document.path ||
      value.metadata_authority !== "wright_host" ||
      value.source !== proposal.source ||
      value.storage_digest !== proposal.source_digest ||
      !Number.isSafeInteger(value.storage_revision) ||
      (value.storage_revision as number) <= document.storage_revision ||
      !Number.isSafeInteger(value.definition_revision) ||
      (value.definition_revision as number) <= document.definition_revision
    )
      throw new Error(
        "The acceptance response could not be matched. Reopen the saved workflow and inspect its revision before another acceptance.",
      );
    return value as unknown as WorkspaceWorkflowSourceDocument;
  },
};
