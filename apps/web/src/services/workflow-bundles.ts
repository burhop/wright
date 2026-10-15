import { hostAdapter } from "./host-adapter";
import type { WorkspaceWorkflowSourceDocument } from "./workspace-service";

export interface WorkflowBundleInspection {
  bundle_digest: string;
  can_import: boolean;
  can_run: false;
  diagnostics: Array<{
    code: string;
    severity: "error" | "warning";
    message: string;
    dependency?: string | null;
  }>;
  external_dependencies: Array<Record<string, unknown>>;
  requirements: Array<Record<string, unknown>>;
}
const record = (value: unknown): value is Record<string, unknown> =>
  !!value && typeof value === "object" && !Array.isArray(value);
export function parseWorkflowBundleFile(text: string): Record<string, unknown> {
  if (new TextEncoder().encode(text).length > 20 * 1024 * 1024)
    throw new Error("Keep the workflow transfer file within 20 MiB.");
  const parsed: unknown = JSON.parse(text);
  const bundle =
    record(parsed) && record(parsed.bundle) ? parsed.bundle : parsed;
  if (!record(bundle) || bundle.schema_version !== "wright.workflow-bundle/1")
    throw new Error("Choose an exported Wright workflow transfer file.");
  return structuredClone(bundle);
}
async function request(path: string, body: Record<string, unknown>) {
  const content = JSON.stringify(body);
  if (new TextEncoder().encode(content).length > 21 * 1024 * 1024)
    throw new Error("The workflow transfer request is too large.");
  const response = await hostAdapter.fetch(
    hostAdapter.resolveBackendUrl(`/api/workspace/workflow-bundles/${path}`),
    {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: content,
    },
  );
  const text = await response.text();
  if (new TextEncoder().encode(text).length > 21 * 1024 * 1024)
    throw new Error("The workflow transfer response is too large.");
  const value: unknown = JSON.parse(text);
  if (!response.ok) {
    const detail = record(value) ? (value.details ?? value.detail) : null;
    throw new Error(
      record(detail) && typeof detail.message === "string"
        ? detail.message
        : "Workflow transfer could not be validated. Inspect its source, dependencies and destination.",
    );
  }
  if (!record(value))
    throw new Error("Wright returned an invalid workflow transfer response.");
  return value;
}
function inspection(value: Record<string, unknown>): WorkflowBundleInspection {
  if (
    typeof value.bundle_digest !== "string" ||
    !/^[a-f0-9]{64}$/.test(value.bundle_digest) ||
    typeof value.can_import !== "boolean" ||
    value.can_run !== false ||
    !Array.isArray(value.diagnostics) ||
    !Array.isArray(value.external_dependencies) ||
    !Array.isArray(value.requirements)
  )
    throw new Error("Wright returned an invalid workflow transfer inspection.");
  if (
    value.diagnostics.some(
      (item) =>
        !record(item) ||
        typeof item.code !== "string" ||
        (item.severity !== "error" && item.severity !== "warning") ||
        typeof item.message !== "string" ||
        (item.dependency != null && typeof item.dependency !== "string"),
    )
  )
    throw new Error("Wright returned invalid transfer diagnostics.");
  return value as unknown as WorkflowBundleInspection;
}
export type WorkflowBundleRequest = (
  operation: "export" | "inspect" | "import",
  body: Record<string, unknown>,
) => Promise<Record<string, unknown>>;

export function createWorkflowBundleClient(
  send: WorkflowBundleRequest = request,
) {
  return {
    async export(
      sessionId: string,
      path: string,
      expectedStorageDigest: string,
      mode: "source" | "bundle",
      selectedReferencePaths: string[],
      selectedUiIds: string[],
    ) {
      const value = await send("export", {
        session_id: sessionId,
        path,
        expected_storage_digest: expectedStorageDigest,
        mode,
        selected_reference_paths: selectedReferencePaths,
        selected_ui_ids: selectedUiIds,
      });
      if (
        !record(value.bundle) ||
        value.bundle.schema_version !== "wright.workflow-bundle/1" ||
        typeof value.bundle_digest !== "string" ||
        !/^[a-f0-9]{64}$/.test(value.bundle_digest)
      )
        throw new Error("Wright returned an invalid workflow export.");
      return { bundle: value.bundle, bundle_digest: value.bundle_digest };
    },
    async inspect(
      sessionId: string,
      bundle: Record<string, unknown>,
      destinationPath: string,
    ) {
      return inspection(
        await send("inspect", {
          session_id: sessionId,
          bundle,
          destination_path: destinationPath,
        }),
      );
    },
    async import(
      sessionId: string,
      bundle: Record<string, unknown>,
      destinationPath: string,
      expectedBundleDigest: string,
    ) {
      const value = await send("import", {
        session_id: sessionId,
        bundle,
        destination_path: destinationPath,
        expected_bundle_digest: expectedBundleDigest,
      });
      if (
        !record(value.source) ||
        typeof value.source.path !== "string" ||
        typeof value.source.workspace_id !== "string" ||
        typeof value.source.source !== "string" ||
        typeof value.source.storage_digest !== "string" ||
        !Array.isArray(value.imported_paths) ||
        !record(value.inspection)
      )
        throw new Error("Wright returned an invalid workflow import.");
      return {
        source: value.source as unknown as WorkspaceWorkflowSourceDocument,
        imported_paths: value.imported_paths as string[],
        inspection: inspection(value.inspection),
      };
    },
  };
}

export const workflowBundles = createWorkflowBundleClient();
export type WorkflowBundleClient = ReturnType<
  typeof createWorkflowBundleClient
>;
