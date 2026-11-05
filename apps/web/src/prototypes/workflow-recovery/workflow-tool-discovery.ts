import { createContext, useContext } from "react";
import { listWorkflowMcpTools } from "./mcp-settings";

export type WorkflowOptionKind = "cad" | "application" | "input-files";
export type WorkflowOptionReader = (
  kind: WorkflowOptionKind,
  sessionId: string,
  serverId?: string,
  includeResources?: boolean,
) => Promise<Response>;
const httpOptions: WorkflowOptionReader = (
  kind,
  sessionId,
  serverId,
  includeResources = false,
) => {
  const query = new URLSearchParams({ session_id: sessionId });
  if (serverId) query.set("server_id", serverId);
  if (kind !== "input-files")
    query.set(
      kind === "cad" ? "documents" : "resources",
      String(includeResources),
    );
  return fetch(`/api/workspace/workflow-sources/${kind}?${query}`);
};

// Discovery and bounded authoring reads are host-adapted; mutations retain their owners.
export const WorkflowToolDiscovery = createContext<{
  read: typeof listWorkflowMcpTools;
  readOptions?: WorkflowOptionReader;
  sessionId?: string;
  openConnections?: () => void;
}>({ read: (sessionId) => listWorkflowMcpTools(sessionId) });
export const useWorkflowToolDiscovery = () =>
  useContext(WorkflowToolDiscovery).read;
export const useWorkflowToolSession = (sessionId?: string) =>
  useContext(WorkflowToolDiscovery).sessionId ?? sessionId;

export const useWorkflowToolManagement = () =>
  useContext(WorkflowToolDiscovery).openConnections;
export const useWorkflowOptionReader = () =>
  useContext(WorkflowToolDiscovery).readOptions ?? httpOptions;
