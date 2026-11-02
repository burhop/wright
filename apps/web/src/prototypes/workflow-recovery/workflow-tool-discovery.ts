import { createContext, useContext } from "react";
import { listWorkflowMcpTools } from "./mcp-settings";

// Only discovery is host-adapted. This scope must not enable HTTP-only actions.
export const WorkflowToolDiscovery = createContext<{
  read: typeof listWorkflowMcpTools;
  sessionId?: string;
  openConnections?: () => void;
}>({ read: (sessionId) => listWorkflowMcpTools(sessionId) });
export const useWorkflowToolDiscovery = () =>
  useContext(WorkflowToolDiscovery).read;
export const useWorkflowToolSession = (sessionId?: string) =>
  useContext(WorkflowToolDiscovery).sessionId ?? sessionId;

export const useWorkflowToolManagement = () =>
  useContext(WorkflowToolDiscovery).openConnections;
