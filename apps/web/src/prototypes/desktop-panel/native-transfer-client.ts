import type { CallToolResult } from "@modelcontextprotocol/sdk/types.js";
import { createWorkflowBundleClient } from "../../services/workflow-bundles";

export type NativeTransferCall = (
  tool:
    | "wright_workflow_export"
    | "wright_workflow_import_inspect"
    | "wright_workflow_import",
  args: Record<string, unknown>,
) => Promise<CallToolResult>;

const tools = {
  export: "wright_workflow_export",
  inspect: "wright_workflow_import_inspect",
  import: "wright_workflow_import",
} as const;
const record = (value: unknown): value is Record<string, unknown> =>
  !!value && typeof value === "object" && !Array.isArray(value);

/** Three exact UI ports. The shared client still validates portable contracts. */
export function createNativeTransferClient(
  workspaceId: string,
  sessionId: string,
  call: NativeTransferCall,
) {
  let pendingImport = false;
  const client = createWorkflowBundleClient(async (operation, body) => {
    if (body.session_id !== sessionId)
      throw new Error("Workflow transfer belongs to another session.");
    const request = { ...body, workspace_id: workspaceId };
    if (
      new TextEncoder().encode(JSON.stringify(request)).length >
      21 * 1024 * 1024
    )
      throw new Error("The workflow transfer request is too large.");
    if (operation === "import") pendingImport = true;
    const result = await call(tools[operation], { request });
    if (result.isError)
      throw new Error("Wright did not confirm this transfer.");
    const text = result.content.find((item) => item.type === "text");
    const value: unknown =
      result.structuredContent ??
      (text?.type === "text" ? JSON.parse(text.text) : null);
    if (
      !record(value) ||
      new TextEncoder().encode(JSON.stringify(value)).length > 21 * 1024 * 1024
    )
      throw new Error("Wright returned an invalid transfer response.");
    if (value.ok === false) {
      if (
        operation === "import" &&
        record(value.error) &&
        value.error.outcome_known === true
      )
        pendingImport = false;
      throw new Error(
        record(value.error) && typeof value.error.message === "string"
          ? value.error.message
          : "Wright could not confirm this transfer.",
      );
    }
    if (operation === "import") {
      if (!record(value.document))
        throw new Error("Wright returned no import record.");
      return value.document;
    }
    return value;
  });
  return {
    ...client,
    async import(...args: Parameters<typeof client.import>) {
      if (pendingImport)
        throw new Error(
          "Import outcome is unknown. Inspect its destination and manifest; no import was repeated.",
        );
      if (args[0] !== sessionId)
        throw new Error("Workflow transfer belongs to another session.");
      const imported = await client.import(...args);
      if (
        imported.source.workspace_id !== workspaceId ||
        imported.source.path !== args[2] ||
        imported.source.source !== args[1].source ||
        imported.source.storage_digest !== args[1].source_digest ||
        imported.inspection.bundle_digest !== args[3]
      )
        throw new Error(
          "Import outcome is unknown: the returned definition identity differs.",
        );
      pendingImport = false;
      return imported;
    },
  };
}
