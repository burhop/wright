import { hostAdapter } from "./host-adapter";
import type { WorkspaceWorkflowSourceDocument } from "./workspace-service";

/** A new definition file, never a copied run or execution permission. */
export async function copyWorkspaceWorkflowSource(
  sessionId: string,
  sourcePath: string,
  destinationPath: string,
  expectedStorageDigest: string,
): Promise<WorkspaceWorkflowSourceDocument> {
  const response = await hostAdapter.fetch(
    hostAdapter.resolveBackendUrl("/api/workspace/workflow-sources/copy"),
    {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        session_id: sessionId,
        source_path: sourcePath,
        destination_path: destinationPath,
        expected_storage_digest: expectedStorageDigest,
      }),
    },
  );
  const result = await response.json();
  if (!response.ok) {
    const detail = result.details ?? result.detail;
    throw new Error(
      typeof detail?.message === "string"
        ? detail.message
        : "Could not copy the saved workflow. Reload its current revision or choose a new filename.",
    );
  }
  if (
    typeof result.workspace_id !== "string" ||
    result.path !== destinationPath ||
    result.metadata_authority !== "wright_host" ||
    result.storage_digest !== expectedStorageDigest ||
    typeof result.source !== "string" ||
    result.storage_revision !== 1 ||
    result.definition_revision !== 1
  )
    throw new Error(
      "Wright returned an invalid saved workflow copy. Inspect the destination before retrying.",
    );
  return result as WorkspaceWorkflowSourceDocument;
}
